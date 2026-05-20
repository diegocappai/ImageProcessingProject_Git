from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QApplication
from PySide6.QtWidgets import QMessageBox, QDialog, QProgressDialog
from PySide6.QtCore import Qt

# --- Importa la MainWindow ---
from Interface_Package.main_view import MainWindow

# --- Importo Project Manager ---
from Models.project_model import ProjectManager

# --- Importa la Home ---
from Interface_Package.views.home_view import HomeView
from Models.home_model import HomeModel
from Controllers.home_controller import HomeController

# --- Importa New Project ---
from Interface_Package.views.new_project_view import NewProjectDialog

# --- Importa Dashboards ---
from Interface_Package.views.new_dashboard_view import NewProjectDashboardView
from Controllers.new_dashboard_controller import NewProjectDashboardController
from Interface_Package.views.dashboard_view import ProjectDashboardView
from Controllers.dashboard_controller import ProjectDashboardController

# --- Importa i Setup ---
from Interface_Package.views.setting_new_slide_view import ImpostazioniSlideDialog
from Interface_Package.views.setting_new_folder_view import ImpostazioniDialog
from Models.setup_model import SetupSlideModel, SetupFolderModel
from Controllers.setup_slide_controller import SetupSlideController
from Controllers.setup_folder_controller import SetupFolderController

# --- Importa Etichettatura ---
from Interface_Package.views.labeling_view import EtichettaturaWindow
from Controllers.labeling_controller import EtichettaturaController

# --- Importa Utils ---
from Utils.utils import crea_cartella_univoca


class AppController(QObject):

    def __init__(self):
        super().__init__()

        # Creazione dello scheletro visivo principale
        self.main_window = MainWindow()

        # nizializzazione della triade MVC iniziale
        self.home_model = HomeModel()
        self.home_view = HomeView()

        # Iniezione delle dipendenze
        self.home_controller = HomeController(
            self.home_model,
            self.home_view,
            on_nuovo_progetto=self.flusso_nuovo_progetto,
            on_carica_progetto=self.flusso_carica_progetto
        )

        # Impostiamo la Home come pagina di partenza
        self.main_window.stack.addWidget(self.home_view)

    def avvia(self):
        self.main_window.showMaximized()

    # ==========================================
    # FLUSSI DI NAVIGAZIONE E ROUTING GLOBALE
    # ==========================================

    def flusso_carica_progetto(self, percorso_cartella):
        """Gestisce l'azione di caricamento di un progetto esistente su disco"""
        print(f"[AppController] Avvio caricamento del progetto da {percorso_cartella}")

        self.project_manager = ProjectManager()
        successo = self.project_manager.carica_progetto_esistente(percorso_cartella)

        if successo:
            self.apri_dashboard_progetto()
        else:
            QMessageBox.critical(
                self.main_window,
                "Errore di Lettura",
                f"Impossibile leggere il progetto in:\n{percorso_cartella}\nIl file JSON potrebbe essere corrotto."
            )

    def flusso_nuovo_progetto(self):
        """Inizializza il Wizard per raccogliere i dati di un nuovo progetto."""
        dialog = NewProjectDialog(parent=self.main_window)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            dati_progetto = dialog.get_project_data()

            # Strategy Pattern: Smistamento in base al tipo di sorgente
            if dati_progetto["input_type"] == "Slide":
                self.avvia_setup_slide(dati_progetto)
            elif dati_progetto["input_type"] == "Dataset":
                self.avvia_setup_cartella(dati_progetto)

    def avvia_setup_slide(self, dati_progetto):
        """Flusso specifico per i file WSI (Whole Slide Image)"""
        model = SetupSlideModel()
        model.imposta_slide(dati_progetto["input_path"])

        view = ImpostazioniSlideDialog(parent=self.main_window)
        setup_controller = SetupSlideController(model, view)

        if setup_controller.esegui():
            classi_scelte = view.get_classi_etichette()
            if not classi_scelte:
                classi_scelte = ["Tessuto Normale", "Necrosi", "Infiammazione"]
            parametri = {
                "source_path": dati_progetto["input_path"],
                "img_w": model.larghezza_originale,
                "img_h": model.altezza_originale,
                "grandezza_patch": int(view.combo_patch.currentText()),
                "roi_reali": model.roi_list
            }

            # Delega la creazione fisica del JSON
            self.flusso_avvia_etichettatura(
                cartella_destinazione=dati_progetto["output_path"],
                nome=dati_progetto["name"],
                tipo="whole_image",
                parametri=parametri,
                classi_etichette=classi_scelte,
                setup_model=model
            )
        else:
            self.flusso_nuovo_progetto()

    def avvia_setup_cartella(self, dati_progetto):
        """Flusso specifico per le cartelle pre-processate di immagini (Dataset)"""
        model = SetupFolderModel()
        model.imposta_cartella(dati_progetto["input_path"])

        patch_totali = model.conta_patch_valide()

        if patch_totali == 0:
            QMessageBox.warning(self.main_window, "Errore", "Nessuna immagine valida trovata nella cartella.")
            return

        view = ImpostazioniDialog(n_patches=patch_totali, parent=self.main_window)
        setup_controller = SetupFolderController(model, view)

        if setup_controller.esegui():
            # Recuperiamo la percentuale pulita per i parametri
            testo_perc = view.combo_perc.currentText().replace("%", "")
            perc_scelta = int(testo_perc)

            parametri = {
                "source_path": dati_progetto["input_path"],
                "sampling_percentage": perc_scelta,
                "ordine": "Sequenziale" if view.radio_seq.isChecked() else "Random"
            }

            classi_scelte = view.get_classi_etichette()
            if not classi_scelte:
                classi_scelte = ["Tessuto Normale", "Necrosi", "Infiammazione"]

            self.flusso_avvia_etichettatura(
                cartella_destinazione=dati_progetto["output_path"],
                nome=dati_progetto["name"],
                tipo="patch_folder",
                parametri=parametri,
                setup_model=model,
                classi_etichette=classi_scelte
            )
        else:
            self.flusso_nuovo_progetto()
    # ==========================================
    # CREAZIONE FISICA DEL PROGETTO (JSON)
    # ==========================================

    def flusso_avvia_etichettatura(self, cartella_destinazione, nome, tipo, parametri, setup_model, classi_etichette):
        """Assembla i dati calcolati e genera fisicamente la struttura di cartelle e il JSON"""
        import os
        import shutil

        percorso_progetto, nome_definitivo = crea_cartella_univoca(cartella_destinazione, nome)

        self.progress_dialog = QProgressDialog("Calcolo dati in corso...", None, 0, 100, self.main_window)
        self.progress_dialog.setWindowTitle("Creazione in corso")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.show()

        QApplication.instance().processEvents()

        def aggiorna_ui(percentuale, testo):
            self.progress_dialog.setValue(percentuale)
            self.progress_dialog.setLabelText(testo)
            QApplication.instance().processEvents()

        try:
            # ========================================================
            # INPUT DA SLIDE
            # ========================================================
            if tipo == "whole_image":
                aggiorna_ui(15, "Inizializzazione copia file Slide nel progetto...")
                src_slide = parametri.get("source_path")

                if src_slide and os.path.exists(src_slide):
                    nome_file_slide = os.path.basename(src_slide)
                    cartella_slide_locale = os.path.join(percorso_progetto, "source_slide")
                    os.makedirs(cartella_slide_locale, exist_ok=True)

                    dest_slide = os.path.join(cartella_slide_locale, nome_file_slide)

                    aggiorna_ui(30, f"Copia di {nome_file_slide} in corso (Richiede tempo)...")
                    shutil.copy2(src_slide, dest_slide)

                    parametri["source_path"] = dest_slide
                    print(f"[DEBUG - SENIOR] Slide copiata internamente: {dest_slide}")

            # Estrazione dei dati dal modello di setup
            dati_estratti = setup_model.prepara_dati(callback_ui=aggiorna_ui)

            if isinstance(dati_estratti, list):
                dati_estratti = {"patches": dati_estratti}

            # Generazione iniziale del JSON da parte del ProjectManager
            self.project_manager = ProjectManager()
            self.project_manager.crea_nuovo_progetto(
                cartella_destinazione=percorso_progetto,
                nome_progetto=nome_definitivo,
                tipo_sorgente=tipo,
                parametri_setup=parametri,
                classi_etichette=classi_etichette,
                dati_calcolati=dati_estratti,
                callback_ui=aggiorna_ui
            )

            # ========================================================
            # INPUT DA CARTELLA
            # ========================================================
            if tipo == "patch_folder":
                perc_val = parametri.get("sampling_percentage", 100)
                ordine = parametri.get("ordine", "Sequenziale")

                self.project_manager.data["sampling_config"] = {
                    "sampling_percentage": perc_val,
                    "ordine": ordine
                }

                patch_list = self.project_manager.data.get("patches", [])
                totale = len(patch_list)
                da_campionare = max(1, int(totale * (perc_val / 100.0))) if totale > 0 else 0

                patch_strutturate = []
                for i, p in enumerate(patch_list):
                    if isinstance(p, dict):
                        p["is_sampled"] = False
                        nome_valido = p.get("file_name") or p.get("patch_id") or f"patch_{i}"
                        p["file_name"] = str(nome_valido)
                        p["patch_id"] = str(p.get("patch_id") or nome_valido)
                        patch_strutturate.append(p)
                    else:
                        patch_strutturate.append({
                            "patch_id": str(p),
                            "file_name": str(p),
                            "is_sampled": False
                        })

                if ordine == "Random":
                    import random
                    campionate = random.sample(patch_strutturate, min(da_campionare, len(patch_strutturate)))
                else:
                    campionate = patch_strutturate[:da_campionare]

                for p in campionate:
                    p["is_sampled"] = True

                cartella_patches_locale = os.path.join(percorso_progetto, "patches")
                os.makedirs(cartella_patches_locale, exist_ok=True)

                src_dir = parametri.get("source_path")
                tot_da_copiare = len(
                    patch_strutturate)

                for idx, p in enumerate(patch_strutturate):
                    nome_file = p["file_name"]
                    src_file = os.path.join(src_dir, nome_file)
                    dest_file = os.path.join(cartella_patches_locale, nome_file)

                    if os.path.exists(src_file):
                        shutil.copy2(src_file, dest_file)

                    if idx % max(1, tot_da_copiare // 5) == 0:
                        perc_progresso = 50 + int((idx / tot_da_copiare) * 45)
                        aggiorna_ui(perc_progresso, f"Salvataggio totale immagini... ({idx}/{tot_da_copiare})")

                self.project_manager.data["source_path"] = cartella_patches_locale
                self.project_manager.data["patches"] = patch_strutturate

                if "progress" not in self.project_manager.data:
                    self.project_manager.data["progress"] = {}
                self.project_manager.data["progress"]["total_patches"] = len(patch_strutturate)

                if hasattr(self.project_manager, "salva_su_disco"):
                    self.project_manager.salva_su_disco()

            aggiorna_ui(100, "Completato!")
            self.progress_dialog.close()
            self.home_controller.aggiungi_nuovo_progetto_ai_recenti(percorso_progetto)
            self.apri_dashboard_progetto()

        except Exception as e:
            self.progress_dialog.close()
            QMessageBox.critical(self.main_window, "Errore Critico",
                                 f"Si è verificato un errore nel salvataggio: {str(e)}")

    # ==========================================
    # TRANSIZIONI DI STATO
    # ==========================================

    def flusso_torna_alla_home(self):
        """Chiude il progetto attivo e ritorna alla schermata principale"""
        print("[AppController] Ritorno alla schermata Home.")
        self.home_controller.aggiorna_view()
        self.main_window.stack.setCurrentWidget(self.home_view)

    def flusso_torna_alla_dashboard(self):
        """
        Ritorna alla Dashboard
        """
        print("[AppController] Ritorno alla Dashboard e pulizia memoria.")
        self.dashboard_controller.aggiorna_vista()
        self.main_window.stack.setCurrentWidget(self.dashboard_view)

        # Svuotiamo la memoria distruggendo la View di Etichettatura
        if hasattr(self, 'etichettatura_view') and self.etichettatura_view:
            self.main_window.stack.removeWidget(self.etichettatura_view)
            self.etichettatura_view.deleteLater()

            self.etichettatura_view = None
            self.etichettatura_controller = None

    def apri_dashboard_progetto(self):
        """Routing intelligente per istanziare la dashboard corretta in base al tipo di input"""

        # Scopriamo che tipo di progetto stiamo aprendo
        tipo_sorgente = self.project_manager.data.get("source_type", "")

        if tipo_sorgente in ["whole_image", "Slide"]:


            self.dashboard_view = NewProjectDashboardView()
            self.dashboard_controller = NewProjectDashboardController(self.project_manager, self.dashboard_view)

        else:


            self.dashboard_view = ProjectDashboardView()
            self.dashboard_controller = ProjectDashboardController(self.project_manager, self.dashboard_view)


        self.dashboard_controller.naviga_a_etichettatura = self.apri_schermata_etichettatura
        self.dashboard_controller.naviga_a_home = self.flusso_torna_alla_home

        self.main_window.stack.addWidget(self.dashboard_view)
        self.main_window.stack.setCurrentWidget(self.dashboard_view)

    def apri_schermata_etichettatura(self, roi_selezionate=None, patch_selezionate=None):
        self.etichettatura_view = EtichettaturaWindow()

        self.etichettatura_controller = EtichettaturaController(
            self.project_manager,
            self.etichettatura_view,
            roi_selezionate,
            patch_selezionate
        )

        self.etichettatura_controller.naviga_alla_dashboard = self.flusso_torna_alla_dashboard

        self.main_window.stack.addWidget(self.etichettatura_view)
        self.main_window.stack.setCurrentWidget(self.etichettatura_view)