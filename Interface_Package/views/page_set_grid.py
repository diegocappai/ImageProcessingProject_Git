from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                               QHBoxLayout, QLabel, QSpinBox, QPushButton)
from PySide6.QtGui import QPixmap
from Interface_Package.visualizzatori.visualizzatore_grid import VisualizzatoreGriglia


class PageSetGrid(QWidget):
    """
    La View completa da inserire nello stack.
    Contiene i controlli (SpinBox) e l'area di visualizzazione.
    """

    richiesta_size = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Inizializzazione Layouts
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        layout_central = QHBoxLayout()


        # Intestazione
        lbl_int = QLabel("Impostare grandezza Patch")
        lbl_int.setStyleSheet("font-size:14px;")


        # 1. Barra degli strumenti (Controls)
        self.toolbar_layout = QVBoxLayout()
        self.toolbar_layout.setContentsMargins(10, 10, 10, 0)

        lbl_width = QLabel("Larghezza Patch:")
        self.spin_grid_width = QSpinBox()
        self.spin_grid_width.setRange(10, 100000)  # Min 10px, Max 500px
        #self.spin_grid_width.setValue(512)  # Default
        self.spin_grid_width.setSingleStep(50)

        lbl_height = QLabel("Altezza Patch:")
        self.spin_grid_height = QSpinBox()
        self.spin_grid_height.setRange(10, 100000)  # Min 10px, Max 500px
        #self.spin_grid_height.setValue(512)  # Default
        self.spin_grid_height.setSingleStep(50)


        self.btn_set = QPushButton("Imposta valori")
        self.btn_set.clicked.connect(self.set_final_size)

        self.lbl_size = QLabel("Totale celle: ")

        self.toolbar_layout.addWidget(lbl_width)
        self.toolbar_layout.addWidget(self.spin_grid_width)
        self.toolbar_layout.addSpacing(20)
        self.toolbar_layout.addWidget(lbl_height)
        self.toolbar_layout.addWidget(self.spin_grid_height)
        self.toolbar_layout.addSpacing(50)
        self.toolbar_layout.addWidget(self.lbl_size)
        self.toolbar_layout.addStretch()  # Spinge tutto a sinistra
        self.toolbar_layout.addWidget(self.btn_set)
        self.toolbar_layout.addSpacing(20)



        # 2. Il Visualizzatore
        self.visualizzatore = VisualizzatoreGriglia()

        # 3. Assemblaggio layout

        layout_central.addWidget(self.visualizzatore)
        layout_central.addLayout(self.toolbar_layout)
        main_layout.addWidget(lbl_int)
        main_layout.addLayout(layout_central)

        # 4. Collegamenti Interni (View Logic)
        # Quando l'utente cambia lo spinbox, aggiorniamo il visualizzatore
        self.spin_grid_width.valueChanged.connect(self.visualizzatore.set_grid_w)
        self.spin_grid_height.valueChanged.connect(self.visualizzatore.set_grid_h)

    def set_thumbnail(self, pixmap: QPixmap, original_w: int, original_h: int):
        """
        API pubblica per il Controller.
        Chiama questo metodo quando il Model ha una nuova thumbnail pronta.
        """
        self.visualizzatore.mostra_immagine(pixmap, original_w, original_h)

    def set_initial_size(self, w, h):
        self.spin_grid_width.setValue(w)
        self.spin_grid_height.setValue(h)

    def set_final_size(self):
        w = str(self.spin_grid_width.value())
        h = str(self.spin_grid_height.value())
        self.richiesta_size.emit(w, h)

    def set_info(self, num_patch):
        self.lbl_size.setText(f"Totale celle: {num_patch}")


