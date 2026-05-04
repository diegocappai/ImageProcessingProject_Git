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
    """
    Application Controller
    """

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
        self.main_window.show()

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
            parametri = {
                "source_path": dati_progetto["input_path"],
                "img_w": model.larghezza_originale,
                "img_h": model.altezza_originale,
                "grandezza_patch": int(view.combo_patch.currentText()),
                "percentuale": view.combo_perc.currentText(),
                "ordine": "Sequenziale" if view.radio_seq.isChecked() else "Random",
                "roi_reali": model.roi_list
            }

            # Delega la creazione fisica del JSON
            self.flusso_avvia_etichettatura(
                cartella_destinazione=dati_progetto["output_path"],
                nome=dati_progetto["name"],
                tipo="whole_image",
                parametri=parametri,
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
            parametri = {
                "source_path": dati_progetto["input_path"],
                "percentuale": view.combo_perc.currentText(),
                "ordine": "Sequenziale" if view.radio_seq.isChecked() else "Random"
            }

            self.flusso_avvia_etichettatura(
                cartella_destinazione=dati_progetto["output_path"],
                nome=dati_progetto["name"],
                tipo="patch_folder",
                parametri=parametri,
                setup_model=model
            )
        else:
            self.flusso_nuovo_progetto()

    # ==========================================
    # CREAZIONE FISICA DEL PROGETTO (JSON)
    # ==========================================

    def flusso_avvia_etichettatura(self, cartella_destinazione, nome, tipo, parametri, setup_model):
        """
        Assembla i dati calcolati e genera fisicamente la struttura di cartelle e il JSON
        """
        percorso_progetto, nome_definitivo = crea_cartella_univoca(cartella_destinazione, nome)

        # Creazione finestra di progresso
        self.progress_dialog = QProgressDialog("Calcolo dati in corso...", None, 0, 100, self.main_window)
        self.progress_dialog.setWindowTitle("Creazione in corso")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.show()

        QApplication.instance().processEvents()

        # Funzione di Callback iniettata nei modelli per aggiornare la UI in tempo reale
        def aggiorna_ui(percentuale, testo):
            self.progress_dialog.setValue(percentuale)
            self.progress_dialog.setLabelText(testo)
            QApplication.instance().processEvents()

        try:
            # Calcolo matematico e filtraggio dei dati
            dati_patch = setup_model.prepara_dati(callback_ui=aggiorna_ui)

            # Generazione del JSON
            self.project_manager = ProjectManager()
            self.project_manager.crea_nuovo_progetto(
                cartella_destinazione=percorso_progetto,
                nome_progetto=nome_definitivo,
                tipo_sorgente=tipo,
                parametri_setup=parametri,
                dati_patch=dati_patch,
                callback_ui=aggiorna_ui
            )

            # Chiusura barra progresso, aggiornamento Home e passaggio alla Dashboard
            self.progress_dialog.close()
            self.home_controller.aggiungi_nuovo_progetto_ai_recenti(percorso_progetto)
            self.apri_dashboard_progetto()

        except Exception as e:
            self.progress_dialog.close()
            QMessageBox.critical(self.main_window, "Errore Critico", f"Si è verificato un errore: {str(e)}")

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
        """Istanzia e visualizza la pagina di riepilogo del progetto"""
        self.dashboard_view = ProjectDashboardView()
        self.dashboard_controller = ProjectDashboardController(self.project_manager, self.dashboard_view)

        self.dashboard_controller.naviga_a_etichettatura = self.apri_schermata_etichettatura
        self.dashboard_controller.naviga_a_home = self.flusso_torna_alla_home

        self.main_window.stack.addWidget(self.dashboard_view)
        self.main_window.stack.setCurrentWidget(self.dashboard_view)

    def apri_schermata_etichettatura(self):
        self.etichettatura_view = EtichettaturaWindow()

        self.etichettatura_controller = EtichettaturaController(self.project_manager, self.etichettatura_view)

        self.etichettatura_controller.naviga_alla_dashboard = self.flusso_torna_alla_dashboard

        self.main_window.stack.addWidget(self.etichettatura_view)
        self.main_window.stack.setCurrentWidget(self.etichettatura_view)