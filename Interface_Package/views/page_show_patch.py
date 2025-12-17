from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, Signal
from Interface_Package.visualizzatori.visualizzatore_patch import VisualizzatorePatch


class PageShowPatch(QWidget):
    etichetta = Signal(str)
    richiesta_salvataggio = Signal()

    def __init__(self):
        super().__init__()

        # Setup Intestazione
        self.label_impostazioni = QLabel("Etichettatura")
        self.label_impostazioni.setStyleSheet("font-size: 20px;")
        self.label_impostazioni.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # Inizializzazione Layouts
        main_layout = QVBoxLayout()
        image_layout = QHBoxLayout()
        btn_layout = QVBoxLayout()

        # Inizializzo visualizzatore
        self.viewer = VisualizzatorePatch()

        # Setup bottoni etichettatura
        self.btn_tumor = QPushButton("Tumor")
        self.btn_normal = QPushButton("Normal")
        self.btn_tumor.clicked.connect(lambda: self._richiesta_etichetta("Tumor"))
        self.btn_normal.clicked.connect(lambda: self._richiesta_etichetta("Normal"))
        self.btn_salva = QPushButton("Salva ed esci")
        self.btn_salva.clicked.connect(self.richiesta_salvataggio)

        # Setup btn_layout
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_tumor)
        btn_layout.addWidget(self.btn_normal)
        btn_layout.addSpacing(20)
        btn_layout.addWidget(self.btn_salva)

        # Setup image_layout
        image_layout.addWidget(self.viewer, stretch=5)
        image_layout.addLayout(btn_layout, stretch=1)

        # Setup main_layout
        main_layout.addWidget(self.label_impostazioni)
        main_layout.addLayout(image_layout)

        self.setLayout(main_layout)

    def mostra_patch(self, pixmap):
        self.viewer.mostra_immagine(pixmap)

    def _richiesta_etichetta(self, etichetta):
        self.etichetta.emit(etichetta)
        # self.viewer.pulisci_visualizzazione()
