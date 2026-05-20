from typing import Optional
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QMessageBox,
                               QLabel, QPushButton, QTextEdit, QRadioButton, QButtonGroup,
                               QCheckBox, QFrame, QScrollArea, QGridLayout, QComboBox)
from PySide6.QtGui import QPixmap, QShortcut, QKeySequence
from PySide6.QtCore import Qt, Signal
from Interface_Package.visualizzatori.visualizzatore_patch import VisualizzatorePatch


class EtichettaturaWindow(QWidget):
    """
    View per l'ambiente operativo di etichettatura delle immagini
    """

    # ==========================================
    # SEGNALI
    # ==========================================
    etichetta_selezionata = Signal(str, bool)     # booleano (True se proviene da scorciatoia, False se è un click)
    richiesta_rimozione_etichetta = Signal()
    richiesta_avanti = Signal()
    richiesta_indietro = Signal()
    richiesta_salto = Signal(str)
    richiesta_contesto = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Digital Pathology Lab - Etichettatura")
        self.setMinimumSize(800, 600)
        self.bottoni_dinamici = {}
        self.shortcuts_dinamici = []
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)


        # ==========================================
        # AREA DI LAVORO
        # ==========================================
        body_layout = QHBoxLayout()

        # 🟢 1. COLONNA SINISTRA: CRONOLOGIA (Visual Context History)
        history_panel = QVBoxLayout()
        history_panel.setSpacing(10)

        titolo_history = QLabel("Ultime Patch Etichettate:")
        titolo_history.setStyleSheet("font-weight: bold; font-size: 14px; color: red;")
        titolo_history.setAlignment(Qt.AlignmentFlag.AlignCenter)
        history_panel.addWidget(titolo_history)

        self.scroll_history = QScrollArea()
        self.scroll_history.setFixedWidth(350)
        self.scroll_history.setWidgetResizable(True)
        self.scroll_history.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_history.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.history_container = QWidget()
        self.history_container.setStyleSheet("background-color: transparent;")
        self.history_layout = QGridLayout(self.history_container)
        self.history_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.history_layout.setSpacing(5)  # Spazio arioso tra le miniature
        self.history_layout.setContentsMargins(5, 5, 5, 5)

        self.scroll_history.setWidget(self.history_container)
        history_panel.addWidget(self.scroll_history)

        body_layout.addLayout(history_panel)

        # 🔵 2. COLONNA CENTRALE: IMMAGINE E NAVIGAZIONE
        center_panel = QVBoxLayout()
        center_panel.setSpacing(10)

        self.image_viewer = VisualizzatorePatch()
        self.image_viewer.reset_interfaccia()
        center_panel.addWidget(self.image_viewer, stretch=1)

        self.radio_rivedere = QRadioButton("Segna come «da rivedere» [R]")
        self.radio_rivedere.setAutoExclusive(False)
        self.radio_rivedere.setProperty("class", "ReviewRadio")
        center_panel.addWidget(self.radio_rivedere)

        # Controller di Navigazione
        nav_layout = QHBoxLayout()
        self.btn_prev = QPushButton("Precedente [←]")
        self.btn_prev.setProperty("class", "NavButton")
        self.btn_prev.clicked.connect(self.richiesta_indietro.emit)

        self.btn_next = QPushButton("Successiva [→]")
        self.btn_next.setProperty("class", "NavButton")
        self.btn_next.clicked.connect(self.richiesta_avanti.emit)

        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.btn_next)
        center_panel.addLayout(nav_layout)

        self.label_counter = QLabel("1 di X")
        self.label_counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_counter.setProperty("class", "CounterLabel")
        center_panel.addWidget(self.label_counter)


        body_layout.addLayout(center_panel, stretch=3)

        # --- PANNELLO DESTRO (Bottoni Dinamici e Note) ---
        right_panel = QVBoxLayout()
        right_panel.setSpacing(15)

        # MENU A TENDINA PER I FILTRI
        titolo_filtri = QLabel("Filtro Navigazione:")
        titolo_filtri.setStyleSheet("font-weight: bold; font-size: 14px;")
        right_panel.addWidget(titolo_filtri)

        self.combo_filtri = QComboBox()
        self.combo_filtri.addItems([
            "Tutte le patch (Nessun filtro)[F1]",
            "Solo non ancora mostrate [F2]",
            "Solo senza etichetta [F3]",
            "Solo 'da rivedere' [F4]"
        ])
        # Stile per renderlo alto e cliccabile comodamente
        self.combo_filtri.setStyleSheet("QComboBox { padding: 5px; font-size: 13px; }")
        right_panel.addWidget(self.combo_filtri)

        right_panel.addSpacing(10)  # Un po' di respiro prima delle classi

        titolo_etichette = QLabel("Classi di Etichette")
        titolo_etichette.setStyleSheet("font-weight: bold; font-size: 14px;")
        right_panel.addWidget(titolo_etichette)

        # CONTENITORE DINAMICO PER I BOTTONI
        self.layout_bottoni_etichette = QVBoxLayout()
        self.layout_bottoni_etichette.setSpacing(10)

        self.gruppo_etichette = QButtonGroup(self)
        self.gruppo_etichette.setExclusive(True)

        right_panel.addLayout(self.layout_bottoni_etichette)

        right_panel.addSpacing(20)

        self.text_note = QTextEdit()
        self.text_note.setPlaceholderText("Aggiungi nota tecnica...")
        self.text_note.setProperty("class", "NoteInput")
        right_panel.addWidget(self.text_note, stretch=1)

        # Salva ed Esci
        save_layout = QHBoxLayout()
        save_layout.addStretch()

        self.btn_dashboard = QPushButton("Torna alla Dashboard")
        self.btn_dashboard.setProperty("class", "PrimaryButton")

        save_layout.addWidget(self.btn_dashboard)
        right_panel.addLayout(save_layout)

        # Ingabbiamo il layout destro dentro un Widget fisico
        right_container = QWidget()
        right_container.setLayout(right_panel)
        right_container.setMaximumWidth(350)
        body_layout.addStretch()
        body_layout.addWidget(right_container)

        main_layout.addLayout(body_layout)

        self._setup_nav_shortcuts()

    # ==========================================
    # API PUBBLICA
    # ==========================================

    # Generazione dinamica dell'interfaccia
    def imposta_etichette_da_json(self, lista_etichette: list[str], color_map: dict = None):
        """
        Riceve l'elenco delle classi dal file di progetto e crea fisicamente
        i pulsanti e le scorciatoie da tastiera
        """
        # Pulizia preventiva
        self._pulisci_bottoni_esistenti()

        # 🟢 Salviamo la mappa colori nella view per usarla nella cronologia!
        self.color_map = color_map or {}

        # Creazione dinamica
        for i, nome_etichetta in enumerate(lista_etichette):
            tasto = str(i + 1) if (i + 1) <= 9 else ""
            testo = f"{nome_etichetta} [{tasto}]" if tasto else nome_etichetta

            # Creiamo il bottone fisico
            nuovo_btn = QPushButton(testo)
            nuovo_btn.setCheckable(True)
            nuovo_btn.setProperty("class", "LabelButton")
            nuovo_btn.setProperty("raw_label", nome_etichetta)

            # Opzionale: Se vuoi colorare anche il bordino del bottone con il colore della classe
            if nome_etichetta in self.color_map:
                colore = self.color_map[nome_etichetta]
                nuovo_btn.setStyleSheet(f"border-left: 5px solid {colore};")

            nuovo_btn.clicked.connect(lambda checked=False, nome=nome_etichetta: self.etichetta_selezionata.emit(nome, False))

            # Aggiungiamo alla UI e al tracciamento
            self.layout_bottoni_etichette.addWidget(nuovo_btn)
            self.gruppo_etichette.addButton(nuovo_btn)
            self.bottoni_dinamici[nome_etichetta] = nuovo_btn

            # Creiamo lo shortcut hardware
            if tasto:
                shortcut = QShortcut(QKeySequence(tasto), self)
                shortcut.activated.connect(lambda n=nome_etichetta: self._shortcut_etichetta(n))
                self.shortcuts_dinamici.append(shortcut)

    def mostra_etichetta_selezionata(self, etichetta_salvata: Optional[str]):
        """Accende il bottone corretto senza innescare i segnali"""
        # Blocchiamo i segnali del gruppo così l'interfaccia si aggiorna in silenzio
        self.gruppo_etichette.blockSignals(True)

        self.gruppo_etichette.setExclusive(False)
        for btn in self.bottoni_dinamici.values():
            btn.setChecked(False)
        self.gruppo_etichette.setExclusive(True)

        if etichetta_salvata and etichetta_salvata in self.bottoni_dinamici:
            self.bottoni_dinamici[etichetta_salvata].setChecked(True)

        self.gruppo_etichette.blockSignals(False)

    def get_etichetta_attiva(self) -> Optional[str]:
        """Restituisce il nome pulito dell'etichetta selezionata, se c'è"""
        btn = self.gruppo_etichette.checkedButton()
        return btn.property("raw_label") if btn else None

    def carica_immagine(self, dato_immagine):
        # Se è già un QPixmap (dal controller), usalo DIRETTAMENTE senza clonarlo!
        if isinstance(dato_immagine, QPixmap):
            pixmap = dato_immagine
        else:
            # Altrimenti comportati come prima (se è un percorso file)
            pixmap = QPixmap(dato_immagine) if dato_immagine else QPixmap()

        if pixmap.isNull():
            self.image_viewer.pulisci_visualizzazione()
            return
        self.image_viewer.mostra_immagine(pixmap)

    def aggiorna_stato_navigazione(self, indice_corrente: int, totale_patch: int):
        self.btn_prev.setEnabled(indice_corrente > 0)
        self.btn_next.setEnabled(indice_corrente < totale_patch - 1)
        self.label_counter.setText(f"{indice_corrente + 1} di {totale_patch}")

    def aggiorna_cronologia(self, history_data: list):
        """Riceve una lista di tuple (QPixmap, nome_etichetta, colore) e le disegna"""
        # 1. Pulisce la vecchia lista
        while self.history_layout.count():
            item = self.history_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 2. Disegna le nuove miniature
        for index, (pid, pixmap, nome, colore) in enumerate(history_data):
            thumb = ThumbnailHistoryWidget(pid, pixmap, nome, colore)
            thumb.doppio_click.connect(self.richiesta_salto.emit)

            riga = index // 2
            colonna = index % 2

            self.history_layout.addWidget(thumb, riga, colonna)

    # ==========================================
    # LOGICA INTERNA
    # ==========================================
    def _pulisci_bottoni_esistenti(self):
        for btn in self.bottoni_dinamici.values():
            self.gruppo_etichette.removeButton(btn)
            self.layout_bottoni_etichette.removeWidget(btn)
            btn.deleteLater()

        for shortcut in self.shortcuts_dinamici:
            shortcut.deleteLater()

        self.bottoni_dinamici.clear()
        self.shortcuts_dinamici.clear()

    def _setup_nav_shortcuts(self):
        """Shortcut fissi di navigazione"""
        self.shortcut_avanti = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        self.shortcut_avanti.activated.connect(lambda: self.btn_next.click())

        self.shortcut_indietro = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        self.shortcut_indietro.activated.connect(lambda: self.btn_prev.click())

        self.shortcut_review = QShortcut(QKeySequence(Qt.Key.Key_R), self)
        self.shortcut_review.activated.connect(lambda: self._click_disabilitato(self.radio_rivedere))

        self.shortcut_esc = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self.shortcut_esc.activated.connect(lambda: self.btn_dashboard.click())

        self.shortcut_filtro_all_patch = QShortcut(QKeySequence(Qt.Key.Key_F1), self)
        self.shortcut_filtro_all_patch.activated.connect(lambda: self.combo_filtri.setCurrentIndex(0))

        self.shortcut_filtro_viste = QShortcut(QKeySequence(Qt.Key.Key_F2), self)
        self.shortcut_filtro_viste.activated.connect(lambda: self.combo_filtri.setCurrentIndex(1))

        self.shortcut_filtro_unlabeled = QShortcut(QKeySequence(Qt.Key.Key_F3), self)
        self.shortcut_filtro_unlabeled.activated.connect(lambda: self.combo_filtri.setCurrentIndex(2))

        self.shortcut_filtro_reviewed = QShortcut(QKeySequence(Qt.Key.Key_F4), self)
        self.shortcut_filtro_reviewed.activated.connect(lambda: self.combo_filtri.setCurrentIndex(3))

    def _click_disabilitato(self, widget: QWidget):
        """Disabilita gli shortcut se l'utente sta scrivendo nelle note"""
        if not self.text_note.hasFocus():
            if isinstance(widget, QRadioButton):
                widget.setChecked(not widget.isChecked())
            elif hasattr(widget, "click"):
                widget.click()

    def mostra_avviso_fine_sessione(self) -> bool:
        """
        Mostra un popup informando l'utente che la sessione è finita.
        Restituisce True se l'utente vuole tornare alla Dashboard, False se vuole restare.
        """
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Sessione Terminata")
        msg.setText("Hai raggiunto l'ultima patch di questa sessione!")
        msg.setInformativeText("Vuoi tornare alla Dashboard o revisionare la sessione corrente?")

        # Creiamo due bottoni personalizzati
        btn_dashboard = msg.addButton("Torna alla Dashboard", QMessageBox.ButtonRole.AcceptRole)
        btn_resta = msg.addButton("Revisiona", QMessageBox.ButtonRole.RejectRole)

        # Mostriamo il popup e blocchiamo l'interfaccia finché l'utente non sceglie
        msg.exec()

        # Controlliamo quale bottone ha cliccato
        return msg.clickedButton() == btn_dashboard

    def _shortcut_etichetta(self, nome_etichetta):
        """Invia il segnale specificando che l'azione proviene da uno shortcut (True)"""
        if not self.text_note.hasFocus():
            self.etichetta_selezionata.emit(nome_etichetta, True)

    # ==========================================
    # EVENTI TASTIERA (Zoom contensto)
    # ==========================================
    def keyPressEvent(self, event):
        # Sicurezza: Se l'utente sta digitando nelle note, disattiviamo le scorciatoie!
        if self.text_note.hasFocus():
            super().keyPressEvent(event)
            return

        # isAutoRepeat() è fondamentale: impedisce che tenere premuto spari mille segnali al secondo
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self.richiesta_contesto.emit(True) # Invia TRUE
        # Tasto CANC o BACKSPACE per eliminare l'etichetta
        elif event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace) and not event.isAutoRepeat():
            self.richiesta_rimozione_etichetta.emit()

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self.richiesta_contesto.emit(False) # Invia FALSE
        super().keyReleaseEvent(event)


class ThumbnailHistoryWidget(QFrame):
    """Mini-widget che mostra una patch etichettata in precedenza"""
    doppio_click = Signal(str)

    def __init__(self, patch_id: str, pixmap: QPixmap, nome_etichetta: str, colore_hex: str):
        super().__init__()
        self.patch_id = patch_id

        dimensione_lato = 140
        self.setFixedSize(dimensione_lato, dimensione_lato + 30)  # +30 per il banner di testo

        self.setStyleSheet(f"""
            QFrame {{
                border: 1px solid {colore_hex};
                border-radius: 3px;
                background-color: #1e1e1e;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        lbl_img = QLabel()


        scaled_pixmap = pixmap.scaled(
            dimensione_lato, dimensione_lato,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        lbl_img.setPixmap(scaled_pixmap)
        lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_img.setStyleSheet("border: none; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;")

        testo = f"{nome_etichetta.upper()} \n {patch_id}"
        lbl_testo = QLabel(testo)
        lbl_testo.setFixedHeight(30)
        lbl_testo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_testo.setStyleSheet(f"""
            background-color: {colore_hex}; 
            color: black; 
            font-weight: 800; 
            font-size: 11px;
            letter-spacing: 1px;
            border: none; 
            border-top-left-radius: 0px; 
            border-top-right-radius: 0px;
            border-bottom-left-radius: 2px;
            border-bottom-right-radius: 2px;
        """)

        layout.addWidget(lbl_img)
        layout.addWidget(lbl_testo)

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mouseDoubleClickEvent(self, event):
        "Override per intercettare il doppio click"
        self.doppio_click.emit(self.patch_id)