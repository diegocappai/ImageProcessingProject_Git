from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QHBoxLayout, QLineEdit, QRadioButton,QGroupBox
from PySide6.QtCore import Qt, Signal
from dataclasses import dataclass


@dataclass
class PageRequestDataset:
    path_directory: str
    order_show: str


class PageSettingDataset(QWidget):

    richiesta_back = Signal()
    richiesta_play = Signal(object)

    def __init__(self):
        super().__init__()

        # Setup Intestazione
        self.label_impostazioni = QLabel("Impostazioni Dataset")
        self.label_impostazioni.setStyleSheet("font-size: 30px;")
        self.label_impostazioni.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # Setup Path
        self.label_dataset = QLabel("Dataset: ")
        self.input_percorso = QLineEdit()
        self.input_percorso.setPlaceholderText("C:/percorso/dataset...")
        self.btn_sfoglia = QPushButton("Sfoglia")
        self.btn_sfoglia.clicked.connect(lambda: self._scegli_path())

        # Setup Bottoni
        self.btn_start = QPushButton("Inizia Etichettatura")
        self.btn_start.clicked.connect(self._btn_request)
        self.btn_back = QPushButton("Indietro")
        self.btn_back.clicked.connect(self.richiesta_back.emit)

        # Setup Ordine Visualizzazione
        self.grp_ordine = QGroupBox("Ordine visualizzazione:")
        self.sub_seq = QRadioButton("Sequenziale")
        self.sub_rand = QRadioButton("Random")
        self.sub_seq.setChecked(True)


        # Inizializzazione Layouts
        #widget_centrale = QWidget()
        layout_principale = QVBoxLayout()
        layout_path = QHBoxLayout()
        layout_bottom = QHBoxLayout()
        layout_ord = QVBoxLayout()

        # Setup layout_path
        layout_path.addWidget(self.label_dataset)
        layout_path.addWidget(self.input_percorso)
        layout_path.addWidget(self.btn_sfoglia)
        layout_path.setContentsMargins(0, 0, 0, 0)

        # Setup layout_bottom
        layout_bottom.addWidget(self.btn_back)
        layout_bottom.addStretch()
        layout_bottom.addWidget(self.btn_start)

        # Setup layout_ord
        layout_ord.addWidget(self.sub_seq)
        layout_ord.addWidget(self.sub_rand)
        self.grp_ordine.setLayout(layout_ord)

        # Setup layout_principale
        layout_principale.addWidget(self.label_impostazioni)
        layout_principale.addSpacing(50)
        layout_principale.addLayout(layout_path)
        layout_principale.addSpacing(50)
        layout_principale.addWidget(self.grp_ordine)
        layout_principale.addStretch()
        #widget_centrale.setLayout(layout_principale)
        layout_principale.addLayout(layout_bottom)


        self.setLayout(layout_principale)

    def _scegli_path(self):
        # Per cartella:
        percorso_file = QFileDialog.getExistingDirectory(self, "Seleziona Dataset", "")
        return self.input_percorso.setText(f"{percorso_file}")

    def _get_path(self):
        path = self.input_percorso.text()
        clean_path = path.strip().replace('"', '')
        return clean_path

    def _get_order(self):
        if self.sub_seq.isChecked():
            return("sequential")
        elif self.sub_rand.isChecked():
            return("random")

    def _btn_request(self):
        path = self._get_path()
        order = self._get_order()

        request_data = PageRequestDataset(path, order)

        self.richiesta_play.emit(request_data)
