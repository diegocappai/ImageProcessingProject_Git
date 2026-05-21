from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtWidgets import (QWidget, QLabel, QPushButton, QHBoxLayout,
                               QProgressBar, QVBoxLayout, QTableWidget, QTableWidgetItem,
                               QHeaderView, QComboBox, QCheckBox, QSplitter, QSpinBox,
                               QGraphicsRectItem, QDialog, QRadioButton, QGraphicsItem,
                               QGraphicsSimpleTextItem, QMenu)
from PySide6.QtGui import QColor, QBrush, QPen, QFont, QPainterPath, QAction

from Interface_Package.widgets.roi_graphics_view import RoiGraphicsView


class NewProjectDashboardView(QWidget):
    """
    View della Dashboard per le WSI (Whole Slide Image)
    """

    # ==========================================
    # SEGNALI
    # ==========================================
    richiesta_inizio_etichettatura = Signal(list)
    richiesta_ritorno_home = Signal()
    cambio_percentuale_roi = Signal(str, int)
    nuova_roi_disegnata = Signal(list)
    stato_roi_modificato = Signal(str, bool)
    richiesta_campionamento_mirato = Signal(QRectF)
    richiesta_eliminazione_roi = Signal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("Dashboard")

        self.roi_graphics_items = {}
        self.patch_graphics_items = []

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # --- HEADER ---
        header_layout = QHBoxLayout()
        self.lbl_project_name = QLabel("Nome Progetto")
        self.lbl_project_name.setProperty("class","HeaderTitle")

        self.btn_back = QPushButton("← Torna alla Home")
        self.btn_back.setObjectName("BtnBack")
        self.btn_back.clicked.connect(self.richiesta_ritorno_home.emit)

        header_layout.addWidget(self.lbl_project_name)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_back)
        main_layout.addLayout(header_layout)

        # --- CORPO PRINCIPALE ---
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # PANNELLO SINISTRO: LA MINIMAPPA
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 10, 10, 0)

        map_title = QLabel("Panoramica Slide e Etichette")
        map_title.setProperty("class", "SectionTitle")
        left_layout.addWidget(map_title)

        # Integriamo la View per la Minimappa
        self.minimap_view = RoiGraphicsView()
        self.minimap_view.imposta_visibilita_griglia(False)
        self.minimap_view.selezione_area.connect(self.richiesta_campionamento_mirato.emit)
        self.minimap_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.minimap_view.customContextMenuRequested.connect(self._mostra_menu_roi)
        left_layout.addWidget(self.minimap_view, stretch=1)

        # Checkbox per visualizzare palette patch
        self.cb_mostra_colori = QCheckBox("Mostra etichette assegnate")
        self.cb_mostra_colori.setChecked(True)
        self.cb_mostra_colori.toggled.connect(self._toggle_colori_patch)
        left_layout.addWidget(self.cb_mostra_colori)

        # Barra della Legenda Colori
        self.layout_legenda = QHBoxLayout()
        left_layout.addLayout(self.layout_legenda)

        splitter.addWidget(left_panel)

        # PANNELLO DESTRO: TABELLA E DATI
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 0, 0)
        right_layout.setSpacing(35)

        # Tabella ROI
        roi_title = QLabel("Gestione ROI")
        roi_title.setProperty("class", "SectionTitle")
        right_layout.addWidget(roi_title)

        self.table_rois = QTableWidget()
        self.table_rois.setColumnCount(7)
        self.table_rois.setHorizontalHeaderLabels(["Sel.", "ID ROI", "Patch\nTotali", "Progresso Etich.\n(Tot)", "Camp.\n(%)", "Visual. /\nCamp.", "Progresso Etich.\n(Camp.)"])
        full_titles = [
            "ROI selezionate",
            "Identicativo ROI",
            "Patch totali della ROI",
            "Progresso etichettatura totale ROI",
            "Percentuale campionamento ROI",
            "Visualizzate/Campionate",
            "Progresso etichettatura campione ROI"
        ]

        for col, testo in enumerate(full_titles):
            item_header = self.table_rois.horizontalHeaderItem(col)
            if item_header:
                item_header.setToolTip(testo)

        self.table_rois.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_rois.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table_rois.verticalHeader().setVisible(False)
        self.table_rois.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        right_layout.addWidget(self.table_rois, stretch=2)

        # Progresso Globale
        prog_header = QHBoxLayout()
        prog_header.addWidget(QLabel("Progresso totale patch campionate:"))
        self.lbl_counter = QLabel("0 / 0")
        prog_header.addStretch()
        prog_header.addWidget(self.lbl_counter)
        right_layout.addLayout(prog_header)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        right_layout.addWidget(self.progress_bar)

        # Azioni
        action_layout = QHBoxLayout()

        self.btn_main_action = QPushButton("Etichetta")
        self.btn_main_action.setProperty("class", "PrimaryButton")
        self.btn_main_action.clicked.connect(self._invia_richiesta_etichettatura)

        action_layout.addStretch()
        action_layout.addWidget(self.btn_main_action)
        right_layout.addLayout(action_layout)

        splitter.addWidget(right_panel)

        splitter.setSizes([600, 400])
        main_layout.addWidget(splitter)

        self.minimap_view.roi_modificate.connect(self._gestisci_new_roi)

    # ==========================================
    # LOGICA DI RENDERING GRAFICO
    # ==========================================

    def disegna_mappa_annotazioni(self, data: dict):
        """Assegna un colore fisso per classe e disegna le patch annotate"""
        for item in self.patch_graphics_items:
            if item.scene():
                item.scene().removeItem(item)
        self.patch_graphics_items.clear()

        color_map_ui = data.get("color_map_generata", {})
        classi_progetto = data.get("labeling_config", {}).get("classes", [])
        self.color_map = color_map_ui

        patches = data.get("patches", [])
        mostra_colori = self.cb_mostra_colori.isChecked()

        percorsi_per_classe = {nome: QPainterPath() for nome in self.color_map.keys()}
        percorso_sconosciuti = QPainterPath()

        for p in patches:
            label = p.get("label")
            if label:
                w = p.get("width", p.get("w", 0))
                h = p.get("height", p.get("h", 0))
                rect = QRectF(p["x"], p["y"], w, h)

                if label in percorsi_per_classe:
                    percorsi_per_classe[label].addRect(rect)
                else:
                    percorso_sconosciuti.addRect(rect)

        for label, path in percorsi_per_classe.items():
            if not path.isEmpty():
                valore_colore = color_map_ui.get(label, "#FFFFFF")

                if isinstance(valore_colore, QColor):
                    colore = QColor(valore_colore.name())
                else:
                    colore = QColor(valore_colore)

                colore.setAlpha(60)

                path_item = self.minimap_view.scene.addPath(path, QPen(Qt.PenStyle.NoPen), QBrush(colore))
                path_item.setZValue(1)
                path_item.setVisible(mostra_colori)
                self.patch_graphics_items.append(path_item)

        if not percorso_sconosciuti.isEmpty():
            colore_scorta = QColor(100, 100, 100, 70)
            path_item = self.minimap_view.scene.addPath(percorso_sconosciuti, QPen(Qt.PenStyle.NoPen),
                                                        QBrush(colore_scorta))
            path_item.setZValue(1)
            path_item.setVisible(mostra_colori)
            self.patch_graphics_items.append(path_item)

        self._aggiorna_legenda(classi_progetto)

    def _aggiorna_legenda(self, etichette: list):
        """Crea la legenda dinamica sotto la mappa"""
        while self.layout_legenda.count():
            item = self.layout_legenda.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.layout_legenda.addWidget(QLabel("Legenda:"))
        for label in etichette:
            hex_color = self.color_map.get(label, "#FFFFFF")

            if isinstance(hex_color, QColor):
                colore = QColor(hex_color.name())
            else:
                colore = QColor(hex_color)

            lbl_color = QLabel("■ " + label)
            lbl_color.setStyleSheet(
                f"color: rgba({colore.red()}, {colore.green()}, {colore.blue()}, 255); font-weight: bold;")
            self.layout_legenda.addWidget(lbl_color)
        self.layout_legenda.addStretch()

    def _toggle_colori_patch(self, is_visible: bool):
        for item in self.patch_graphics_items:
            item.setVisible(is_visible)

    def _mostra_menu_roi(self, pos):
        """Intercetta il tasto destro sulla minimappa e rileva se siamo sopra una ROI"""

        scene_pos = self.minimap_view.mapToScene(pos)
        item = self.minimap_view.scene.itemAt(scene_pos, self.minimap_view.transform())

        if not item:
            return

        if isinstance(item, QGraphicsSimpleTextItem) and item.parentItem():
            item = item.parentItem()

        if not isinstance(item, QGraphicsRectItem):
            return

        roi_id_cliccato = None
        for rid, (rect_item, _) in self.roi_graphics_items.items():
            if rect_item == item:
                roi_id_cliccato = rid
                break

        if not roi_id_cliccato:
            return

        menu = QMenu(self)
        menu.setObjectName("MenuElimina")

        azione_elimina = QAction("❌ Elimina ROI", self)
        azione_elimina.triggered.connect(lambda: self.richiesta_eliminazione_roi.emit(roi_id_cliccato))
        menu.addAction(azione_elimina)

        menu.exec(self.minimap_view.mapToGlobal(pos))

    # ==========================================
    # API PUBBLICHE E INTERAZIONE
    # ==========================================
    def _invia_richiesta_etichettatura(self):
        roi_selezionate = []
        for row in range(self.table_rois.rowCount()):
            cb = self.table_rois.cellWidget(row, 0).layout().itemAt(0).widget()
            if cb.isChecked():
                roi_selezionate.append(self.table_rois.item(row, 1).text())
        self.richiesta_inizio_etichettatura.emit(roi_selezionate)

    def _invia_nuove_roi(self):
        """Invia le nuove ROI disegnate al Controller per aggiungerle al JSON"""
        rects = self.minimap_view.get_roi_rects()
        self.nuova_roi_disegnata.emit(rects)

    def display_project(self, data: dict):
        """Popola UI, Tabella e Minimappa"""
        self.lbl_project_name.setText(f"Progetto: {data.get('case_id', 'Unnamed')}")

        roi_list = data.get("sampling_config", {}).get("roi_list", [])
        self.table_rois.setRowCount(len(roi_list))

        # Pulizia Scena
        for roi_rect, text_item in self.roi_graphics_items.values():
            if roi_rect.scene():
                roi_rect.scene().removeItem(roi_rect)
        self.roi_graphics_items.clear()

        tot_etich, tot_camp = 0, 0
        rects_bloccati = []

        def crea_cella_readonly(testo, allineamento=Qt.AlignmentFlag.AlignCenter):
            item = QTableWidgetItem(str(testo))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(allineamento)
            return item


        for row, roi in enumerate(roi_list):
            roi_id = roi.get("id", f"ROI_{row + 1}")
            stats = roi.get("stats", {"sampled": 0, "labeled": 0,"shown_to_user": 0, "total_valid": 0})

            sampled = stats.get("sampled", 0)
            labeled = stats.get("labeled", 0)
            shown_to_user = stats.get("shown_to_user", 0)
            total_valid = stats.get("total_valid", 0)

            tot_etich += labeled
            tot_camp += sampled

            is_active = roi.get("is_active", True)
            perc_camp = int((labeled / sampled) * 100) if sampled > 0 else 0
            perc_tot = int((labeled / total_valid) * 100) if total_valid > 0 else 0

            # --- COMPONENTI INTERATTIVI ---
            cb_container = QWidget()
            cb_layout = QHBoxLayout(cb_container)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            cb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cb = QCheckBox()
            cb.setChecked(is_active)
            cb_layout.addWidget(cb)
            cb.toggled.connect(lambda checked, rid=roi_id: self._on_roi_toggled(rid, checked))

            spin = QSpinBox()
            spin.setRange(0, 100)
            spin.setSingleStep(10)
            spin.setSuffix("%")
            spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
            valore = int(f"{roi.get('sampling_percentage', 100)}")
            spin.setValue(valore)

            def salva_spinbox(rid=roi_id, s=spin, val_iniziale=valore):
                try:
                    nuovo_valore = s.value()
                    if nuovo_valore != val_iniziale:
                        self.cambio_percentuale_roi.emit(rid, nuovo_valore)
                except RuntimeError:
                    pass

            spin.editingFinished.connect(salva_spinbox)

            w_roi = roi.get("width", roi.get("w", 0))
            h_roi = roi.get("height", roi.get("h", 0))

            if "x" in roi and "y" in roi and w_roi > 0 and h_roi > 0:
                rects_bloccati.append(QRectF(roi["x"], roi["y"], w_roi, h_roi))

                roi_rect = QGraphicsRectItem(0, 0, w_roi, h_roi)
                roi_rect.setPos(roi["x"], roi["y"])

                colore = Qt.GlobalColor.red if is_active else Qt.GlobalColor.gray
                spessore = 4 if is_active else 2
                z_value = 2 if is_active else 1

                pen = QPen(colore, spessore)
                pen.setCosmetic(True)
                roi_rect.setPen(pen)
                roi_rect.setZValue(z_value)
                roi_rect.setToolTip(f"{roi_id}")


                roi_rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape)

                testo_formattato = f" {roi_id}"
                text_item = QGraphicsSimpleTextItem(testo_formattato, roi_rect)
                text_item.setBrush(QBrush(colore))

                text_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)

                text_item.setFont(QFont("Arial", 12, QFont.Weight.Bold))

                text_item.setPos(0, 0)

                self.minimap_view.scene.addItem(roi_rect)
                self.roi_graphics_items[roi_id] = (roi_rect, text_item)
            # --- POPOLAMENTO TABELLA ---
            self.table_rois.setCellWidget(row, 0, cb_container)
            self.table_rois.setItem(row, 1, crea_cella_readonly(roi_id))
            self.table_rois.setItem(row, 2, crea_cella_readonly(total_valid))

            # Progresso Totale ROI
            bar_tot_roi = QProgressBar()
            bar_tot_roi.setRange(0, 100)
            bar_tot_roi.setValue(perc_tot)
            bar_tot_roi.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_rois.setCellWidget(row, 3, bar_tot_roi)
            self.table_rois.setCellWidget(row, 4, spin)
            self.table_rois.setItem(row, 5, crea_cella_readonly(f"{shown_to_user} / {sampled}"))

            # Progresso Campionamento
            bar_camp = QProgressBar()
            bar_camp.setRange(0, 100)
            bar_camp.setValue(perc_camp)
            bar_camp.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_rois.setCellWidget(row, 6, bar_camp)

        self.minimap_view.imposta_roi_bloccate(rects_bloccati)
        self.disegna_mappa_annotazioni(data)

        self.lbl_counter.setText(f"{tot_etich} / {tot_camp}")
        self.progress_bar.setValue(int((tot_etich / tot_camp) * 100) if tot_camp > 0 else 0)

    def _on_roi_toggled(self, roi_id: str, is_active: bool):
        """Cambia colore alla ROI se è attiva o non è attiva"""
        if roi_id in self.roi_graphics_items:
            roi_rect, text_item = self.roi_graphics_items[roi_id]

            if is_active:
                colore = Qt.GlobalColor.red
                spessore = 4
                z_value = 2
            else:
                colore = Qt.GlobalColor.gray
                spessore = 2
                z_value = 0

            pen = QPen(colore, spessore)
            pen.setCosmetic(True)
            roi_rect.setPen(pen)
            roi_rect.setZValue(z_value)

            text_item.setBrush(QBrush(colore))
            self.stato_roi_modificato.emit(roi_id, is_active)

    def _gestisci_new_roi(self):
        """Si attiva appena l'utente rilascia il tasto destro dopo aver tracciato la ROI"""
        rects = self.minimap_view.get_roi_rects()
        if not rects:
            return

        self.nuova_roi_disegnata.emit([rects[-1]])


class NewRoiDialog(QDialog):
    """Dialog che appare dopo il disegno di una nuova ROI per chiederne i parametri"""

    def __init__(self, roi_id: str, patch_valide_stimate: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configura Nuova ROI")
        self.setFixedSize(350, 180)
        self.setModal(True)

        self.percentuale_scelta = 100

        layout = QVBoxLayout(self)

        lbl_info = QLabel(
            f"<b>Hai disegnato {roi_id}</b><br>Contiene circa <b>{patch_valide_stimate}</b> patch valide (tessuto).")
        layout.addWidget(lbl_info)

        layout_perc = QHBoxLayout()
        layout_perc.addWidget(QLabel("Campionamento:"))
        self.combo_perc = QComboBox()
        self.combo_perc.addItems([f"{i}%" for i in range(10, 101, 10)])
        self.combo_perc.setCurrentText("50%")
        layout_perc.addWidget(self.combo_perc)
        layout.addLayout(layout_perc)

        layout_ordine = QHBoxLayout()
        layout_ordine.addWidget(QLabel("Ordine:"))
        self.radio_seq = QRadioButton("Sequenziale")
        self.radio_seq.setChecked(True)
        self.radio_rand = QRadioButton("Random")
        layout_ordine.addWidget(self.radio_seq)
        layout_ordine.addWidget(self.radio_rand)
        layout.addLayout(layout_ordine)

        layout_btn = QHBoxLayout()
        btn_annulla = QPushButton("Annulla")

        btn_salva = QPushButton("Salva ROI")
        btn_salva.setProperty("class", "PrimaryButton")

        btn_annulla.clicked.connect(self.reject)
        btn_salva.clicked.connect(self.accept)

        layout_btn.addStretch()
        layout_btn.addWidget(btn_annulla)
        layout_btn.addWidget(btn_salva)
        layout.addLayout(layout_btn)

    def get_dati(self):
        perc = int(self.combo_perc.currentText().replace("%", ""))
        ordine = "sequential" if self.radio_seq.isChecked() else "random"
        return perc, ordine