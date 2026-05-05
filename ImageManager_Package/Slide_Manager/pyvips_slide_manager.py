from .abc_slide_manager import SlideManager
from Utils.set_pyvips import setup_vips
import pyvips
import numpy as np


class VipsSlideManager(SlideManager):
    """
    Manager specializzato per la gestione di Whole Slide Images (WSI) tramite la libreria PyVips.
    """

    def __init__(self, input_path, tile_w, tile_h):
        # Carica solo i metadati e i puntatori del livello di massima risoluzione (Livello 0)
        try:
            # Tenta di caricarla come una WSI medica (con i livelli)
            self.vips_image = pyvips.Image.new_from_file(input_path, level=0)
        except pyvips.error.Error as e:
            # Se la libreria si lamenta del parametro 'level', è un'immagine normale (PNG/JPG)
            if "does not support optional argument level" in str(e):
                self.vips_image = pyvips.Image.new_from_file(input_path)
            else:
                # Se è un altro tipo di errore (es. file corrotto o inesistente), lo rilanciamo
                raise e
        # Crea una 'Region' per il livello 0
        self.region = pyvips.Region.new(self.vips_image)

        # Inizializza la lista che conterrà tutti i livelli piramidali dell'immagine
        self.livelli_piramide = []
        self._inizializza_piramide(input_path)

        super().__init__(input_path, tile_w, tile_h)

    def _inizializza_piramide(self, input_path):
        """
        Esplora iterativamente i metadati del file per mappare tutti i livelli di risoluzione presenti
        """
        level = 0
        while True:
            try:
                # Carica i metadati per il livello corrente
                img_livello = pyvips.Image.new_from_file(input_path, level=level)

                # Calcola il fattore di riduzione rispetto all'originale
                downsample = self.vips_image.width / img_livello.width

                # Salva i riferimenti dell'immagine e crea una Region dedicata per questo specifico livello
                self.livelli_piramide.append({
                    'level': level,
                    'image': img_livello,
                    'region': pyvips.Region.new(img_livello),
                    'downsample': downsample,
                    'width': img_livello.width,
                    'height': img_livello.height
                })

                # Criterio di arresto: Se il livello è così compresso da essere più piccolo di 1000 pixel, abbiamo raggiunto il vertice della piramide
                if img_livello.width < 1000 or img_livello.height < 1000:
                    break
                level += 1
            except pyvips.error.Error:
                # PyVips solleva un'eccezione quando cerchiamo di accedere a un livello non esistente
                break

        # Fallback di sicurezza: Se l'immagine caricata non è una WSI piramidale, simuliamo una piramide con un solo livello.
        if not self.livelli_piramide:
            self.livelli_piramide.append({
                'level': 0, 'image': self.vips_image, 'region': self.region, 'downsample': 1.0,
                'width': self.vips_image.width, 'height': self.vips_image.height
            })

        print(
            f"[VipsSlideManager] Trovati {len(self.livelli_piramide)} livelli piramidali con Region attive in {input_path}")

    @property
    def width(self):
        """Restituisce la larghezza massima dell'immagine (Livello 0)"""
        return self.vips_image.width

    @property
    def height(self):
        """Restituisce l'altezza massima dell'immagine (Livello 0)"""
        return self.vips_image.height

    def extract_patch(self, tile_coords):
        """
        Estrae una singola patch dal livello 0 (massima risoluzione)
        """
        x, y, w, h = tile_coords

        if x + w > self.width:
            x = max(0, self.width - w)

        if y + h > self.height:
            y = max(0, self.height - h)

        # Calcoliamo la porzione massima estraibile senza uscire dai bordi fisici dell'immagine
        w_sicura = min(w, self.width - x)
        h_sicura = min(h, self.height - y)

        if w_sicura <= (w // 2) or h_sicura <= (h // 2):
            return None

        try:
            # Legge l'array di byte direttamente dalla RAM
            raw_bytes = self.region.fetch(x, y, w, h)

            # Re-impacchetta l'array di byte in un oggetto pyvips.Image
            patch = pyvips.Image.new_from_memory(
                raw_bytes, w, h, self.vips_image.bands, self.vips_image.format
            )
        except pyvips.error.Error:
            # Fallback: Se le coordinate sforano i bordi dell'immagine (edge case matematico), ripieghiamo in modo sicuro sul .crop() nativo.
            patch = self.vips_image.crop(x, y, w, h)

        # PADDING
        # Se la porzione che abbiamo ritagliato è più piccola della grandezza target
        if w_sicura < w or h_sicura < h:
            # posiziona la nostra patch alle coordinate (0,0) di un nuovo canvas grande (target_w, target_h)
            patch = patch.embed(
                0, 0, w, h,
                extend='background',
                background=[255, 255, 255]
            )

        return patch



    def get_high_res_crop(self, x_scene, y_scene, w_scene, h_scene, scene_w, scene_h):
        """
        Motore di rendering dinamico: Calcola l'area visualizzata a schermo e decide in autonomia
        quale livello della piramide caricare per mantenere la risoluzione visiva altissima
        senza far crashare la memoria RAM.
        """
        if scene_w <= 0 or scene_h <= 0: return None

        # TRASFORMAZIONE COORDINATE: Mappa le coordinate dello schermo (scene) sulle coordinate reali assolute (Livello 0).
        scala_reale_x = self.width / scene_w
        scala_reale_y = self.height / scene_h

        real_x = int(x_scene * scala_reale_x)
        real_y = int(y_scene * scala_reale_y)
        real_w = int(w_scene * scala_reale_x)
        real_h = int(h_scene * scala_reale_y)

        if real_w <= 0 or real_h <= 0: return None

        # =================================================================
        # SCELTA INTELLIGENTE DEL LIVELLO PIRAMIDALE
        # =================================================================
        # Definiamo due costanti chiave per il bilanciamento Qualità/Performance:
        TARGET_PIXELS = 2500.0  # Risoluzione target per l'occhio umano.
        MAX_PIXELS = 4500.0  # Tetto massimo di sicurezza: oltre questo limite il rischio di OutOfMemoryException (RAM piena) è alto

        # Calcoliamo di quanto dovremmo scalare l'immagine reale per farla rientrare nel nostro TARGET
        target_downsample = real_w / TARGET_PIXELS

        # Selezioniamo come punto di partenza il vertice della piramide
        livello_scelto = self.livelli_piramide[-1]

        # Scendiamo lungo la piramide dal livello più sgranato al più dettagliato (Livello 0)
        for lvl in reversed(self.livelli_piramide):
            # Calcola quanti pixel verrebbero caricati in RAM se usassimo questo livello
            pixel_che_verrebbero_estratti = real_w / lvl['downsample']

            # Se questo livello è troppo pesante, manteniamo il livello precedente
            if pixel_che_verrebbero_estratti > MAX_PIXELS:
                break

            livello_scelto = lvl

            # Se il downsample di questo livello ha raggiunto o superato il TARGET visivo fermiamo il ciclo
            if lvl['downsample'] <= target_downsample:
                break

        # =================================================================
        # ESTRAZIONE E CONVERSIONE
        # =================================================================

        # Adattiamo le coordinate del livello 0 con il livello corrente
        ds_x = self.width / livello_scelto['width']
        ds_y = self.height / livello_scelto['height']
        lvl_x = int(real_x / ds_x)
        lvl_y = int(real_y / ds_y)
        lvl_w = int(real_w / ds_x)
        lvl_h = int(real_h / ds_y)

        # Controllo di sicurezza: Assicuriamoci che il ritaglio non esca dai limiti fisici dell'immagine
        if lvl_x + lvl_w > livello_scelto['width']: lvl_w = livello_scelto['width'] - lvl_x
        if lvl_y + lvl_h > livello_scelto['height']: lvl_h = livello_scelto['height'] - lvl_y

        if lvl_w <= 0 or lvl_h <= 0: return None

        try:
            # Estraiamo i pixel usando la Region associata al livello scelto
            raw_bytes = livello_scelto['region'].fetch(lvl_x, lvl_y, lvl_w, lvl_h)

            return pyvips.Image.new_from_memory(
                raw_bytes,
                lvl_w,
                lvl_h,
                livello_scelto['image'].bands,
                livello_scelto['image'].format
            )

        except Exception as e:
            print(f"[SlideManager] Errore imprevisto fetch pyvips al livello {livello_scelto['level']}: {e}")
            return None

    def load_thumbnail_rgb(self, max_width=1024):
        """
        Carica un'anteprima (thumbnail) dell'intera WSI
        """

        # Sfrutta l'ottimizzazione nativa di pyvips per generare thumbnail
        loaded_thumb = pyvips.Image.thumbnail(self.input_path, max_width)

        # Manteniamo solo il i canali RGB
        if loaded_thumb.bands > 3:
            loaded_thumb = loaded_thumb.extract_band(0, n=3)

        # Convertiamo in sRGB se è in formato diverso
        if loaded_thumb.interpretation != 'srgb':
            loaded_thumb = loaded_thumb.colourspace('srgb')

        # Convertiamo i valori dei pixel a interi da 0 a 255
        return loaded_thumb.cast("uchar")

    def load_thumbnail_numpy(self, vips_thumb):
        """
        Metodo di utilità per convertire un'immagine PyVips in un array NumPy
        """
        # Scrive l'immagine in un buffer di memoria
        mem = vips_thumb.write_to_memory()

        # Costruisce la matrice NumPy leggendo quel buffer, rispettando altezza, larghezza e canali RGB
        img_np = np.ndarray(
            buffer=mem,
            dtype=np.uint8,
            shape=[vips_thumb.height, vips_thumb.width, vips_thumb.bands]
        )
        return img_np