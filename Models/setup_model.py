from ImageManager_Package import get_manager


# ==========================================
# CLASSE DI SETUP BASE
# ==========================================
class BaseSetupModel:
    """
    Classe base: Definisce l'interfaccia che tutti i modelli di setup devono rispettare ed eredita le funzionalità comuni
    """

    def __init__(self):
        self.patch_generate = []

    def imposta_parametri_comuni(self, percentuale, ordine):
        """Salva i parametri di campionamento scelti dall'utente nell'interfaccia"""
        self.percentuale = int(percentuale.replace('%', ''))
        self.ordine = ordine

    def notifica_ui(self, callback_ui, percentuale, messaggio):
        """Metodo centralizzato per inviare il feedback visivo (Progress Bar)"""
        if callback_ui:
            callback_ui(percentuale, messaggio)

    def calcola_step(self, totale_elementi):
        """Centralizza la protezione matematica contro divisioni per zero"""
        return max(1, totale_elementi // 100)

    def prepara_dati(self):
        """Metodo che forza le sottoclassi a implementare la logica"""
        raise NotImplementedError("Devi implementare questo metodo nelle sottoclassi")


# ==========================================
# CLASSE PER WSI (Whole Slide Image)
# ==========================================
class SetupSlideModel(BaseSetupModel):
    """
    Gestisce la logica spaziale e geometrica delle immagini gigapixel
    """

    def __init__(self):
        super().__init__()
        self.percorso_slide = ""
        self.manager = None
        self.roi_list = []
        self.larghezza_originale = 0
        self.altezza_originale = 0
        self.grandezza_patch = 512

    def imposta_slide(self, percorso):
        self.percorso_slide = percorso
        self.manager = get_manager('Slide', percorso, tile_w=0, tile_h=0)
        self.larghezza_originale = self.manager.width
        self.altezza_originale = self.manager.height

    def imposta_grandezza_patch(self, nuova_grandezza):
        self.grandezza_patch = nuova_grandezza

    def calcola_patch_totali(self):
        """Calcola la dimensione della griglia massima teorica (tutto il vetrino)"""
        import math
        if not self.manager or self.grandezza_patch <= 0:
            return 0
        colonne = math.ceil(self.larghezza_originale / self.grandezza_patch)
        righe = math.ceil(self.altezza_originale / self.grandezza_patch)
        return righe * colonne

    def ottieni_thumbnail(self, max_dim=1024):
        if not self.manager:
            return None
        return self.manager.load_thumbnail_rgb(max_dim)

    def estrai_area_alta_risoluzione(self, x, y, w, h, scene_w, scene_h):
        if not self.manager:
            print("[DEBUG - ERROR] Model: Image Manager non inizializzato.")
            return None
        return self.manager.get_high_res_crop(x, y, w, h, scene_w, scene_h)

    def calcola_patch_in_roi(self, rois, scene_w, scene_h, step_x, step_y, offset_x=0.0, offset_y=0.0):
        """
        Calcola in tempo reale quante patch cadono all'interno delle ROI disegnate per fornire un feedback all'utente
        """
        import math
        step_x = float(step_x)
        step_y = float(step_y)
        offset_x = float(offset_x)
        offset_y = float(offset_y)

        if not rois or step_x <= 0 or step_y <= 0 or scene_w <= 0 or scene_h <= 0:
            return []

        patch_valide = {}

        for r_idx, r in enumerate(rois):
            roi_id = f"ROI_{r_idx + 1}"
            rx, ry, rw, rh = r['x'], r['y'], r['w'], r['h']

            # Indici della griglia intersecati dal rettangolo ROI
            i_start = math.floor((rx - offset_x) / step_x)
            i_end = math.ceil((rx + rw - offset_x) / step_x)
            j_start = math.floor((ry - offset_y) / step_y)
            j_end = math.ceil((ry + rh - offset_y) / step_y)

            for j in range(int(j_start), int(j_end) + 1):
                for i in range(int(i_start), int(i_end) + 1):
                    px = offset_x + (i * step_x)
                    py = offset_y + (j * step_y)

                    if px >= scene_w or py >= scene_h or (px + step_x) <= 0 or (py + step_y) <= 0:
                        continue

                    w_reale = min(step_x, scene_w - px)
                    h_reale = min(step_y, scene_h - py)
                    soglia_dinamica = (w_reale * h_reale) * 0.40

                    # Calcolo dell'area di sovrapposizione
                    dx = max(0.0, min(px + step_x, rx + rw) - max(px, rx))
                    dy = max(0.0, min(py + step_y, ry + rh) - max(py, ry))

                    if (dx * dy) >= soglia_dinamica:
                        chiave_univoca = (round(px, 3), round(py, 3))
                        if chiave_univoca not in patch_valide:
                            patch_valide[chiave_univoca] = {
                                'x': round(px, 3), 'y': round(py, 3),
                                'w': round(step_x, 3), 'h': round(step_y, 3),
                                'roi_id': roi_id
                            }
        return list(patch_valide.values())

    def prepara_dati(self, callback_ui=None):
        """Assembla i dati definitivi passando attraverso i filtri"""
        if not self.manager or self.grandezza_patch <= 0:
            return []

        self.notifica_ui(callback_ui, 5, "Inizializzazione motore PyVips...")

        self.manager = get_manager('Slide', self.percorso_slide, tile_w=self.grandezza_patch,
                                   tile_h=self.grandezza_patch)

        # Popolamento griglia teorica
        self.manager.patches_coords = self.manager.get_coords()

        # Filtraggio
        self.notifica_ui(callback_ui, 10, "Analisi del tessuto in corso con PyVips...")
        print("[DEBUG] Calcolo delle zone di tessuto in corso...")
        coordinate_valide = self.manager.get_tissue_coords(tissue_coverage=0.1)

        dati_pronti = []
        for coord in coordinate_valide:
            dati_pronti.append({
                "x": int(coord[0]), "y": int(coord[1]),
                "dimensione": int(coord[2]), "percorso": None
            })

        # Timbratura ROI
        if hasattr(self, 'roi_list') and self.roi_list:
            step = float(self.grandezza_patch)
            totale_patch = len(dati_pronti)
            step_aggiornamento = self.calcola_step(totale_patch)

            for i, patch in enumerate(dati_pronti):
                patch['roi_id'] = None
                px, py = float(patch['x']), float(patch['y'])

                w_reale = min(step, self.larghezza_originale -px)
                h_reale = min(step, self.altezza_originale - py)
                soglia_dinamica = (w_reale * h_reale) * 0.40

                for r_idx, r in enumerate(self.roi_list):
                    rx, ry = float(r['x']), float(r['y'])
                    rw, rh = float(r['width']), float(r['height'])

                    dx = max(0.0, min(px + step, rx + rw) - max(px, rx))
                    dy = max(0.0, min(py + step, ry + rh) - max(py, ry))

                    if (dx * dy) >= soglia_dinamica:
                        patch['roi_id'] = f"ROI_{r_idx + 1}"
                        break

                if i % step_aggiornamento == 0:
                    percentuale = 10 + int((i / totale_patch) * 20)
                    self.notifica_ui(callback_ui, percentuale, f"Incrocio ROI patch {i} di {totale_patch}...")
                    import time
                    time.sleep(0.001)

        print(f"[DEBUG] Trovate {len(dati_pronti)} patch valide con tessuto!")
        return dati_pronti


# ==========================================
# CLASSE PER DATASET FOLDER
# ==========================================
class SetupFolderModel(BaseSetupModel):
    """Gestisce progetti basati su cartelle di immagini pre-processate (PATCH)"""

    def __init__(self):
        super().__init__()
        self.percorso_cartella = ""
        self.manager = None

    def imposta_cartella(self, percorso):
        self.percorso_cartella = percorso
        self.manager = get_manager(method='Folder', input_path=percorso)

    def conta_patch_valide(self):
        if self.manager:
            return len(self.manager.get_items())
        return 0

    def prepara_dati(self, callback_ui=None):
        """Impacchetta le stringhe dei percorsi in dizionari compatibili con il JSON"""
        if not self.manager:
            return []

        self.notifica_ui(callback_ui, 10, "Lettura dei file in corso...")

        lista_file = self.manager.get_items()
        totale_file = len(lista_file)
        step_aggiornamento = self.calcola_step(totale_file)

        dati_pronti = []
        for i, nome_file in enumerate(lista_file):
            dati_pronti.append({
                "percorso": nome_file,
                "x": 0, "y": 0, "dimensione": 0
            })

            if i % step_aggiornamento == 0:
                perc = 10 + int((i / totale_file) * 20)
                self.notifica_ui(callback_ui, perc, f"Scansione file {i} di {totale_file}...")

        return dati_pronti