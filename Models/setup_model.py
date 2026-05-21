import math
import random
from ImageManager_Package import get_manager

# ==========================================
# CLASSE DI SETUP BASE
# ==========================================
class BaseSetupModel:
    """
    Classe base: Definisce l'interfaccia che tutti i modelli di setup devono rispettare
    """

    def __init__(self):
        # Inizializzo l'elenco vuoto delle patch che verranno poi generate
        self.patch_generate = []

    def imposta_parametri_comuni(self, percentuale, ordine):
        """Salva i parametri di campionamento scelti dall'utente"""
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
        """Metodo che forza le sottoclassi a implementare la propria logica di preparazione dei dati"""
        raise NotImplementedError("Devi implementare questo metodo nelle sottoclassi")

# ==========================================
# CLASSE PER WSI (Whole Slide Image)
# ==========================================
class SetupSlideModel(BaseSetupModel):
    """
    Modello specifico per i vetrini digitali interi (WSI).
    Si occupa di gestire la logica spaziale, estrarre le coordinate del tessuto
    e calcolare quali patch cadono dentro le ROI
    """

    def __init__(self):
        super().__init__()
        self.percorso_slide = ""
        self.manager = None
        self.roi_list = []
        self.larghezza_originale = 0
        self.altezza_originale = 0
        self.grandezza_patch = 512 # default

    def imposta_slide(self, percorso):
        """Inizializzo il motore PyVips per leggere i metadati della slide senza caricarla in RAM"""
        self.percorso_slide = percorso
        self.manager = get_manager('Slide', percorso, tile_w=0, tile_h=0)
        self.larghezza_originale = self.manager.width
        self.altezza_originale = self.manager.height

    def imposta_grandezza_patch(self, nuova_grandezza):
        """Aggiorno la dimensione della griglia in base alla scelta dell'utente"""
        self.grandezza_patch = nuova_grandezza

    def calcola_patch_totali(self):
        """Calcola numero teorico di patch che entrebbero in tutta la slide (comprese zone senza tessuto)"""
        if not self.manager or self.grandezza_patch <= 0:
            return 0
        colonne = math.ceil(self.larghezza_originale / self.grandezza_patch)
        righe = math.ceil(self.altezza_originale / self.grandezza_patch)
        return righe * colonne

    def ottieni_thumbnail(self, max_dim=1024):
        """Chiedo a PyVips di generare una miniatura leggera"""
        if not self.manager:
            return None
        return self.manager.load_thumbnail_rgb(max_dim)

    def estrai_area_alta_risoluzione(self, x, y, w, h, scene_w, scene_h):
        """Estraggo un crop ad altissima risoluzione"""
        if not self.manager:
            print("[DEBUG - ERROR] Model: Image Manager non inizializzato.")
            return None
        return self.manager.get_high_res_crop(x, y, w, h, scene_w, scene_h)

    def calcola_patch_in_roi(self, rois, scene_w, scene_h, step_x, step_y, offset_x=0.0, offset_y=0.0):
        """
        Calcola in tempo reale quante patch cadono all'interno della ROI
        """
        step_x = float(step_x)
        step_y = float(step_y)
        offset_x = float(offset_x)
        offset_y = float(offset_y)

        if not rois or step_x <= 0 or step_y <= 0 or scene_w <= 0 or scene_h <= 0:
            return []

        patch_valide = {}

        for r_idx, r in enumerate(rois):
            roi_id = f"ROI_{r_idx + 1}"

            # Difesa anti-crash: cerco sia 'width' che 'w' per supportare diversi formati
            rx = float(r.get('x', 0))
            ry = float(r.get('y', 0))
            rw = float(r.get('width', r.get('w', 0)))
            rh = float(r.get('height', r.get('h', 0)))

            # Calcolo indici della griglia intersecati dal rettangolo ROI
            i_start = math.floor((rx - offset_x) / step_x)
            i_end = math.ceil((rx + rw - offset_x) / step_x)
            j_start = math.floor((ry - offset_y) / step_y)
            j_end = math.ceil((ry + rh - offset_y) / step_y)

            for j in range(int(j_start), int(j_end) + 1):
                for i in range(int(i_start), int(i_end) + 1):
                    px = offset_x + (i * step_x)
                    py = offset_y + (j * step_y)

                    # Salto le patch che sbordano fuori dall'immagine reale
                    if px >= scene_w or py >= scene_h or (px + step_x) <= 0 or (py + step_y) <= 0:
                        continue

                    # Calcolo la vera area della patch (in caso sia tagliata sui bordi)
                    w_reale = min(step_x, scene_w - px)
                    h_reale = min(step_y, scene_h - py)
                    soglia_dinamica = (w_reale * h_reale) * 0.40

                    # Calcolo l'intersezione matematica tra patch e ROI
                    dx = max(0.0, min(px + step_x, rx + rw) - max(px, rx))
                    dy = max(0.0, min(py + step_y, ry + rh) - max(py, ry))

                    # Se la sovrapposizione è almeno del 40%, la considero valida
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
        """
        Il vero "cervello" dell'estrazione WSI.
        Analizzo tutto il vetrino con l'algoritmo di Otsu per trovare il tessuto,
        incrocio i dati con le ROI e genero i dizionari pronti per il salvataggio JSON.
        """
        if not self.manager or self.grandezza_patch <= 0:
            return {"rois": [], "patches": []}

        self.notifica_ui(callback_ui, 5, "Inizializzazione motore PyVips...")
        self.manager = get_manager('Slide', self.percorso_slide, tile_w=self.grandezza_patch,
                                   tile_h=self.grandezza_patch)
        self.manager.patches_coords = self.manager.get_coords()

        self.notifica_ui(callback_ui, 10, "Analisi del tessuto su tutto il vetrino in corso...")

        # Estraggo TUTTE le coordinate del vetrino che contengono almeno il 30% di tessuto
        coordinate_valide = self.manager.get_tissue_coords(tissue_coverage=0.3)

        roi_list_json = []
        patches_json = []
        percentuale_base = getattr(self, 'percentuale', 100)
        rois_da_processare = getattr(self, 'roi_list', [])

        for idx, r in enumerate(rois_da_processare):
            if 'id' not in r:
                r['id'] = f"ROI_{idx + 1}"

        step_x = float(self.grandezza_patch)
        step_y = float(self.grandezza_patch)
        totale_patch_analizzate = len(coordinate_valide)
        step_aggiornamento = self.calcola_step(totale_patch_analizzate)

        patch_per_roi = {roi["id"]: [] for roi in rois_da_processare}
        patch_fuori_roi = []

        # Scansiono ogni patch di tessuto per vedere a quale ROI appartiene
        for idx, coord in enumerate(coordinate_valide):
            px, py, pw, ph = float(coord[0]), float(coord[1]), float(coord[2]), float(coord[3])

            assegnata_a_roi = False
            w_reale = min(step_x, self.larghezza_originale - px)
            h_reale = min(step_y, self.altezza_originale - py)
            soglia_dinamica = (w_reale * h_reale) * 0.40

            for roi in rois_da_processare:
                rx, ry = float(roi['x']), float(roi['y'])
                rw, rh = float(roi['width']), float(roi['height'])

                dx = max(0.0, min(px + step_x, rx + rw) - max(px, rx))
                dy = max(0.0, min(py + step_y, ry + rh) - max(py, ry))

                if (dx * dy) >= soglia_dinamica:
                    patch_per_roi[roi["id"]].append((px, py, pw, ph))
                    assegnata_a_roi = True
                    break

            if not assegnata_a_roi:
                patch_fuori_roi.append((px, py, pw, ph))

            # Aggiorno la barra di progresso
            if callback_ui and idx % step_aggiornamento == 0:
                self.notifica_ui(callback_ui, 30 + int((idx / totale_patch_analizzate) * 30),
                                 f"Mappatura patch {idx} di {totale_patch_analizzate}...")

        # Procedo col campionamento matematico per ogni ROI
        for roi in rois_da_processare:
            roi_id = roi["id"]
            patch_in_questa_roi = patch_per_roi[roi_id]

            totale_utili = len(patch_in_questa_roi)
            da_campionare = max(1, int(totale_utili * (percentuale_base / 100.0))) if totale_utili > 0 else 0
            patch_scelte = set(random.sample(patch_in_questa_roi, da_campionare)) if totale_utili > 0 else set()

            for (px, py, pw, ph) in patch_in_questa_roi:
                patches_json.append({
                    "id": f"p_{int(px)}_{int(py)}",
                    "roi_id": roi_id,
                    "x": int(px), "y": int(py), "w": int(pw), "h": int(ph),
                    "is_sampled": (px, py, pw, ph) in patch_scelte,
                    "label": None,
                    "is_review": False
                })

            roi_list_json.append({
                "id": roi_id,
                "x": int(roi['x']), "y": int(roi['y']), "w": int(roi['width']), "h": int(roi['height']),
                "sampling_percentage": percentuale_base,
                "stats": {"total_valid": totale_utili, "sampled": da_campionare, "labeled": 0}
            })

        # Salvo anche le patch di tessuto che l'utente ha escluso, per avere un backup completo
        for (px, py, pw, ph) in patch_fuori_roi:
            patches_json.append({
                "id": f"p_{int(px)}_{int(py)}",
                "roi_id": None,  # Non appartiene a nessuna ROI
                "x": int(px), "y": int(py), "w": int(pw), "h": int(ph),
                "is_sampled": False,
                "label": None,
                "is_review": False
            })

        # Ordino le patch geometricamente da sinistra a destra, dall'alto in basso
        patches_json.sort(key=lambda p: (p['x'], p['y']))

        print(f"[DEBUG] Setup completato: {len(patches_json)} patch valide totali trovate nel vetrino.")

        return {
            "rois": roi_list_json,
            "patches": patches_json
        }

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
        """Inizializzo il manager passando la cartella selezionata dall'utente."""
        self.percorso_cartella = percorso
        self.manager = get_manager(method='Folder', input_path=percorso)

    def conta_patch_valide(self):
        """Restituisco il totale dei file immagine trovati (patch)"""
        if self.manager:
            return len(self.manager.get_items())
        return 0

    def prepara_dati(self, callback_ui=None):
        """
        Trasformo l'elenco dei nomi file in dizionari strutturati,
        pronti per essere incollati dal ProjectManager dentro il file JSON.
        """
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
                "x": 0, "y": 0, "dimensione": 0 # Coordinate non necessarie
            })

            # Aggiorno la progress bar
            if i % step_aggiornamento == 0:
                perc = 10 + int((i / totale_file) * 20)
                self.notifica_ui(callback_ui, perc, f"Scansione file {i} di {totale_file}...")

        return dati_pronti