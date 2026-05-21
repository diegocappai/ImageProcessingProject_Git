from typing import Optional
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                               QLabel, QComboBox, QPushButton,
                               QMessageBox, QGraphicsPixmapItem, QCheckBox,
                               )
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent

from Interface_Package.widgets.roi_graphics_view import RoiGraphicsView
from Utils.ui_settings import CLASSI_DEFAULT
from Interface_Package.widgets.class_selector_view import ClassSelectorWidget


class ImpostazioniSlideDialog(QDialog):
    """
    View per la configurazione dei progetti WSI (Whole Slide Image)
    """
    # ==========================================
    # SEGNALI
    # ==========================================
    vista_cambiata = Signal()
    griglia_toggled = Signal(bool)
    aggiorna_grandezza_patch = Signal(int)
    salva_e_inizia = Signal()
    roi_modificate = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurazione Progetto - Whole Slide Image")
        self.setMinimumWidth(850)
        self.setMinimumHeight(600)

        self.current_hd_tile: Optional[QGraphicsPixmapItem] = None

        self.init_ui()

        # Cablaggio interno dei segnali
        self.roi_view.vista_cambiata.connect(self.vista_cambiata.emit)
        self.roi_view.roi_modificate.connect(self.roi_modificate.emit)
        self.checkbox_griglia.toggled.connect(self.griglia_toggled.emit)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # ==========================================
        # SEZIONE SUPERIORE
        # ==========================================
        top_hlayout = QHBoxLayout()

        # --- PANNELLO SINISTRO (Vista Grafica) ---
        left_vlayout = QVBoxLayout()

        self.roi_view = RoiGraphicsView()
        self.roi_view.setMinimumSize(500, 400)
        self.roi_view.imposta_modalita_disegno(False)

        left_vlayout.addWidget(self.roi_view)
        top_hlayout.addLayout(left_vlayout, stretch=3)

        # --- PANNELLO DESTRO ---
        right_vlayout = QVBoxLayout()
        right_vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        right_vlayout.setContentsMargins(10, 0, 0, 0)

        grandezza_label = QLabel("Grandezza patch:")
        grandezza_label.setProperty("class", "SectionTitle")
        right_vlayout.addWidget(grandezza_label)

        spin_layout = QHBoxLayout()
        spin_layout.setSpacing(5)

        valori_patch = ["128", "256", "512", "1024", "2048", "4096", "8192"]
        self.combo_patch = QComboBox()
        self.combo_patch.addItems(valori_patch)
        self.combo_patch.setCurrentIndex(2) # Default 512 px

        px_label = QLabel("px")
        spin_layout.addWidget(self.combo_patch)
        spin_layout.addWidget(px_label)
        spin_layout.addStretch()
        right_vlayout.addLayout(spin_layout)

        self.combo_patch.currentTextChanged.connect(self.invia_nuova_grandezza)

        self.checkbox_griglia = QCheckBox("Mostra Griglia (Virtuale)")
        self.checkbox_griglia.setChecked(True)
        right_vlayout.addWidget(self.checkbox_griglia)

        right_vlayout.addSpacing(25)

        # Statistiche in tempo reale
        patch_tot_layout = QHBoxLayout()
        patch_tot_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.label_n_patch_tot = QLabel("Numero Patch Totali:\n0")
        self.label_n_patch_tot.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.info_icon = QLabel("i")
        self.info_icon.setFixedSize(16, 16)
        self.info_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_icon.setProperty("class", "InfoBadge")
        self.info_icon.setToolTip("Rappresenta l'intera griglia WSI (incluse patch vuote e sfondo).")

        patch_tot_layout.addWidget(self.label_n_patch_tot)
        patch_tot_layout.addSpacing(5)
        patch_tot_layout.addWidget(self.info_icon)
        patch_tot_layout.addStretch()

        right_vlayout.addLayout(patch_tot_layout)

        right_vlayout.addSpacing(15)

        # SEZIONE ETICHETTE
        etichette_title = QLabel("Composizione Classi:")
        etichette_title.setProperty("class", "SectionTitle")
        right_vlayout.addWidget(etichette_title)

        self.class_selector = ClassSelectorWidget(default_classes=CLASSI_DEFAULT)
        right_vlayout.addWidget(self.class_selector)
        right_vlayout.addStretch()

        top_hlayout.addLayout(right_vlayout, stretch=1)
        content_layout.addLayout(top_hlayout)

        # ==========================================
        # SEZIONE INFERIORE
        # ==========================================
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_annulla = QPushButton("Annulla")
        self.btn_salva = QPushButton("Salva")
        self.btn_salva.setProperty("class", "PrimaryButton")

        self.btn_annulla.clicked.connect(self.reject)
        self.btn_salva.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_annulla)
        btn_layout.addWidget(self.btn_salva)

        content_layout.addLayout(btn_layout)
        main_layout.addLayout(content_layout)

    # ==========================================
    # LOGICA DI PRESENTAZIONE
    # ==========================================
    def invia_nuova_grandezza(self, testo_selezionato: str):
        """Valida e instrada il cambio di combobox verso il Controller per ricalcolare la griglia."""
        if not testo_selezionato:
            return
        try:
            valore_intero = int(testo_selezionato)
            self.aggiorna_grandezza_patch.emit(valore_intero)
        except ValueError:
            pass

    # ==========================================
    # API PUBBLICHE
    # ==========================================

    def aggiorna_griglia_visiva(self, real_patch_size: int, offset_x=0, offset_y=0):
        """
        Transla le dimensioni fisiche del WSI in coordinate schermo per renderizzare correttamente la maglia della griglia
        """
        if hasattr(self, 'orig_w') and self.orig_w > 0 and self.orig_h > 0:
            scala_x = self.thumb_w / self.orig_w
            scala_y = self.thumb_h / self.orig_h

            grid_step_x = real_patch_size * scala_x
            grid_step_y = real_patch_size * scala_y

            self.roi_view.set_grid_step(grid_step_x, grid_step_y, offset_x, offset_y)

            # Forza lo zoom se la spunta della griglia è attiva
            if self.checkbox_griglia.isChecked():
                self.roi_view.set_zoom_grid()

    def set_griglia_visiva(self, visibile: bool):
        self.roi_view.imposta_visibilita_griglia(visibile)

    def aggiorna_totale_patch(self, n):
        self.label_n_patch_tot.setText(f"Numero Patch Totali:\n{n}")

    def get_classi_etichette(self) -> list:
        """
        Delega interamente la raccolta delle classi selezionate al widget
        """
        return self.class_selector.get_selected_classes()

    def get_dimensioni_miniatura(self) -> tuple:
        return self.roi_view.get_dimensioni_scena()

    def get_grandezza_patch(self) -> int:
        return int(self.combo_patch.currentText())

    def closeEvent(self, event: QCloseEvent):
        """Imopedisce la chiusura accidentale tramite la 'X' in alto."""
        box = QMessageBox(self)
        box.setWindowTitle("Conferma Uscita")
        box.setText("Sicuro di voler annullare la creazione?\nI parametri del progetto andranno persi.")
        box.setIcon(QMessageBox.Icon.Warning)

        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.No)

        if box.exec() == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()


