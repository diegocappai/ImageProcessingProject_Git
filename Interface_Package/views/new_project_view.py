from pathlib import Path
from typing import Dict, Optional

from PySide6.QtWidgets import (QDialog, QLabel, QPushButton, QVBoxLayout,
                               QHBoxLayout, QFileDialog, QLineEdit,
                               QFormLayout, QMessageBox)


class NewProjectDialog(QDialog):
    """
    View-Controller per la creazione guidata di un nuovo progetto
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Digital Pathology Lab - Crea Nuovo Progetto")
        self.setMinimumWidth(500)

        self.detected_input_type: Optional[str] = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Nome Progetto
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Es: Paziente_01_Biopsia")
        form_layout.addRow("Nome Progetto:", self.input_name)

        # Output Path (Destinazione)
        out_layout = QHBoxLayout()
        self.input_out_path = QLineEdit()
        self.btn_out_path = QPushButton("Sfoglia...")
        self.btn_out_path.clicked.connect(self._browse_output)
        out_layout.addWidget(self.input_out_path)
        out_layout.addWidget(self.btn_out_path)
        form_layout.addRow("Salva in:", out_layout)

        # Input Path (Sorgente: Slide o Cartella)
        in_layout = QHBoxLayout()
        self.input_in_path = QLineEdit()
        self.input_in_path.setPlaceholderText("Percorso Slide o Cartella Dataset")

        self.btn_path_file = QPushButton("📄 Slide")
        self.btn_path_file.clicked.connect(self._browse_input_file)

        self.btn_path_folder = QPushButton("📁 Cartella")
        self.btn_path_folder.clicked.connect(self._browse_input_folder)

        in_layout.addWidget(self.input_in_path)
        in_layout.addWidget(self.btn_path_file)
        in_layout.addWidget(self.btn_path_folder)
        form_layout.addRow("Sorgente:", in_layout)

        # Feedback Visivo (Rilevamento Automatico)
        self.label_detection = QLabel("Tipologia: in attesa di input...")
        # Stile di default
        self.label_detection.setStyleSheet("color: gray; font-style: italic;")
        form_layout.addRow("", self.label_detection)

        layout.addLayout(form_layout)

        # Action Area
        btn_box = QHBoxLayout()
        self.btn_annulla = QPushButton("Annulla")
        self.btn_annulla.clicked.connect(self.reject)  # QDialog.Rejected

        self.btn_crea = QPushButton("Crea Progetto")
        self.btn_crea.setProperty("class", "PrimaryButton")
        self.btn_crea.clicked.connect(self._validate_and_accept)

        btn_box.addStretch()
        btn_box.addWidget(self.btn_annulla)
        btn_box.addWidget(self.btn_crea)
        layout.addLayout(btn_box)

        # Aggiorna l'etichetta in tempo reale mentre l'utente digita o incolla un path
        self.input_in_path.textChanged.connect(self._auto_detect_input)

    # ==========================================
    # METODI DI BROWSING
    # ==========================================
    def _browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleziona cartella di destinazione", str(Path.home()))
        if folder:
            self.input_out_path.setText(folder)

    def _browse_input_file(self):
        # Filtro per le estensioni WSI più comuni supportate da librerie come OpenSlide/PyVips
        filtro = "Slide Images (*.tif *.tiff *.svs *.ndpi *.vms *.png *.jpg *jpeg);;Tutti i file (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleziona Slide Istologica", str(Path.home()), filtro)

        if file_path:
            self.input_in_path.setText(file_path)

    def _browse_input_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleziona Cartella Dataset", str(Path.home()))
        if folder:
            self.input_in_path.setText(folder)

    # ==========================================
    # LOGICA DI PRESENTAZIONE E VALIDAZIONE UI
    # ==========================================
    def _auto_detect_input(self, path_str: str):
        """
        Analizza superficialmente il percorso inserito per dare feedback immediato
        """
        if not path_str:
            self.label_detection.setText("Tipologia: In attesa di input...")
            self.label_detection.setStyleSheet("color: gray; font-style: italic;")
            self.detected_input_type = None
            return

        path = Path(path_str)

        if not path.exists():
            self.label_detection.setText("❌ Errore: Il percorso non esiste nel sistema.")
            self.label_detection.setStyleSheet("color: #E74C3C; font-weight: bold;")
            self.detected_input_type = None
            return

        # Rilevamento Slide
        if path.is_file():
            estensioni_slide = ['.tif', '.tiff', '.svs', '.ndpi', '.vms', '.png', '.jpg', '.jpeg']
            if path.suffix.lower() in estensioni_slide:
                self.label_detection.setText("✅ Rilevata: Whole Slide Image (WSI)")
                self.label_detection.setStyleSheet("color: #2ECC71; font-weight: bold;")
                self.detected_input_type = "Slide"
            else:
                self.label_detection.setText("⚠️ Attenzione: Estensione file non standard.")
                self.label_detection.setStyleSheet("color: #F39C12; font-weight: bold;")
                self.detected_input_type = None

        # Rilevamento Dataset (Cartella)
        elif path.is_dir():
            self.label_detection.setText("✅ Rilevato: Dataset di Patch (Cartella)")
            self.label_detection.setStyleSheet("color: #2ECC71; font-weight: bold;")
            self.detected_input_type = "Dataset"

    def _validate_and_accept(self):
        """
        Esegue i controlli finali sui campi obbligatori prima di passare il l'ggetto al Controller
        """
        if not self.input_name.text().strip():
            QMessageBox.warning(self, "Campi Incompleti", "Per favore, inserisci un nome per il progetto.")
            return

        if not self.input_out_path.text().strip():
            QMessageBox.warning(self, "Campi Incompleti", "Per favore, seleziona una cartella di destinazione.")
            return

        if not self.detected_input_type:
            QMessageBox.warning(self, "Sorgente Non Valida",
                                "Assicurati di aver inserito una Slide o una cartella valida.")
            return

        self.accept()

    # ==========================================
    # API PUBBLICA
    # ==========================================
    def get_project_data(self) -> Dict[str, str]:
        """
        Restituisce un dizionario formattato con i parametri confermati dall'utente
        """
        return {
            "name": self.input_name.text().strip(),
            "output_path": self.input_out_path.text().strip(),
            "input_path": self.input_in_path.text().strip(),
            "input_type": self.detected_input_type
        }