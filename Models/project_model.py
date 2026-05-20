import os
import random
import json
from datetime import datetime, timezone


class ProjectManager:
    """
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
        Scansiona l'intero array delle patch e aggiorna il contatore globale del progresso e le statistiche delle singole ROI
        """
        if "patches" not in self.data or "progress" not in self.data:
            return

        totale = len(self.data["patches"])
        etichettate = sum(1 for p in self.data["patches"] if p["status"] == "labeled")
        saltate = sum(1 for p in self.data["patches"] if p["status"] == "skipped")
        mostrate = sum(1 for p in self.data["patches"] if p.get("shown_to_user", False))

        self.data["progress"]["total_patches"] = totale
        self.data["progress"]["labeled_patches"] = etichettate
        self.data["progress"]["skipped_patches"] = saltate
        self.data["progress"]["shown_patches"] = mostrate

        pendenti = sum(1 for p in self.data["patches"] if p["status"] == "pending" and p.get("is_sampled", False))
        self.data["progress"]["completed"] = (pendenti == 0 and totale > 0)

        if "sampling_config" in self.data and "roi_list" in self.data["sampling_config"]:
            for roi in self.data["sampling_config"]["roi_list"]:
                roi_id = roi["id"]

                patch_roi = [p for p in self.data["patches"] if p.get("roi_id") == roi_id]

                sampling_roi = sum(1 for p in patch_roi if p.get("is_sampled", False))
                labeled_in_roi = sum(1 for p in patch_roi if p["status"] == "labeled" and p.get("is_sampled", False))

                if "stats" not in roi:
                    roi["stats"] = {"total_valid": len(patch_roi), "sampled": 0, "labeled": 0}

                roi["stats"]["sampled"] = sampling_roi
                roi["stats"]["labeled"] = labeled_in_roi

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

        self.data["updated_at"] = self._ora_corrente_iso()
        self._ricalcola_progress()

        try:
            with open(self.percorso_file_json, 'w', encoding='utf-8') as f:
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
            file_json_trovati = [f for f in os.listdir(percorso_cartella) if f.endswith('.json')]

            if not file_json_trovati:
                return False

            nome_file_json = file_json_trovati[0]
            percorso_completo_json = os.path.join(percorso_cartella, nome_file_json)

            with open(percorso_completo_json, 'r', encoding='utf-8') as file:
                self.data = json.load(file)

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
    def crea_nuovo_progetto(self, cartella_destinazione, nome_progetto, tipo_sorgente, parametri_setup,
                            classi_etichette, dati_calcolati, callback_ui=None):
        """
        Costruisce l'intero JSON del progetto assemblando i dati pre-calcolati dal Model
        """
        self.percorso_cartella_progetto = cartella_destinazione
        self.percorso_file_json = os.path.join(self.percorso_cartella_progetto, f"{nome_progetto}_data.json")

        ora_attuale = self._ora_corrente_iso()

        lista_roi = dati_calcolati.get("rois", [])
        lista_patch = dati_calcolati.get("patches", [])

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
                "roi_list": lista_roi
            },
            "labeling_config": {
                "classes": classi_etichette
            },
            "progress": {
                "total_patches": len(lista_patch),
                "eligible_patches": len(lista_patch),
                "shown_patches": 0,
                "labeled_patches": 0,
                "skipped_patches": 0,
                "completed": False
            },
            "patches": []
        }

        totale_patch = len(lista_patch)
        step_aggiornamento = max(1, totale_patch // 100)
        totale_campionate = 0

        for i, p_dati in enumerate(lista_patch, start=1):

            is_sampled = p_dati.get("is_sampled", False)
            if is_sampled:
                totale_campionate += 1

            self.data["patches"].append({
                "patch_id": p_dati.get("id", f"p_{i:06d}"),
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

        if callback_ui:
            callback_ui(95, "Salvataggio file su disco in corso...")

        self.salva_su_disco()
        print(
            f"[DEBUG - PROJECT] Generato JSON. L'utente etichetterà {totale_campionate} patch su {totale_patch} valide trovate.")

    def aggiorna_patch(self, patch_id, label, note, da_rivedere, user_id="utente_locale"):
        """
        API chiamata durante l'Etichettatura: Aggiorna lo stato di una singola patch e innesca il salvataggio incrementale dei progressi
        """
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

    def modifica_percentuale_roi(self, roi_id, nuova_percentuale):
        """
        Modifica dinamicamente il numero di patch da etichettare per una ROI,
        proteggendo le patch già etichettate.
        """

        roi = next((r for r in self.data["sampling_config"]["roi_list"] if r["id"] == roi_id), None)
        if not roi:
            return False, f"ROI {roi_id} non trovata nel progetto.", nuova_percentuale

        patch_roi = [p for p in self.data["patches"] if p.get("roi_id") == roi_id]
        totale_valide = len(patch_roi)

        if totale_valide == 0:
            return False, "Nessuna patch in questa ROI.", nuova_percentuale

        patch_attualmente_campionate = [p for p in patch_roi if p.get("is_sampled", False)]

        patch_gia_lavorate = [p for p in patch_attualmente_campionate if p["status"] != "pending"]
        totale_lavorate = len(patch_gia_lavorate)

        nuovo_target_campionate = max(1, int(totale_valide * (nuova_percentuale / 100.0)))

        percentuale_finale_applicata = nuova_percentuale
        messaggio = "Percentuale aggiornata con successo."

        if nuovo_target_campionate < totale_lavorate:
            nuovo_target_campionate = totale_lavorate
            percentuale_finale_applicata = int((totale_lavorate / totale_valide) * 100)
            messaggio = f"Hai già visualizzato {totale_lavorate} patch di questa ROI. \nLa percentuale non può scendere sotto il {percentuale_finale_applicata}%."

        campionate_attuali_count = len(patch_attualmente_campionate)
        delta = nuovo_target_campionate - campionate_attuali_count

        if delta > 0:
            patch_disponibili = [p for p in patch_roi if not p.get("is_sampled", False)]
            da_aggiungere = random.sample(patch_disponibili, min(delta, len(patch_disponibili)))

            for p in da_aggiungere:
                p["is_sampled"] = True

        elif delta < 0:
            patch_rimovibili = [p for p in patch_attualmente_campionate if p["status"] == "pending"]
            da_rimuovere = random.sample(patch_rimovibili, abs(delta))

            for p in da_rimuovere:
                p["is_sampled"] = False

        roi["sampling_percentage"] = percentuale_finale_applicata
        roi["stats"]["sampled"] = nuovo_target_campionate

        self.salva_su_disco()

        return True, messaggio, percentuale_finale_applicata