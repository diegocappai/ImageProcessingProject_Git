from .abc_slide_manager import SlideManager
from Utils.set_pyvips import setup_vips
import pyvips
import numpy as np


class VipsSlideManager(SlideManager):
    def __init__(self, input_path, tile_w, tile_h):
        self.vips_image = pyvips.Image.new_from_file(input_path, access='random')
        super().__init__(input_path, tile_w, tile_h)


    @property
    def width(self): return self.vips_image.width

    @property
    def height(self): return self.vips_image.height

    def extract_patch(self, tile_coords):
        return self.vips_image.crop(tile_coords[0], tile_coords[1], tile_coords[2], tile_coords[3])

    def load_thumbnail_rgb(self, max_width=1024):
        best_level = 0
        loaded_thumb = None

        # --- RILEVAMENTO LIVELLI (Logica Pyramid) ---
        # Controlla se l'immagine è multi-livello (formato Slide)
        if "slide.level-count" in self.vips_image.get_fields():
            level_count = int(self.vips_image.get("slide.level-count"))

            # Cicla tra i livelli disponibili (dal più grande al più piccolo)
            for i in range(level_count):
                w = int(self.vips_image.get(f"slide.level[{i}].width"))

                # Cerca un livello gestibile (< 5000px) ma non troppo piccolo
                if w < 5000:
                    best_level = i
                    # Se il livello è vicino alla grandezza desiderata si ferma (max_width * 2)
                    if w <= max_width * 2:
                        break

            # Carica SOLO il livello specifico
            loaded_thumb = pyvips.Image.new_from_file(self.input_path, level=best_level)
        else:
            # Fallback per immagini normali (JPG/PNG)
            loaded_thumb = self.vips_image

        # --- RIDIMENSIONAMENTO FINALE ---
        # Se l'immagine è ancora più grande del limite richiesto la rimpicciolisce
        if loaded_thumb.width > max_width:
            loaded_thumb = loaded_thumb.thumbnail_image(max_width)

        # --- NORMALIZZAZIONE (sRGB + No Alpha) ---
        # Se l'immagine ha più di 3 canali estrae solo i primi 3 (R, G, B)
        if loaded_thumb.bands > 3:
            loaded_thumb = loaded_thumb.extract_band(0, n=3)

        # Converte lo spazio colore in sRGB se non lo è già
        if loaded_thumb.interpretation != 'srgb':
            loaded_thumb = loaded_thumb.colourspace('srgb')

        # Converte i dati in "unsigned char" (0-255) [formato standard per immagini RGB a 8 bit]
        return loaded_thumb.cast("uchar")

    def load_thumbnail_numpy(self, vips_thumb):
        # Estrazione dati in memoria RAM
        mem = vips_thumb.write_to_memory()

        # Creazione dell'array NumPy
        #
        img_np = np.ndarray(
            buffer=mem, # dati estratti
            dtype=np.uint8, # formato a 8 bit ([0, 255] standard per immagini)
            shape=[vips_thumb.height, vips_thumb.width, 3] # formato array (Altezza, Larghezza, Canali)
        )
        return img_np

