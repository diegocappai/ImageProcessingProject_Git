from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QMessageBox

from ImageManager_Package import get_manager
from Interface_Package.views.new_dashboard_view import NewRoiDialog
from Utils.ui_settings import PALETTE_COLORI

import random

class NewProjectDashboardController:
    """Controller della Dashboard per progetti WSI (Whole Slide Image)"""
    def __init__(self, project_manager, dashboard_view):
        self.project_manager = project_manager
        self.view = dashboard_view

        # Mappo i segnali generati dall'utente ai metodi
        self.view.cambio_percentuale_roi.connect(self._gestisci_cambio_percentuale)
        self.view.richiesta_inizio_etichettatura.connect(self._on_inizio_etichettatura)
        self.view.richiesta_ritorno_home.connect(self._on_ritorno_home)
        self.view.nuova_roi_disegnata.connect(self._gestisci_nuova_roi)
        self.view.stato_roi_modificato.connect(self._salva_stato_roi)
        self.view.richiesta_campionamento_mirato.connect(self._gestisci_campionamento_mirato)
        self.view.richiesta_eliminazione_roi.connect(self._gestisci_eliminazione_roi)

        self.naviga_a_etichettatura = None
        self.naviga_a_home = None

        self._inizializza_minimappa()
        self.aggiorna_vista()

    def _inizializza_minimappa(self):
        """Crea il motore di estrazione PyVips e lo cede in gestione alla View"""
        source_path = self.project_manager.data.get("source_path")
        source_type = self.project_manager.data.get("source_type")

        if source_type in ["whole_image", "Slide"] and source_path:
            try:
                manager = get_manager('Slide', source_path, tile_w=0, tile_h=0)
                # Passiamo il manager alla View
                self.view.minimap_view.imposta_motore_immagini(manager)
            except Exception as e:
                print(f"[DEBUG - ERROR] Impossibile inizializzare il manager per la Dashboard: {e}")

    def aggiorna_vista(self):
        """
        Estraggo il JSON e lo invio alla UI per ripopolare la tabella
        """
        data = self.project_manager.data
        classi = data.get("labeling_config", {}).get("classes", [])

        color_map_ui = {
            classe: PALETTE_COLORI[i% len(PALETTE_COLORI)]
            for i, classe in enumerate(classi)
        }
        self.view.display_project({**data, "color_map_generata": color_map_ui})

    # ==========================================
    # GESTIONE INTERAZIONI UTENTE
    # ==========================================

    def _gestisci_cambio_percentuale(self, roi_id, nuova_percentuale):
        """
        Invocato qaundo l'utente cambia il valore della percentuale di campionamento di una ROI
        """
        successo, messaggio, perc_effettiva = self.project_manager.modifica_percentuale_roi(roi_id, nuova_percentuale)

        if not successo:
            QMessageBox.critical(self.view, "Errore", messaggio)
        elif perc_effettiva != nuova_percentuale:
            QMessageBox.warning(self.view, "Limite Raggiunto", messaggio)

        self.aggiorna_vista()

    def _on_inizio_etichettatura(self, roi_selezionate):
        """Controlla la validità del progettoprima e lancia la sessione di etichettatura"""

        data = self.project_manager.data
        lista_roi = data.get("sampling_config", {}).get("roi_list", [])

        if not lista_roi:
            QMessageBox.warning(
                self.view,
                "Nessuna ROI definita",
                "Impossibile avviare la sessione di etichettatura.\n\n"
                "Non hai disegnato alcuna Region of Interest (ROI) per questa slide, "
                "pertanto non ci sono patch da estrarre e mostrare."
            )
            return


        patch_totali_campionate = sum(1 for p in data.get("patches", []) if p.get("is_sampled"))

        if patch_totali_campionate == 0:
            QMessageBox.warning(
                self.view,
                "Nessuna Patch Campionata",
                "Impossibile procedere.\n\n"
                "Hai disegnato delle ROI, ma nessuna patch risulta campionata (percentuale allo 0%).\n"
                "Modifica la percentuale di campionamento delle ROI dalla tabella prima di iniziare."
            )
            return

        if self.naviga_a_etichettatura:
            self.naviga_a_etichettatura(roi_selezionate)

    def _on_ritorno_home(self):
        """Ritorno alla schemata principale dell'applicazione"""
        if self.naviga_a_home:
            self.naviga_a_home()

    # ==========================================
    # LOGICA DI DISEGNO ROI E CAMPIONAMENTO
    # ==========================================

    def _gestisci_nuova_roi(self, rects_disegnati):
        """
        Intercetto il rettangolo disegnato (ROI), forzo i suoi bordi ad allinearsi (snap) alle patch reali della
        griglia e salvo la nuova ROI.
        """
        if not rects_disegnati:
            return

        rect_utente = rects_disegnati[-1]

        # Applico il Grid Snapping per allinearmi alle patch reali
        rect_snappato, patch_coinvolte = self._applica_grid_snapping(rect_utente)

        if not rect_snappato:
            QMessageBox.information(self.view, "Area ignorata",
                                    "La ROI non ingloba abbastanza tessuto (minimo 40% di una patch).\nIl disegno verrà annullato.")
            self.view.minimap_view.undo_last_roi()
            return

        # Assegno un nuovo ID senza sovrascrivere quelli vecchi
        lista_roi = self.project_manager.data.get("sampling_config", {}).get("roi_list", [])
        if lista_roi:
            numeri_roi = []
            for r in lista_roi:
                try:
                    numeri_roi.append(int(r["id"].split("_")[1]))
                except (IndexError, ValueError):
                    numeri_roi.append(0)
            max_id = max(numeri_roi)
        else:
            max_id = 0

        roi_id = f"ROI_{max_id + 1}"
        patch_totali_valide = len(patch_coinvolte)

        # Finestra di settaggio e conferma ROI
        dialog = NewRoiDialog(roi_id, patch_totali_valide, self.view)
        if dialog.exec():
            perc_camp, ordine = dialog.get_dati()
            da_campionare = int(patch_totali_valide * (perc_camp / 100.0))
            patch_scelte = random.sample(patch_coinvolte, da_campionare)

            for p in patch_coinvolte:
                p["roi_id"] = roi_id
                p["is_sampled"] = False

            for p in patch_scelte:
                p["is_sampled"] = True

            nuova_roi = {
                "id": roi_id,
                "x": int(rect_snappato.x()),
                "y": int(rect_snappato.y()),
                "width": int(rect_snappato.width()),
                "height": int(rect_snappato.height()),
                "sampling_percentage": perc_camp,
                "show_order": ordine,
                "is_active": True,
                "stats": {
                    "total_valid": patch_totali_valide,
                    "sampled": da_campionare,
                    "labeled": 0,
                    "shown_to_user": 0
                }
            }

            if "sampling_config" not in self.project_manager.data:
                self.project_manager.data["sampling_config"] = {"roi_list": []}

            self.project_manager.data["sampling_config"]["roi_list"].append(nuova_roi)
            self.project_manager.salva_su_disco()

            # Rimuovo il disegno della ROI per lasciare la snap grid
            self.view.minimap_view.undo_last_roi()
            self.aggiorna_vista()
        else:
            self.view.minimap_view.undo_last_roi()

    def _gestisci_eliminazione_roi(self, roi_id: str):
        """
        Eliminazione sicura delle ROI: Valuta la presenza di patch già etichettate
        """
        data = self.project_manager.data
        patches = data.get("patches", [])

        patch_collegate = [p for p in patches if isinstance(p, dict) and p.get("roi_id") == roi_id]

        ha_patch_etichettate = any(
            p.get("status") == "labeled" or p.get("label") is not None
            for p in patch_collegate
        )

        if ha_patch_etichettate:
            QMessageBox.warning(
                self.view,
                "Impossibile eliminare ROI",
                f"Impossibile eliminare la {roi_id}.\n\n"
                f"L'area contiene delle patch a cui è stata già assegnata un'etichetta.\n"
            )
            return

        risposta = QMessageBox.question(
            self.view,
            "Conferma Eliminazione",
            f"Sei sicuro di voler eliminare definitivamente la {roi_id}?\n\n",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if risposta != QMessageBox.StandardButton.Yes:
            return


        print(f"[DEBUG] Avvio eliminazione fisica e rollback della {roi_id}")

        roi_list = data.get("sampling_config", {}).get("roi_list", [])
        data["sampling_config"]["roi_list"] = [r for r in roi_list if r.get("id") != roi_id]

        # Elimino l'appartenenza delle patch alla ROI
        for p in patch_collegate:
            p["roi_id"] = None
            p["is_sampled"] = False
            p["shown_to_user"] = False
            p["status"] = None

        self.project_manager.salva_su_disco()
        self.aggiorna_vista()

        QMessageBox.information(
            self.view,
            "ROI Eliminata",
            f"La {roi_id} è stata rimossa con successo."
        )

    def _salva_stato_roi(self, roi_id: str, is_active: bool):
        """Salva nel JSON lo stato della ROI"""
        roi_list = self.project_manager.data["sampling_config"]["roi_list"]

        for roi in roi_list:
            if roi.get("id") == roi_id:
                roi["is_active"] = is_active
                self.project_manager.salva_su_disco()
                break

    def _gestisci_campionamento_mirato(self, rect_selezione):
        """Calcola quali patch cadono nell'area Ctrl+Drag e lancia l'etichettatura mirata"""
        patch_da_etichettare = []
        roi_coinvolte = set()

        # Intercetto le patch toccate dal rettangolo
        for patch in self.project_manager.data.get("patches", []):
            if not patch.get("roi_id"):
                continue

            w = patch.get("width", patch.get("w", 0))
            h = patch.get("height", patch.get("h", 0))
            patch_rect = QRectF(patch["x"], patch["y"], w, h)

            if rect_selezione.intersects(patch_rect):
                patch_da_etichettare.append(patch)
                roi_coinvolte.add(patch["roi_id"])

        if not patch_da_etichettare:
            QMessageBox.warning(self.view, "Selezione Vuota", "L'area selezionata non contiene patch di tessuto valide.\nProva a selezionare un'area più ampia o con maggior densità cellulare.")
            return

        # Conferma utente
        numero_patch = len(patch_da_etichettare)
        box_conferma = QMessageBox(self.view)
        box_conferma.setWindowTitle("Campionamento Mirato")
        box_conferma.setText(f"<b>{numero_patch}</b> patch selezionate.")
        box_conferma.setInformativeText("Procedere con l'etichettatura?")
        box_conferma.setIcon(QMessageBox.Icon.Question)

        btn_annulla = box_conferma.addButton("Annulla", QMessageBox.ButtonRole.RejectRole)
        btn_etichetta = box_conferma.addButton("Etichetta", QMessageBox.ButtonRole.AcceptRole)
        box_conferma.setDefaultButton(btn_etichetta)
        box_conferma.exec()

        if box_conferma.clickedButton() == btn_annulla:
            return

        patch_effettivamente_modificate = [p for p in patch_da_etichettare if not p.get("is_sampled", False)]

        if patch_effettivamente_modificate:
            for p in patch_effettivamente_modificate:
                p["is_sampled"] = True

            # Aggiorno i contatori dividendo il numero correttamente per ogni singola ROI
            for roi in self.project_manager.data.get("sampling_config", {}).get("roi_list", []):
                if roi["id"] in roi_coinvolte:
                    incremento = sum(1 for p in patch_effettivamente_modificate if p.get("roi_id") == roi["id"])
                    roi["stats"]["sampled"] += incremento

            self.project_manager.salva_su_disco()
            self.aggiorna_vista()

        # Inizio sessione mirata
        id_patch_selezionate = [p["patch_id"] for p in patch_da_etichettare]

        if hasattr(self, 'naviga_a_etichettatura') and self.naviga_a_etichettatura:
            self.naviga_a_etichettatura(roi_selezionate=None, patch_selezionate=id_patch_selezionate)

    def _applica_grid_snapping(self, rect_utente: QRectF):
        """
        Motore di Grid Snapping: analizza l'area disegnata e restituisce solo le patch sovrapposte per almeno il 40%.
        """
        patch_accettate = []
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')

        patches = self.project_manager.data.get("patches", [])

        for patch in patches:
            # Ignoro patch che appartengono già ad altre ROI
            if patch.get("roi_id"): continue

            w = patch.get("width", patch.get("w", 0))
            h = patch.get("height", patch.get("h", 0))
            patch_rect = QRectF(patch["x"], patch["y"], w, h)

            intersezione = rect_utente.intersected(patch_rect)

            if not intersezione.isEmpty():
                area_intersezione = intersezione.width() * intersezione.height()
                area_patch = w * h

                # 40% di copertura richiesta per essere ritenuta valida
                if area_patch > 0 and (area_intersezione / area_patch) >= 0.40:
                    patch_accettate.append(patch)

                    # Estendo i confini della ROI
                    if patch["x"] < min_x: min_x = patch["x"]
                    if patch["y"] < min_y: min_y = patch["y"]
                    if patch["x"] + w > max_x: max_x = patch["x"] + w
                    if patch["y"] + h > max_y: max_y = patch["y"] + h

        if not patch_accettate:
            return None, []

        rect_perfetto = QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
        return rect_perfetto, patch_accettate
