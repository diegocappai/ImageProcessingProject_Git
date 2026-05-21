from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                               QLabel, QComboBox, QRadioButton, QPushButton, QMessageBox)
from PySide6.QtGui import QCloseEvent
from Interface_Package.widgets.class_selector_view import ClassSelectorWidget
from Utils.ui_settings import CLASSI_DEFAULT


class ImpostazioniDialog(QDialog):
    """
    View per la configurazione dei progetti basati su cartelle (Dataset)
    """
    def __init__(self, n_patches: int, parent=None):
        super().__init__(parent)

        # Stato iniziale passato dal Controller
        self.n_patches = n_patches

        self.setWindowTitle("Configurazione Progetto - Dataset Folder")
        self.setFixedSize(500, 450)

        self.init_ui()

    def init_ui(self):
        # Layout principale
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Layout interno
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # Info Dataset
        patch_label = QLabel(f"{self.n_patches} patch valide trovate nella cartella.")
        patch_label.setProperty("class", "InstructionLabel")
        content_layout.addWidget(patch_label)

        # Percentuale di Campionamento
        perc_layout = QHBoxLayout()
        perc_label = QLabel("Percentuale di patch da etichettare:")

        self.combo_perc = QComboBox()
        # Generazione dinamica
        self.combo_perc.addItems([f"{i}%" for i in range(10, 101, 10)])
        self.combo_perc.setCurrentText("50%")

        perc_layout.addWidget(perc_label)
        perc_layout.addWidget(self.combo_perc)
        perc_layout.addStretch()
        content_layout.addLayout(perc_layout)

        # Ordinamento Visualizzazione
        order_label = QLabel("Ordine di visualizzazione:")
        order_label.setProperty("class", "SectionTitle")
        content_layout.addWidget(order_label)

        self.radio_seq = QRadioButton("Sequenziale")
        self.radio_seq.setChecked(True)

        self.radio_rand = QRadioButton("Random")

        content_layout.addWidget(self.radio_seq)
        content_layout.addWidget(self.radio_rand)

        content_layout.addSpacing(10)

        # --- GESTIONE CLASSI ETICHETTE --
        self.class_selector = ClassSelectorWidget(default_classes=CLASSI_DEFAULT)
        content_layout.addWidget(self.class_selector)

        content_layout.addSpacing(10)

        # Action Area (Bottoni Finali)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_annulla = QPushButton("Annulla")
        self.btn_salva = QPushButton("Salva ed Esegui")
        self.btn_salva.setProperty("class", "PrimaryButton")

        self.btn_annulla.clicked.connect(self.reject)
        self.btn_salva.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_annulla)
        btn_layout.addWidget(self.btn_salva)

        content_layout.addLayout(btn_layout)
        main_layout.addLayout(content_layout)

    # ==========================================
    # API PUBBLICA
    # ==========================================

    def get_classi_etichette(self) -> list:
        """Metodo pubblico chiamato dal Controller per estrarre le etichette selezionate dall'utente."""
        return self.class_selector.get_selected_classes()

    def closeEvent(self, event: QCloseEvent):
        """
        Overriding dell'evento di chiusura della finestra
        """
        box = QMessageBox(self)
        box.setWindowTitle("Conferma Uscita")
        box.setText("Sicuro di voler uscire?\nI parametri del progetto in fase di creazione andranno persi.")
        box.setIcon(QMessageBox.Icon.Warning)

        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.No)

        risposta = box.exec()

        if risposta == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()