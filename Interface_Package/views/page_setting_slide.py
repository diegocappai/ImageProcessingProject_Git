from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QHBoxLayout, QLineEdit, QComboBox, \
    QRadioButton, QButtonGroup, QGroupBox
from PySide6.QtCore import Qt, Signal
from dataclasses import dataclass


@dataclass
class PageRequestSlide:
    path_slide: str
    tile_w: int
    tile_h: int
    method_show: str
    order_show: str


class PageSettingSlide(QWidget):

    richiesta_back = Signal()
    richiesta_set_grid = Signal(int, int, str)
    richiesta_play = Signal(object)



    def __init__(self):
        super().__init__()

        # Setup Titolo
        self.label_impostazioni = QLabel("Impostazioni Slide")
        self.label_impostazioni.setStyleSheet("font-size: 30px;")
        self.label_impostazioni.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # Setup Input Path
        self.label_dataset = QLabel("Slide: ")
        self.input_percorso = QLineEdit()
        self.input_percorso.setPlaceholderText("C:/percorso/slide...")
        self.btn_sfoglia = QPushButton("Sfoglia")
        self.btn_sfoglia.clicked.connect(lambda: self.scegli_path())


        # Setup Dimensione Patch
        lista_valori = ["128", "256", "512", "1024", "2048", "4098", "8192"]
        self.menu_widht = QComboBox()
        self.menu_widht.addItems(lista_valori)
        self.menu_widht.setEditable(True)
        self.menu_widht.setValidator(QIntValidator(0, 10000))
        self.label_width = QLabel("Larghezza patch:")
        self.menu_height = QComboBox()
        self.menu_height.addItems(lista_valori)
        self.menu_height.setEditable(True)
        self.menu_height.setValidator(QIntValidator(0,10000))
        self.label_height = QLabel("Altezza Patch:")
        self.label_px1 = QLabel("px")
        self.label_px = QLabel("px")

        # Setup Modalità Visualizzazione
        self.label_modalità = QLabel("Seleziona modalità visualizzazione:")
        self.radio_slide = QRadioButton("Slide Intera")
        self.radio_patch = QRadioButton("Patch Singole")
        self.radio_slide.setChecked(True)
        self.gruppo_mod = QButtonGroup(self)
        self.gruppo_mod.addButton(self.radio_slide, 1)
        self.gruppo_mod.addButton(self.radio_patch, 2)

        # Setup Ordine Visualizzazione
        self.grp_ordine = QGroupBox("Ordine visualizzazione:")
        self.sub_seq = QRadioButton("Sequenziale")
        self.sub_rand = QRadioButton("Random")
        self.grp_ordine.setEnabled(False)
        self.radio_patch.toggled.connect(self.gestisci_ordine)


        # Setup Tasti
        self.btn_set = QPushButton("Verifica Griglia")
        self.btn_set.clicked.connect(self.gestisci_set_grid)
        self.btn_start = QPushButton("Inizia Etichettatura")
        self.btn_start.clicked.connect(self._btn_request)
        self.btn_back = QPushButton("Indietro")
        self.btn_back.clicked.connect(self.richiesta_back.emit)


        # Inizializzazione Layouts
        layout_principale = QVBoxLayout()
        layout_path = QHBoxLayout()
        layout_patch = QHBoxLayout()
        layout_modalità = QVBoxLayout()
        layout_ordine = QVBoxLayout()
        layout_bottom = QHBoxLayout()


        # Setup layout_path
        layout_path.setContentsMargins(0, 0, 0, 0)
        layout_path.addWidget(self.label_dataset)
        layout_path.addWidget(self.input_percorso)
        layout_path.addWidget(self.btn_sfoglia)

        # Setup layout_patch
        layout_patch.addWidget(self.label_width)
        layout_patch.addWidget(self.menu_widht)
        layout_patch.addWidget(self.label_px)
        layout_patch.addWidget(self.label_height)
        layout_patch.addWidget(self.menu_height)
        layout_patch.addWidget(self.label_px1)
        layout_patch.addSpacing(20)
        layout_patch.addWidget(self.btn_set)

        # Setup layout_modalità
        layout_modalità.addWidget(self.label_modalità)
        layout_modalità.addWidget(self.radio_slide)
        layout_modalità.addWidget(self.radio_patch)

        # Setup layout_ordine
        layout_ordine.addWidget(self.sub_seq)
        layout_ordine.addWidget(self.sub_rand)
        self.grp_ordine.setLayout(layout_ordine)

        # Setup layout_bottom
        layout_bottom.addWidget(self.btn_back)
        layout_bottom.addStretch()
        layout_bottom.addWidget(self.btn_start)

        # Setup layout_principale
        layout_principale.addWidget(self.label_impostazioni)
        layout_principale.addSpacing(30)
        layout_principale.addLayout(layout_path)
        layout_principale.addSpacing(45)
        layout_principale.addLayout(layout_patch)
        layout_principale.addSpacing(35)
        layout_principale.addLayout(layout_modalità)
        layout_principale.addSpacing(10)
        layout_principale.addWidget(self.grp_ordine)
        layout_principale.addStretch()
        layout_principale.addLayout(layout_bottom)



        self.setLayout(layout_principale)

    def scegli_path(self):
        percorso_file, _ = QFileDialog.getOpenFileName(self, "Seleziona Immagine", "", "Immagini (*.png *.jpg *.jpeg *.tif *.tiff *.svs)")
        return self.input_percorso.setText(percorso_file)


    def grandezza_patch(self):
        w = self.menu_widht.currentText()
        h = self.menu_height.currentText()
        return w,h

    def get_path(self):
        path = self.input_percorso.text()
        clean_path = path.strip().replace('"', '')
        return clean_path

    # Attiva Radio Button Ordine se Mod. Patch
    def gestisci_ordine(self, checked):
        self.grp_ordine.setEnabled(checked)

    def get_order(self):
        if self.sub_seq.isChecked():
            return("sequential")
        elif self.sub_rand.isChecked():
            return("random")

    def gestisci_set_grid(self):
        w,h = self.grandezza_patch()
        input_path = self.get_path()
        self.richiesta_set_grid.emit(int(w),int(h), input_path)

    # Gestisce segnale modalità visualizzazione
    def _btn_request(self):
        id_sel = self.gruppo_mod.checkedId()
        path = self.get_path()
        tile_w = self.grandezza_patch()[0]
        tile_h = self.grandezza_patch()[1]

        if id_sel == 1:
            method_show = "Slide"
            order_show = None



        elif id_sel == 2:
            method_show = "Patch"
            order_show = self.get_order()


        request_data = PageRequestSlide(path, tile_w, tile_h, method_show, order_show)
        self.richiesta_play.emit(request_data)
