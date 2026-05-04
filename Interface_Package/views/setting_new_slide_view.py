from typing import Optional, Dict
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                               QLabel, QComboBox, QRadioButton, QPushButton,
                               QMessageBox, QGraphicsPixmapItem, QCheckBox)
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QCloseEvent

from Interface_Package.widgets.roi_graphics_view import RoiGraphicsView


class ImpostazioniSlideDialog(QDialog):
    """
    View-Controller per la configurazione dei progetti WSI (Whole Slide Image)
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
        self.setWindowTitle("Digital Pathology Lab - Impostazioni Slide")
        self.setMinimumWidth(750)

        self.current_hd_tile: Optional[QGraphicsPixmapItem] = None

        self.init_ui()

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
        left_vlayout.addWidget(self.roi_view)

        istruzioni_label = QLabel("🖱️ Click Sinistro: Sposta | Click Destro: Disegna ROI | Rotellina: Deep Zoom")
        istruzioni_label.setProperty("class", "InstructionLabel")
        left_vlayout.addWidget(istruzioni_label)

        # Toolbox ROI
        roi_btns_layout = QHBoxLayout()
        self.btn_undo_roi = QPushButton("↩ Annulla ultima ROI")
        self.btn_undo_roi.setProperty("class", "SmallToolButton")
        self.btn_clear_rois = QPushButton("🗑 Cancella tutte")
        self.btn_clear_rois.setProperty("class", "SmallToolButton")

        self.btn_undo_roi.clicked.connect(self.roi_view.undo_last_roi)
        self.btn_clear_rois.clicked.connect(self.roi_view.clear_all_rois)

        roi_btns_layout.addWidget(self.btn_undo_roi)
        roi_btns_layout.addWidget(self.btn_clear_rois)
        roi_btns_layout.addStretch()

        left_vlayout.addLayout(roi_btns_layout)
        top_hlayout.addLayout(left_vlayout, stretch=3)

        # --- PANNELLO DESTRO ---
        right_vlayout = QVBoxLayout()
        right_vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        right_vlayout.setContentsMargins(10, 50, 0, 0)

        grandezza_label = QLabel("Grandezza patch:")
        right_vlayout.addWidget(grandezza_label)

        spin_layout = QHBoxLayout()
        spin_layout.setSpacing(5)

        valori_patch = ["128", "256", "512", "1024", "2048", "4096", "8192"]
        self.combo_patch = QComboBox()
        self.combo_patch.addItems(valori_patch)
        self.combo_patch.setCurrentIndex(2)

        px_label = QLabel("px")
        spin_layout.addWidget(self.combo_patch)
        spin_layout.addWidget(px_label)
        spin_layout.addStretch()
        right_vlayout.addLayout(spin_layout)

        self.combo_patch.currentTextChanged.connect(self.invia_nuova_grandezza)

        self.checkbox_griglia = QCheckBox("Mostra Griglia (Virtuale)")
        self.checkbox_griglia.setChecked(True)
        right_vlayout.addWidget(self.checkbox_griglia)

        right_vlayout.addSpacing(30)

        # Statistiche in tempo reale
        patch_tot_layout = QHBoxLayout()
        patch_tot_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.label_n_patch_tot = QLabel("Numero Patch Totali:\n0")
        self.label_n_patch_tot.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.info_icon = QLabel("i")
        self.info_icon.setFixedSize(16, 16)
        self.info_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_icon.setToolTip("Rappresenta l'intera griglia WSI (incluse patch vuote e sfondo).")
        self.info_icon.setStyleSheet("""
                    QLabel {
                        background-color: #4b8bcf;
                        color: white;
                        border-radius: 8px;
                        font-family: "Times New Roman", serif;
                        font-weight: bold;
                        font-size: 11px;
                    }
                    QLabel:hover { background-color: #5c9cdf; }
                """)

        patch_tot_layout.addWidget(self.label_n_patch_tot)
        patch_tot_layout.addSpacing(5)
        patch_tot_layout.addWidget(self.info_icon)
        patch_tot_layout.addStretch()

        right_vlayout.addLayout(patch_tot_layout)

        self.label_n_patch_roi = QLabel("Patch valide nelle ROI:\n0")
        self.label_n_patch_roi.setProperty("class", "HighlightLabel")
        right_vlayout.addWidget(self.label_n_patch_roi)

        top_hlayout.addLayout(right_vlayout, stretch=1)
        content_layout.addLayout(top_hlayout)

        # ==========================================
        # SEZIONE INFERIORE
        # ==========================================
        perc_layout = QHBoxLayout()
        perc_label = QLabel("Percentuale di campionamento ROI:")

        self.combo_perc = QComboBox()
        self.combo_perc.addItems([f"{i}%" for i in range(10, 101, 10)])
        self.combo_perc.setCurrentText("30%")

        perc_layout.addWidget(perc_label)
        perc_layout.addWidget(self.combo_perc)
        perc_layout.addStretch()
        content_layout.addLayout(perc_layout)

        order_label = QLabel("Strategia di visualizzazione per l'etichettatura:")
        content_layout.addWidget(order_label)

        self.radio_seq = QRadioButton("Sequenziale")
        self.radio_seq.setChecked(True)
        self.radio_rand = QRadioButton("Random")

        content_layout.addWidget(self.radio_seq)
        content_layout.addWidget(self.radio_rand)

        # Action Area
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
        """Valida e instrada il cambio di combobox verso il Controller."""
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
    def imposta_immagine_anteprima(self, pixmap_pronto, orig_w: int, orig_h: int):
        """Carica il thumbnail di base per la navigazione fluida"""
        if not pixmap_pronto.isNull():
            self.orig_w = orig_w
            self.orig_h = orig_h
            self.thumb_w = pixmap_pronto.width()
            self.thumb_h = pixmap_pronto.height()

            self.roi_view.scene.clear()
            self.roi_view.roi_items.clear()

            sfondo_item = QGraphicsPixmapItem(pixmap_pronto)
            sfondo_item.setZValue(-1)
            self.roi_view.scene.addItem(sfondo_item)

            self.roi_view.setSceneRect(0, 0, pixmap_pronto.width(), pixmap_pronto.height())
            self.roi_view.fitInView(self.roi_view.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        else:
            print("[DEBUG - ERROR] View: Ricevuto QPixmap nullo o corrotto.")

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

    def set_griglia_visiva(self, visibile: bool):
        self.roi_view.imposta_visibilita_griglia(visibile)

    def aggiorna_layer_alta_risoluzione(self, pixmap_alta_ris, rect_visibile: QRectF):
        """
        Gestisce la memoria della Deep Zoom Pyramid
        """
        # Garbage Collection proattiva: prevenzione di memory leak (RAM bloat)
        if hasattr(self, 'current_hd_tile') and self.current_hd_tile:
            self.roi_view.scene.removeItem(self.current_hd_tile)
            self.current_hd_tile = None

        if pixmap_alta_ris is None or pixmap_alta_ris.isNull():
            return

        self.current_hd_tile = QGraphicsPixmapItem(pixmap_alta_ris)
        self.current_hd_tile.setPos(rect_visibile.topLeft())

        scala_x = rect_visibile.width() / pixmap_alta_ris.width()
        scala_y = rect_visibile.height() / pixmap_alta_ris.height()

        from PySide6.QtGui import QTransform
        self.current_hd_tile.setTransform(QTransform().scale(scala_x, scala_y))
        self.current_hd_tile.setZValue(-0.5)
        self.roi_view.scene.addItem(self.current_hd_tile)

    def aggiorna_totale_patch(self, n):
        self.label_n_patch_tot.setText(f"Numero Patch Totali:\n{n}")

    def aggiorna_conteggio_roi(self, n):
        self.label_n_patch_roi.setText(f"Patch valide nelle ROI:\n{n}")

    def get_dimensioni_miniatura(self) -> tuple:
        return self.roi_view.get_dimensioni_scena()

    def get_grandezza_patch(self) -> int:
        return int(self.combo_patch.currentText())

    def get_roi_rects(self) -> list:
        return self.roi_view.get_roi_rects()

    def get_area_visibile_pura(self) -> Optional[Dict[str, float]]:
        return self.roi_view.get_area_visibile_pura()

    def get_perc_sampling(self) -> str:
        return self.combo_perc.currentText()

    def get_sampling_order(self) -> str:
        return "Sequenziale" if self.radio_seq.isChecked() else "Random"

    def closeEvent(self, event: QCloseEvent):
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


