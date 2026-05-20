import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QWidget, QFrame, QLabel, QPushButton, QHBoxLayout,
                               QProgressBar, QVBoxLayout, QScrollArea, QSpinBox)


class ProjectDashboardView(QWidget):
    """
    View per la Dashboard di riepilogo del progetto
    """
    # ==========================================
    # SEGNALI
    # ==========================================
    richiesta_inizio_etichettatura = Signal()
    richiesta_ritorno_home = Signal()
    richiesta_cambio_campionamento = Signal(int)

    def __init__(self):
        super().__init__()
        self.setObjectName("Dashboard")
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)

        # --- HEADER ---
        header_layout = QHBoxLayout()
        self.lbl_project_name = QLabel("Nome Progetto")
        self.lbl_project_name.setProperty("class", "HeaderTitle")

        self.btn_back = QPushButton("← Torna alla Home")
        self.btn_back.setObjectName("BtnBack")
        self.btn_back.clicked.connect(self.richiesta_ritorno_home.emit)

        header_layout.addWidget(self.lbl_project_name)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_back)
        main_layout.addLayout(header_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(25)

        # 1. Informazioni Generali
        self.card_info, info_layout = self._crea_card("INFORMAZIONI GENERALI")
        #self.val_tipo = self._add_info_row(info_layout, "Tipo Input:")
        self.val_file = self._add_info_row(info_layout, "File Sorgente:")
        #self.val_patch_size = self._add_info_row(info_layout, "Dimensione Patch:")
        content_layout.addWidget(self.card_info)

        # 2. Statistiche Campionamento
        self.card_stats, stats_layout = self._crea_card("STATISTICHE CAMPIONAMENTO")
        self.val_teoriche = self._add_info_row(stats_layout, "Patch totali:")
        #self.val_roi = self._add_info_row(stats_layout, "Patch nelle ROI:")
        row_perc_layout = QHBoxLayout()
        lbl_perc = QLabel("Percentuale campionamento:")
        lbl_perc.setProperty("class", "InfoLabel")
        self.spin_perc = QSpinBox()
        self.spin_perc.setRange(10, 100)
        self.spin_perc.setSingleStep(10)
        self.spin_perc.setSuffix(" %")
        self.spin_perc.setFixedWidth(120)
        self.spin_perc.setMinimumHeight(38)
        #self.spin_perc.setStyleSheet("background-color: #333; color: white; border: 1px solid #555;")

        self.spin_perc.valueChanged.connect(self.richiesta_cambio_campionamento.emit)

        row_perc_layout.addWidget(lbl_perc)
        row_perc_layout.addStretch()
        row_perc_layout.addWidget(self.spin_perc)
        stats_layout.addLayout(row_perc_layout)

        self.val_sampled = self._add_info_row(stats_layout, "Patch da Etichettare:")
        content_layout.addWidget(self.card_stats)

        # 3. Sezione Progresso
        prog_layout = QVBoxLayout()
        prog_header = QHBoxLayout()

        prog_title = QLabel("Progresso Etichettatura")
        prog_title.setProperty("class", "SectionTitle")

        self.lbl_counter = QLabel("0 / 0")
        self.lbl_counter.setStyleSheet("color: white; font-weight: bold;")

        prog_header.addWidget(prog_title)
        prog_header.addStretch()
        prog_header.addWidget(self.lbl_counter)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        prog_layout.addLayout(prog_header)
        prog_layout.addWidget(self.progress_bar)
        content_layout.addLayout(prog_layout)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # --- ACTION AREA ---
        action_layout = QHBoxLayout()
        action_layout.addStretch()

        self.btn_main_action = QPushButton("Inizia Etichettatura")
        self.btn_main_action.setObjectName("BtnMain")
        self.btn_main_action.clicked.connect(self.richiesta_inizio_etichettatura.emit)

        action_layout.addWidget(self.btn_main_action)
        action_layout.addStretch()
        main_layout.addLayout(action_layout)

    def _crea_card(self, titolo: str):
        """Utility factory per creare card stilizzate in modo omogeneo"""
        card = QFrame()
        card.setProperty("class", "Card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(30, 25, 30, 30)
        layout.setSpacing(15)

        title_lbl = QLabel(titolo)
        title_lbl.setProperty("class", "SectionTitle")
        layout.addWidget(title_lbl)

        linea = QFrame()
        linea.setFrameShape(QFrame.Shape.HLine)
        linea.setStyleSheet("background-color: #333333; margin-bottom: 10px;")
        layout.addWidget(linea)

        return card, layout

    def _add_info_row(self, parent_layout, label_text: str) -> QLabel:
        """Utility per creare righe campo:valore """
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)

        lbl = QLabel(label_text)
        lbl.setProperty("class", "InfoLabel")

        val = QLabel("-")
        val.setProperty("class", "InfoValue")
        val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        row_layout.addWidget(lbl)
        row_layout.addStretch()
        row_layout.addWidget(val)

        parent_layout.addLayout(row_layout)
        return val

    # ==========================================
    # API PUBBLICA
    # ==========================================
    def display_project(self, data: dict):
        """
        Popola la dashboard con estrazione sicura dei dati
        """
        name_project = data.get("case_id", "Progetto senza nome")
        self.lbl_project_name.setText(f"Progetto: {name_project}")

        # Info Generali

        percorso_sorgente = data.get("source_path", "-")
        self.val_file.setText(os.path.basename(percorso_sorgente))

        # 🟢 FIX 1: Protezione su patching_config
        patch_conf = data.get("patching_config")
        patch_conf = patch_conf if isinstance(patch_conf, dict) else {}

        # 🟢 FIX 2: Protezione su progress
        prog = data.get("progress")
        prog = prog if isinstance(prog, dict) else {}
        self.val_teoriche.setText(str(prog.get("total_patches", 0)))

        # Calcoli di presentazione
        patches = data.get("patches", [])
        patches = patches if isinstance(patches, list) else [] # Sicurezza extra

        # 🟢 FIX 3: Protezione su sampling_config
        samp_conf = data.get("sampling_config")
        samp_conf = samp_conf if isinstance(samp_conf, dict) else {}
        percentuale = samp_conf.get("sampling_percentage", 100)
        self.spin_perc.blockSignals(True)
        self.spin_perc.setValue(percentuale)
        self.spin_perc.blockSignals(False)

        tot_campionate = sum(1 for p in patches if isinstance(p, dict) and p.get("is_sampled") is not False)
        self.val_sampled.setText(f"{tot_campionate}")

        # Progresso
        etichettate = prog.get("labeled_patches", 0)
        self.lbl_counter.setText(f"{etichettate} / {tot_campionate}")

        perc_completamento = 0
        if tot_campionate > 0:
            perc_completamento = int((etichettate / tot_campionate) * 100)
            self.progress_bar.setValue(perc_completamento)

        # Logica Testo Bottone Action
        mostrate = prog.get("shown_patches", 0)
        if mostrate == 0:
            self.btn_main_action.setText("Inizia Etichettatura Patch")
        elif perc_completamento == 100:
            self.btn_main_action.setText("Revisiona Patch")
        else:
            self.btn_main_action.setText("Riprendi Etichettatura Patch")