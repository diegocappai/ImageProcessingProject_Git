import os
import random
import json
from datetime import datetime, timezone


class ProjectManager:
    """
    Core Model dell'applicazione:
    Mantiene in memoria il dizionario JSON completo del progetto e si occupa di sincronizzarlo in modo sicuro sul disco fisso
    """

    def __init__(self):
        self.percorso_cartella_progetto = ""
        self.percorso_file_json = ""
        self.data = {}

    # ==========================================
    # UTILITY INTERNE
    # ==========================================
    def _ora_corrente_iso(self):
        """Restituisce l'ora esatta nel formato standard internazionale"""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _ricalcola_progress(self):
        """
        Motore di Statistica: Scansiona l'intero array delle patch e aggiorna
        il contatore globale del progresso. Fondamentale per i grafici della Dashboard.
        """
        if "patches" not in self.data or "progress" not in self.data:
            return

        totale = len(self.data["patches"])
        etichettate = sum(1 for p in self.data["patches"] if p["status"] == "labeled")
        saltate = sum(1 for p in self.data["patches"] if p["status"] == "skipped")
        mostrate = sum(1 for p in self.data["patches"] if p.get("shown_to_user", False))

        # Aggiornamento dell'albero JSON
        self.data["progress"]["total_patches"] = totale
        self.data["progress"]["labeled_patches"] = etichettate
        self.data["progress"]["skipped_patches"] = saltate
        self.data["progress"]["shown_patches"] = mostrate

        # Calcolo del completamento: se non ci sono più patch 'pending' nel campione, abbiamo finito.
        pendenti = sum(1 for p in self.data["patches"] if p["status"] == "pending" and p.get("is_sampled", False))
        self.data["progress"]["completed"] = (pendenti == 0 and totale > 0)

    @staticmethod
    def genera_indici_campionamento(totale_patch, percentuale, modalita="Random"):
        """
        Genera gli indici delle patch da mostrare
        """
        if totale_patch == 0:
            return []

        if percentuale >= 100:
            indici = list(range(totale_patch))
            if modalita == "Random":
                random.shuffle(indici)
            return indici

        numero_indici = max(1, int(totale_patch * (percentuale / 100.0)))

        # CAMPIONAMENTO
        indici_scelti = random.sample(range(totale_patch), numero_indici)

        # ORDINAMENTO
        if modalita == "Sequential":
            indici_scelti.sort()
        else:
            random.shuffle(indici_scelti)

        return indici_scelti


    # ==========================================
    # OPERAZIONI DI I/O SU DISCO
    # ==========================================
    def salva_su_disco(self):
        """
        Serializza l'albero self.data in formato JSON e lo scrive fisicamente su disco.
        """
        if not self.percorso_file_json:
            raise ValueError("Percorso del file JSON non impostato!")

        # Aggiorna il timestamp e ricalcola le statistiche prima di ogni salvataggio
        self.data["updated_at"] = self._ora_corrente_iso()
        self._ricalcola_progress()

        try:
            with open(self.percorso_file_json, 'w', encoding='utf-8') as f:
                # ensure_ascii=False permette di salvare correttamente eventuali accenti nelle note
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[DEBUG - ERROR] Errore critico durante il salvataggio del JSON: {e}")

    def carica_progetto_esistente(self, percorso_cartella):
        """
        Esplora la cartella selezionata, individua il file JSON, lo legge e
        popola l'oggetto self.data in memoria.
        """
        if not os.path.exists(percorso_cartella):
            print(f"[DEBUG - ERROR] La cartella {percorso_cartella} non esiste più.")
            return False

        try:
            # Ricerca del manifesto di progetto
            file_json_trovati = [f for f in os.listdir(percorso_cartella) if f.endswith('.json')]

            if not file_json_trovati:
                return False

            nome_file_json = file_json_trovati[0]
            percorso_completo_json = os.path.join(percorso_cartella, nome_file_json)

            # Deserializzazione in RAM
            with open(percorso_completo_json, 'r', encoding='utf-8') as file:
                self.data = json.load(file)

            # Impostazione dello stato interno del Controller
            self.percorso_file_json = percorso_completo_json
            self.percorso_cartella_progetto = percorso_cartella

            print(f"[DEBUG - PROJECT] Progetto caricato. {len(self.data['patches'])} patch trovate in totale.")
            return True

        except Exception as e:
            print(f"[DEBUG - ERROR] Eccezione durante la lettura del progetto: {e}")
            return False

    # ==========================================
    # CREAZIONE E MANIPOLAZIONE DATI
    # ==========================================
    def crea_nuovo_progetto(self, cartella_destinazione, nome_progetto, tipo_sorgente, parametri_setup, classi_etichette, dati_patch, callback_ui=None):
        """
        Costruisce l'intero JSON del progetto
        """
        self.percorso_cartella_progetto = cartella_destinazione
        self.percorso_file_json = os.path.join(self.percorso_cartella_progetto, f"{nome_progetto}_data.json")

        ora_attuale = self._ora_corrente_iso()

        # Normalizzazione dei parametri
        percentuale_raw = parametri_setup.get("percentuale", 100)
        percentuale = int(str(percentuale_raw).replace("%", ""))
        ordine = parametri_setup.get("ordine", "Sequential")

        # ==============================================
        # IDENTIFICAZIONE DEL POOL DI CAMPIONAMENTO
        # ==============================================
        # Se ci sono ROI, limitiamo il campionamento solo alle patch interne ad esse
        patch_nelle_roi = [p for p in dati_patch if p.get('roi_id') is not None]
        target_pool = patch_nelle_roi if patch_nelle_roi else dati_patch

        # Otteniamo gli indici matematici
        indici_attivi = self.genera_indici_campionamento(len(target_pool), percentuale, ordine)

        # Usiamo l'indirizzo di memoria 'id()' dell'oggetto per creare un Set che ci dirà se una patch deve essere etichettata o no.
        pool_attivi = set(id(target_pool[i]) for i in indici_attivi)

        # Inizializzazione dello scheletro JSON
        self.data = {
            "schema_version": "1.0",
            "case_id": nome_progetto,
            "source_type": tipo_sorgente,
            "source_path": parametri_setup.get("source_path", ""),
            "created_at": ora_attuale,
            "updated_at": ora_attuale,
            "image_metadata": {
                "width": parametri_setup.get("img_w", 0),
                "height": parametri_setup.get("img_h", 0),
                "channels": 3,
                "microns_per_pixel": None
            },
            "patching_config": {
                "patch_size": parametri_setup.get("grandezza_patch", 0),
                "patch_shape": "square",
                "overlap": 0,
                "generated_by_program": True
            },
            "sampling_config": {
                "roi_list": parametri_setup.get("roi_reali", []),
                "sampling_percentage": percentuale,
                "sampling_strategy": ordine.lower()
            },
            "labeling_config": {
              "classes": classi_etichette
            },
            "progress": {
                "total_patches": len(pool_attivi),
                "eligible_patches": len(target_pool),
                "shown_patches": 0,
                "labeled_patches": 0,
                "skipped_patches": 0,
                "completed": False
            },
            "patches": []
        }

        # Generazione massiva delle Patch
        totale_patch = len(dati_patch)
        step_aggiornamento = max(1, totale_patch // 100)

        for i, p_dati in enumerate(dati_patch, start=1):

            # Se l'indirizzo di memoria di questa patch è nel set viene marcata
            is_sampled = id(p_dati) in pool_attivi

            self.data["patches"].append({
                "patch_id": f"p_{i:06d}",
                "file_name": p_dati.get("percorso", None),
                "x": p_dati.get("x", 0),
                "y": p_dati.get("y", 0),
                "width": p_dati.get("w", p_dati.get("dimensione", 0)),
                "height": p_dati.get("h", p_dati.get("dimensione", 0)),
                "roi_id": p_dati.get("roi_id", None),
                "is_sampled": is_sampled,
                "selected_for_review": False,
                "shown_to_user": False,
                "status": "pending",
                "label": None,
                "annotation_text": None,
                "user_id": None,
                "reviewed_at": None
            })

            if callback_ui and i % step_aggiornamento == 0:
                percentuale_progresso = 30 + int((i / totale_patch) * 60)
                callback_ui(percentuale_progresso, f"Scrittura patch {i} di {totale_patch}...")

                import time
                time.sleep(0.001)

        if callback_ui:
            callback_ui(95, "Salvataggio file su disco in corso...")

        self.salva_su_disco()
        print(f"[DEBUG - PROJECT] Generato JSON. L'utente etichetterà {len(indici_attivi)} patch.")

    def aggiorna_patch(self, patch_id, label, note, da_rivedere, user_id="utente_locale"):
        """
        API chiamata durante l'Etichettatura: Aggiorna lo stato di una singola patch e innesca il salvataggio incrementale dei progressi
        """
        # Ricerca lineare della patch tramite il suo ID univoco
        patch_trovata = next((p for p in self.data["patches"] if p["patch_id"] == patch_id), None)

        if not patch_trovata:
            print(f"[DEBUG - ERROR] Patch {patch_id} non trovata nel JSON!")
            return

        # Aggiornamento Metadati Comuni
        patch_trovata["annotation_text"] = note if note else None
        patch_trovata["selected_for_review"] = da_rivedere
        patch_trovata["shown_to_user"] = True
        patch_trovata["user_id"] = user_id

        # Aggiornamento Logica Classificazione
        if label:
            patch_trovata["label"] = label
            patch_trovata["status"] = "labeled"
            patch_trovata["reviewed_at"] = self._ora_corrente_iso()
        else:
            # Se passa oltre senza assegnare un'etichetta
            patch_trovata["label"] = None
            patch_trovata["status"] = "skipped"
            patch_trovata["reviewed_at"] = None

        # Sincronizzazione sul file system
        self.salva_su_disco()