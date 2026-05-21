import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QWidget, QFrame, QLabel, QPushButton, QHBoxLayout,
                               QProgressBar, QVBoxLayout, QScrollArea, QSpinBox)


class ProjectDashboardView(QWidget):
    """
    View per la Dashboard di riepilogo per i progetti basati su Dataset (Cartelle di immagini).
    Mostra le statistiche globali, permette di cambiare il campionamento e funge da
    trampolino di lancio per la schermata di etichettatura.
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
        self.btn_back.setProperty("class", "NavButton")
        self.btn_back.clicked.connect(self.richiesta_ritorno_home.emit)

        header_layout.addWidget(self.lbl_project_name)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_back)
        main_layout.addLayout(header_layout)

        # --- SCROLL AREA CENTRALE ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(25)

        # Card: Informazioni Generali
        self.card_info, info_layout = self._crea_card("INFORMAZIONI GENERALI")
        self.val_file = self._add_info_row(info_layout, "Cartella Sorgente:")
        content_layout.addWidget(self.card_info)

        # Card: Statistiche Campionamento
        self.card_stats, stats_layout = self._crea_card("STATISTICHE CAMPIONAMENTO")
        self.val_teoriche = self._add_info_row(stats_layout, "Immagini totali trovate:")

        # Riga custom per lo SpinBox della Percentuale
        row_perc_layout = QHBoxLayout()
        lbl_perc = QLabel("Percentuale da etichettare:")
        lbl_perc.setProperty("class", "InfoLabel")

        self.spin_perc = QSpinBox()
        self.spin_perc.setRange(0, 100)
        self.spin_perc.setSingleStep(10)
        self.spin_perc.setSuffix(" %")
        self.spin_perc.setFixedWidth(120)
        self.spin_perc.setMinimumHeight(38)
        self.spin_perc.editingFinished.connect(lambda: self.richiesta_cambio_campionamento.emit(self.spin_perc.value()))

        row_perc_layout.addWidget(lbl_perc)
        row_perc_layout.addStretch()
        row_perc_layout.addWidget(self.spin_perc)
        stats_layout.addLayout(row_perc_layout)

        self.val_sampled = self._add_info_row(stats_layout, "Patch da Etichettare:")
        content_layout.addWidget(self.card_stats)

        # Sezione Progresso
        prog_layout = QVBoxLayout()
        prog_header = QHBoxLayout()

        prog_title = QLabel("Progresso Etichettatura")
        prog_title.setProperty("class", "SectionTitle")

        self.lbl_counter = QLabel("0 / 0")
        self.lbl_counter.setProperty("class", "CounterLabel")

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

        # --- ACTION AREA (Bottone in basso) ---
        action_layout = QHBoxLayout()
        action_layout.addStretch()

        self.btn_main_action = QPushButton("Inizia Etichettatura")
        self.btn_main_action.setProperty("class", "PrimaryButton")
        self.btn_main_action.setMinimumWidth(250)
        self.btn_main_action.setMinimumHeight(45)
        self.btn_main_action.clicked.connect(self.richiesta_inizio_etichettatura.emit)

        action_layout.addWidget(self.btn_main_action)
        action_layout.addStretch()
        main_layout.addLayout(action_layout)

    def _crea_card(self, titolo: str):
        """
        Utility factory per creare i pannelli che conterranno le righe di informazioni.
        """
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
        linea.setStyleSheet("background-color: #555555; margin-bottom: 10px;")
        layout.addWidget(linea)

        return card, layout

    def _add_info_row(self, parent_layout, label_text: str) -> QLabel:
        """Utility per impaginare perfettamente la coppia 'Titolo : Valore'."""
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
    # API PUBBLICA (Aggiornamento Dati dal Controller)
    # ==========================================
    def display_project(self, data: dict):
        """
        Inietta i dati del JSON nell'interfaccia.
        Contiene protezioni per non far crashare l'app se mancano chiavi.
        """
        name_project = data.get("case_id", "Progetto senza nome")
        self.lbl_project_name.setText(f"Progetto: {name_project}")

        # Info Generali
        percorso_sorgente = data.get("source_path", "-")
        self.val_file.setText(os.path.basename(percorso_sorgente))

        # Protezione su progress
        prog = data.get("progress")
        prog = prog if isinstance(prog, dict) else {}
        self.val_teoriche.setText(str(prog.get("total_patches", 0)))

        # Calcoli di presentazione
        patches = data.get("patches", [])
        patches = patches if isinstance(patches, list) else []

        # Protezione su sampling_config
        samp_conf = data.get("sampling_config")
        samp_conf = samp_conf if isinstance(samp_conf, dict) else {}
        percentuale = samp_conf.get("sampling_percentage", 100)

        # Blocco i segnali per evitare loop infiniti tra View e Controller quando forzo il valore
        self.spin_perc.blockSignals(True)
        self.spin_perc.setValue(percentuale)
        self.spin_perc.blockSignals(False)

        tot_campionate = sum(1 for p in patches if isinstance(p, dict) and p.get("is_sampled") is not False)
        self.val_sampled.setText(f"{tot_campionate}")

        # Progresso Lavori
        etichettate = prog.get("labeled_patches", 0)
        self.lbl_counter.setText(f"{etichettate} / {tot_campionate}")

        perc_completamento = 0
        if tot_campionate > 0:
            perc_completamento = int((etichettate / tot_campionate) * 100)
            self.progress_bar.setValue(perc_completamento)

        # Logica Testo Bottone Action (Cambia in base allo stato del lavoro)
        mostrate = prog.get("shown_patches", 0)
        if mostrate == 0:
            self.btn_main_action.setText("Inizia Etichettatura Dataset")
        elif perc_completamento == 100:
            self.btn_main_action.setText("Revisiona Immagini")
        else:
            self.btn_main_action.setText("Riprendi Etichettatura")