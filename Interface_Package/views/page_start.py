
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QRadioButton, QHBoxLayout, QLineEdit, QFileDialog
from PySide6.QtCore import Qt, Signal

class HomePage(QWidget):
    # Segnale avvio input
    richiesta_start = Signal( str, str)

    def __init__(self):
        super().__init__()
        # Inizializzazione Layout
        layout = QVBoxLayout()
        layout_path_output = QHBoxLayout()

        # Setup Intestazione
        self.label_benvenuto = QLabel("Benvenuto in Image Processing!")
        self.label_benvenuto.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.label_benvenuto.setStyleSheet("font-size: 30px;")

        # Setup Modalità Input
        self.radio_slide = QRadioButton("Input da Slide")
        self.radio_dataset = QRadioButton("Input da Dataset")
        self.radio_slide.setChecked(True)

        # Setup Percorso Output
        self.label_path = QLabel("Selezionare percorso output: ")
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("C:/percorso/outuput...")
        self.btn_sfoglia = QPushButton("Sfoglia")
        self.btn_sfoglia.clicked.connect(lambda: self._scegli_path())

        # Setup bottoni
        btn_start = QPushButton("Start")
        btn_start.clicked.connect(self._decidi_destinazione)

        # Setup layout_path_output
        layout_path_output.addWidget(self.label_path)
        layout_path_output.addWidget(self.output_path)
        layout_path_output.addWidget(self.btn_sfoglia)

        # Setup Layout
        layout.addWidget(self.label_benvenuto)
        layout.addSpacing(50)
        layout.addLayout(layout_path_output)
        layout.addSpacing(50)
        layout.addWidget(self.radio_slide)
        layout.addWidget(self.radio_dataset)
        layout.addWidget(btn_start)
        self.setLayout(layout)

    # Metodo interno per emissione del segnale
    def _decidi_destinazione(self):
        # Caso input da Slide
        if self.radio_slide.isChecked():
            self.richiesta_start.emit("Slide", self.output_path.text())

        # Caso input da Dataset
        else:
            self.richiesta_start.emit("Dataset", self.output_path.text())

    # Metodo per acquisizione output_path
    def _scegli_path(self):
        percorso_file = QFileDialog.getExistingDirectory(self, "Seleziona percorso di salvataggio", "")

        return self.output_path.setText(f"{percorso_file}")
