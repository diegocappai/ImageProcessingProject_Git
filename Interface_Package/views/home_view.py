import os
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QHBoxLayout,
                               QPushButton, QListWidget, QListWidgetItem, QMenu)
from PySide6.QtGui import QCursor


class HomeView(QWidget):
    """
    View per la schermata Iniziale (Home)
    """
    # ==========================================
    # SEGNALI
    # ==========================================
    richiesta_creazione = Signal()
    richiesta_caricamento = Signal()
    progetto_recente_cliccato = Signal(str)
    progetto_recente_eliminato = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Digital Pathology Lab - Home")
        self.setMinimumSize(700, 400)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Corpo centrale
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(40, 40, 40, 40)
        body_layout.setSpacing(50)

        # ==========================================
        # PANNELLO SINISTRO
        # ==========================================
        left_layout = QVBoxLayout()

        self.btn_crea = QPushButton("➕ Nuovo Progetto")
        self.btn_crea.setProperty("class", "HeroButton")
        self.btn_crea.setMinimumHeight(80)

        self.btn_carica = QPushButton("📂 Carica Progetto")
        self.btn_carica.setProperty("class", "HeroButton")
        self.btn_carica.setMinimumHeight(80)

        # Cablaggio
        self.btn_crea.clicked.connect(self.richiesta_creazione.emit)
        self.btn_carica.clicked.connect(self.richiesta_caricamento.emit)

        left_layout.addWidget(self.btn_crea)
        left_layout.setSpacing(20)
        left_layout.addWidget(self.btn_carica)
        left_layout.addStretch()

        body_layout.addLayout(left_layout, stretch=2)

        # ==========================================
        # PANNELLO DESTRO (Progetti Recenti)
        # ==========================================
        right_layout = QVBoxLayout()
        right_layout.setSpacing(5)

        lbl_recenti = QLabel("Progetti recenti:")
        lbl_recenti.setProperty("class", "SectionTitle")
        right_layout.addWidget(lbl_recenti)

        self.list_recenti = QListWidget()

        self.list_recenti.itemDoubleClicked.connect(
            lambda item: self.progetto_recente_cliccato.emit(item.data(Qt.ItemDataRole.UserRole))
        )

        self.list_recenti.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_recenti.customContextMenuRequested.connect(self.mostra_menu_contestuale)

        right_layout.addWidget(self.list_recenti)
        body_layout.addLayout(right_layout, stretch=1)

        main_layout.addLayout(body_layout)

    # ==========================================
    # API PUBBLICA E RENDERING DATI
    # ==========================================
    def aggiorna_lista_recenti(self, progetti: list):
        """
        Popola la UI con la cronologia dei progetti recenti
        """
        self.list_recenti.clear()

        if not progetti:
            item_vuoto = QListWidgetItem("Nessun progetto recente.\nCreane o caricane uno!")
            item_vuoto.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_vuoto.setFlags(Qt.ItemFlag.NoItemFlags)
            item_vuoto.setForeground(Qt.GlobalColor.gray)

            item_vuoto.setSizeHint(item_vuoto.sizeHint().expandedTo(item_vuoto.sizeHint() * 3))

            self.list_recenti.addItem(item_vuoto)
            return

        for percorso in progetti:
            nome_cartella = os.path.basename(percorso)
            item = QListWidgetItem(f"📁 {nome_cartella}")

            item.setData(Qt.ItemDataRole.UserRole, percorso)
            item.setToolTip(percorso)

            self.list_recenti.addItem(item)

    def mostra_menu_contestuale(self, posizione):
        """Genera e gestisce il menù a tendina sul click destro"""
        item = self.list_recenti.itemAt(posizione)

        if item is not None:
            percorso = item.data(Qt.ItemDataRole.UserRole)

            if not percorso:
                return

            menu = QMenu(self)
            menu.setObjectName("MenuElimina")

            azione_elimina = menu.addAction("Rimuovi dai recenti")

            azione_scelta = menu.exec(QCursor.pos())

            if azione_scelta == azione_elimina:
                self.progetto_recente_eliminato.emit(percorso)