from typing import Optional
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QTextEdit, QRadioButton, QButtonGroup)
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
    etichetta_selezionata = Signal(str)
    richiesta_avanti = Signal()
    richiesta_indietro = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Digital Pathology Lab - Etichettatura")
        self.setMinimumSize(800, 600)

        # Tracciamo i bottoni e gli shortcut per poterli gestire dinamicamente
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

        # --- PANNELLO SINISTRO (Immagine e Navigazione) ---
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)

        self.image_viewer = VisualizzatorePatch()
        self.image_viewer.reset_interfaccia()
        left_panel.addWidget(self.image_viewer, stretch=1)

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

        self.label_counter = QLabel("1 di X")
        self.label_counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_counter.setProperty("class", "CounterLabel")
        left_panel.addWidget(self.label_counter)

        body_layout.addLayout(left_panel, stretch=2)

        # --- PANNELLO DESTRO (Bottoni Dinamici e Note) ---
        right_panel = QVBoxLayout()
        right_panel.setSpacing(15)

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

        self.btn_salva = QPushButton("Salva ed esci")
        self.btn_salva.setProperty("class", "PrimaryButton")

        save_layout.addWidget(self.btn_salva)
        right_panel.addLayout(save_layout)

        body_layout.addLayout(right_panel, stretch=1)
        main_layout.addLayout(body_layout)

        self._setup_nav_shortcuts()

    # ==========================================
    # API PUBBLICA
    # ==========================================

    # Generazione dinamica dell'interfaccia
    def imposta_etichette_da_json(self, lista_etichette: list):
        """
        Riceve l'elenco delle classi dal file di progetto e crea fisicamente
        i pulsanti e le scorciatoie da tastiera
        """
        # Pulizia preventiva
        self._pulisci_bottoni_esistenti()

        # Creazione dinamica
        for i, nome_etichetta in enumerate(lista_etichette):
            tasto_tastiera = str(i + 1) if (i + 1) <= 9 else ""
            testo_bottone = f"{nome_etichetta} [{tasto_tastiera}]" if tasto_tastiera else nome_etichetta

            # Creiamo il bottone fisico
            nuovo_btn = QPushButton(testo_bottone)
            nuovo_btn.setCheckable(True)
            nuovo_btn.setProperty("class", "LabelButton")

            nuovo_btn.clicked.connect(lambda checked=False, nome=nome_etichetta: self.etichetta_selezionata.emit(nome))

            # Aggiungiamo alla UI e al tracciamento
            self.layout_bottoni_etichette.addWidget(nuovo_btn)
            self.gruppo_etichette.addButton(nuovo_btn)
            self.bottoni_dinamici[nome_etichetta] = nuovo_btn

            # Creiamo lo shortcut hardware
            if tasto_tastiera:
                shortcut = QShortcut(QKeySequence(tasto_tastiera), self)
                shortcut.activated.connect(lambda btn=nuovo_btn: self._click_protetto(btn))
                self.shortcuts_dinamici.append(shortcut)

    def carica_immagine(self, percorso: Optional[str]):
        pixmap = QPixmap(percorso) if percorso else QPixmap()
        if pixmap.isNull():
            self.image_viewer.pulisci_visualizzazione()
            return
        self.image_viewer.mostra_immagine(pixmap)

    def aggiorna_stato_navigazione(self, indice_corrente: int, totale_patch: int):
        self.btn_prev.setEnabled(indice_corrente > 0)
        self.btn_next.setEnabled(indice_corrente < totale_patch - 1)
        self.label_counter.setText(f"{indice_corrente + 1} di {totale_patch}")

    # ==========================================
    # LOGICA INTERNA
    # ==========================================
    def _pulisci_bottoni_esistenti(self):
        """Rimuove i bottoni dalla UI e distrugge gli oggetti per evitare memory leaks"""
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
        self.shortcut_avanti.activated.connect(self.btn_next.clicked)

        self.shortcut_indietro = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        self.shortcut_indietro.activated.connect(self.btn_prev.clicked)

        self.shortcut_review = QShortcut(QKeySequence(Qt.Key.Key_R), self)
        self.shortcut_review.activated.connect(lambda: self._click_protetto(self.radio_rivedere))

    def _click_protetto(self, widget: QWidget):
        """Protegge gli shortcut se l'utente sta scrivendo nelle note"""
        if not self.text_note.hasFocus():
            if isinstance(widget, QRadioButton):
                widget.setChecked(not widget.isChecked())
            else:
                widget.click()