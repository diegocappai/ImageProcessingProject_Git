from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

from Interface_Package.visualizzatori.visualizzatore_patch import VisualizzatorePatch
from Interface_Package.visualizzatori.visualizzatore_slide import VisualizzatoreSlide


class PageShowSlide(QWidget):
    # Segnale con coordinate doppio-click
    estrai_patch = Signal(int, int)
    # Segnale con etichetta patch
    etichetta = Signal(str)
    # Segnale per richiesta salvataggio
    richiesta_salvataggio = Signal()

    def __init__(self):
        super().__init__()
        self.label_impostazioni = QLabel("Slide Vetrino")
        self.label_impostazioni.setStyleSheet("font-size: 20px;")
        self.label_impostazioni.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # Inizializzazione Layouts
        main_layout = QVBoxLayout()
        image_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()

        # Setup Immagine principale
        #self.label_immagine = QLabel("Caricamento immagine")
        #self.label_immagine.setAlignment(Qt.AlignCenter)
        #self.label_immagine.setStyleSheet("border: 2px dashed gray; background-color: white; color: black; font_size: 16px ")
        #self.label_immagine.setMinimumSize(600, 400)
        self.viewer_slide = VisualizzatoreSlide()
        self.viewer_patch = VisualizzatorePatch()


        # Setup Patch
        self.label_patch = QLabel("Selezionare Patch")
        self.label_patch.setAlignment(Qt.AlignCenter)
        self.label_patch.setStyleSheet("border: 2px dashed gray; background-color: white; color: black; font_size: 16px ")
        self.label_patch.setMinimumSize(400, 400)

        # Setup Bottom
        self.label_info = QLabel("Doppio click su una patch per selezionarla.")
        self.btn_tumor = QPushButton("Tumor")
        self.btn_normal = QPushButton("Normal")
        self.btn_tumor.clicked.connect(lambda: self._richiesta_etichetta("Tumor"))
        self.btn_normal.clicked.connect(lambda: self._richiesta_etichetta("Normal"))
        self.btn_salvadati = QPushButton("Salva ed esci")
        self.btn_salvadati.clicked.connect(self.richiesta_salvataggio)


        # Setup image_layout
        image_layout.addWidget(self.viewer_slide, stretch= 150)
        image_layout.addWidget(self.viewer_patch, stretch= 50)

        # Setup bottom_layout
        bottom_layout.addWidget(self.label_info)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_normal)
        bottom_layout.addWidget(self.btn_tumor)
        bottom_layout.addStretch(30)
        bottom_layout.addWidget(self.btn_salvadati)

        # Setup main_layout
        main_layout.addWidget(self.label_impostazioni)
        main_layout.addLayout(image_layout)
        main_layout.addLayout(bottom_layout)

        # Setup collegamento doppio-click
        self.viewer_slide.seg_doppio_click.connect(self.estrai_patch)


        self.setLayout(main_layout)

    def mostra_patch(self, pixmap):
        self.viewer_patch.mostra_immagine(pixmap)

    # Settaggio thumbnail slide
    def set_thumbnail(self, pixmap: QPixmap, original_w: int, original_h: int, tile_w:int, tile_h:int):
        self.viewer_slide.current_w = tile_w
        self.viewer_slide.current_h = tile_h
        self.viewer_slide.mostra_immagine(pixmap, original_w, original_h)

    def _richiesta_etichetta(self, etichetta):
        #self.viewer_patch.pulisci_visualizzazione() TODO RAGIONARE SU METODO PER TOGLIERE PATCH
        self.etichetta.emit(etichetta)
