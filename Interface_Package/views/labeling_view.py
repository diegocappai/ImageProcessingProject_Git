from typing import Optional
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QTextEdit, QRadioButton, QButtonGroup,
                               QMenu, QInputDialog)
from PySide6.QtGui import QPixmap, QAction, QShortcut, QKeySequence
from PySide6.QtCore import Qt, Signal
from Interface_Package.visualizzatori.visualizzatore_patch import VisualizzatorePatch


class EtichettaturaWindow(QWidget):
    """
    View per l'ambiente operativo di etichettatura delle immagini
    """

    # ==========================================
    # SEGNALI
    # ==========================================
    etichetta_selezionata = Signal(str)
    richiesta_avanti = Signal()
    richiesta_indietro = Signal()

    def __init__(self, percorso_immagine: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Digital Pathology Lab - Etichettatura")
        self.setMinimumSize(800, 600)

        self.init_ui()

        self.carica_immagine(percorso_immagine)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ==========================================
        # HEADER: BARRA DEI MENU
        # ==========================================
        menu_bar = QWidget()
        menu_layout = QHBoxLayout(menu_bar)
        menu_layout.setContentsMargins(10, 5, 10, 5)

        self.btn_etichette = QPushButton("Etichette")
        self.btn_etichette.setProperty("class", "MenuDropdownBtn")

        self.menu_etichette = QMenu(self)

        self.action_normal = QAction("Normal", self, checkable=True)
        self.action_normal.setChecked(True)
        self.menu_etichette.addAction(self.action_normal)

        self.action_tumor = QAction("Tumor", self, checkable=True)
        self.action_tumor.setChecked(True)
        self.menu_etichette.addAction(self.action_tumor)

        self.action_separator = self.menu_etichette.addSeparator()

        self.action_custom = QAction("+ Personalizzata...", self)
        self.action_custom.triggered.connect(self.aggiungi_etichetta_personalizzata)
        self.menu_etichette.addAction(self.action_custom)

        self.btn_etichette.setMenu(self.menu_etichette)
        menu_layout.addWidget(self.btn_etichette)
        menu_layout.addStretch()
        main_layout.addWidget(menu_bar)

        # ==========================================
        # AREA DI LAVORO
        # ==========================================
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(15, 15, 15, 15)
        body_layout.setSpacing(20)

        # --- PANNELLO SINISTRO ---
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)

        # Import del componente specializzato per il rendering delle immagini
        self.image_viewer = VisualizzatorePatch()
        self.image_viewer.reset_interfaccia()
        left_panel.addWidget(self.image_viewer, stretch=1)

        # RadioButton per segnalazioni
        self.radio_rivedere = QRadioButton("Segna come «da rivedere» [R]")
        self.radio_rivedere.setAutoExclusive(False)
        self.radio_rivedere.setProperty("class", "ReviewRadio")
        left_panel.addWidget(self.radio_rivedere)

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
        left_panel.addLayout(nav_layout)

        self.label_counter = QLabel("1 di 100")
        self.label_counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_counter.setProperty("class", "CounterLabel")
        left_panel.addWidget(self.label_counter)

        body_layout.addLayout(left_panel, stretch=2)

        # --- PANNELLO DESTRO ---
        right_panel = QVBoxLayout()
        right_panel.setSpacing(15)

        self.text_note = QTextEdit()
        self.text_note.setPlaceholderText("Aggiungi nota...")
        self.text_note.setProperty("class", "NoteInput")
        right_panel.addWidget(self.text_note, stretch=1)

        # Layout Bottoni Etichettatura
        self.layout_bottoni_etichette = QVBoxLayout()
        self.layout_bottoni_etichette.setSpacing(10)

        self.gruppo_etichette = QButtonGroup(self)
        self.gruppo_etichette.setExclusive(True)

        self.btn_normal = QPushButton("Normal [1]")
        self.btn_normal.setCheckable(True)
        self.btn_normal.setProperty("class", "LabelButton")
        self.btn_normal.clicked.connect(lambda: self.etichetta_selezionata.emit("Normal"))

        self.layout_bottoni_etichette.addWidget(self.btn_normal)
        self.gruppo_etichette.addButton(self.btn_normal)

        self.btn_tumor = QPushButton("Tumor [2]")
        self.btn_tumor.setCheckable(True)
        self.btn_tumor.setProperty("class", "LabelButton")
        self.btn_tumor.clicked.connect(lambda: self.etichetta_selezionata.emit("Tumor"))

        self.layout_bottoni_etichette.addWidget(self.btn_tumor)
        self.gruppo_etichette.addButton(self.btn_tumor)

        # Stato per l'allocazione dinamica delle scorciatoie da tastiera
        self.prossimo_tasto_libero = 3

        # Sincronizzazione visiva
        self.action_normal.toggled.connect(self.btn_normal.setVisible)
        self.action_tumor.toggled.connect(self.btn_tumor.setVisible)

        right_panel.addLayout(self.layout_bottoni_etichette)
        right_panel.addStretch(1)

        # Salva ed Esci
        save_layout = QHBoxLayout()
        save_layout.addStretch()

        self.btn_salva = QPushButton("Salva ed esci")
        self.btn_salva.setProperty("class", "PrimaryButton")

        save_layout.addWidget(self.btn_salva)
        right_panel.addLayout(save_layout)

        body_layout.addLayout(right_panel, stretch=1)
        main_layout.addLayout(body_layout)

        self._setup_shortcuts()

    def aggiungi_etichetta_personalizzata(self):
        """Istanzia nuovi bottoni, scorciatoie e voci di menù"""
        testo, ok = QInputDialog.getText(self, "Nuova Etichetta", "Inserisci il nome della nuova etichetta:")

        if ok and testo.strip():
            nome_etichetta = testo.strip()

            testo_visibile = nome_etichetta
            ha_shortcut = False

            # Allocazione dinamica dello shortcut
            if hasattr(self, 'prossimo_tasto_libero') and self.prossimo_tasto_libero <= 9:
                testo_visibile = f"{nome_etichetta} [{self.prossimo_tasto_libero}]"
                ha_shortcut = True

            # Costruzione Widget
            nuovo_btn = QPushButton(testo_visibile)
            nuovo_btn.setCheckable(True)
            nuovo_btn.setProperty("class", "LabelButton")
            nuovo_btn.style().polish(nuovo_btn)

            nuovo_btn.clicked.connect(lambda checked=False, text=nome_etichetta: self.etichetta_selezionata.emit(text))

            if ha_shortcut:
                nuovo_shortcut = QShortcut(QKeySequence(str(self.prossimo_tasto_libero)), self)
                nuovo_shortcut.activated.connect(lambda btn=nuovo_btn: self._click_protetto(btn))
                self.prossimo_tasto_libero += 1

            self.layout_bottoni_etichette.addWidget(nuovo_btn)
            self.gruppo_etichette.addButton(nuovo_btn)

            # Costruzione Elemento Menu
            nuova_action = QAction(nome_etichetta, self, checkable=True)
            nuova_action.setChecked(True)
            self.menu_etichette.insertAction(self.action_separator, nuova_action)
            nuova_action.toggled.connect(nuovo_btn.setVisible)

    # ==========================================
    # API PUBBLICA
    # ==========================================
    def carica_immagine(self, percorso: Optional[str]):
        """Passa il percorso fisico al visualizzatore interno"""
        pixmap = QPixmap(percorso) if percorso else QPixmap()
        if pixmap.isNull():
            self.image_viewer.pulisci_visualizzazione()
            return

        self.image_viewer.mostra_immagine(pixmap)

    def aggiorna_stato_navigazione(self, indice_corrente: int, totale_patch: int):
        """Disabilita automaticamente le frecce se si è all'inizio o alla fine dell'array"""
        self.btn_prev.setEnabled(indice_corrente > 0)
        self.btn_next.setEnabled(indice_corrente < totale_patch - 1)

    # ==========================================
    # KEYBINDINGS E SICUREZZA UX
    # ==========================================
    def _setup_shortcuts(self):
        """Mappa la tastiera fisica alle azioni virtuali del software"""

        # Frecce direzionali
        self.shortcut_avanti = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        self.shortcut_avanti.activated.connect(self.btn_next.clicked)

        self.shortcut_indietro = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        self.shortcut_indietro.activated.connect(self.btn_prev.clicked)

        # Tasti Etichettatura Base
        self.shortcut_label1 = QShortcut(QKeySequence("1"), self)
        self.shortcut_label1.activated.connect(lambda: self._click_protetto(self.btn_normal))

        self.shortcut_label2 = QShortcut(QKeySequence("2"), self)
        self.shortcut_label2.activated.connect(lambda: self._click_protetto(self.btn_tumor))

        self.shortcut_review = QShortcut(QKeySequence(Qt.Key.Key_R), self)
        self.shortcut_review.activated.connect(lambda: self._click_protetto(self.radio_rivedere))

    def _click_protetto(self, widget: QWidget):
        """
        Impedisce che i tasti rapidi interferiscano con la digitazione all'interno della casella di testo delle Note
        """
        if not self.text_note.hasFocus():
            if isinstance(widget, QRadioButton):
                widget.setChecked(not widget.isChecked())
            else:
                widget.click()