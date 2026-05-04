
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QWidget, QHBoxLayout, QMessageBox
from PySide6.QtGui import QCloseEvent
from PySide6.QtCore import Signal
from enum import Enum, auto

from .views.page_start import HomePage
from .views.page_show_patch import PageShowPatch
from .views.page_setting_slide import PageSettingSlide
from .views.page_setting_dataset import PageSettingDataset
from .views.page_set_grid import PageSetGrid
from .views.page_show_slide import PageShowSlide


class PageID(Enum):
    START = auto()
    SET_DATASET = auto()
    SET_SLIDE = auto()
    SET_GRID = auto()
    SHOW_PATCH = auto()
    SHOW_SLIDE = auto()



class MainWindow(QMainWindow):
    richiesta_uscita = Signal()
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Processing Application")
        self.resize(600, 400)

        #Widget centrale
        central_widget = QWidget()
        main_layout = QHBoxLayout()


        # ---- STACK DELLE PAGINE ----
        self.stack = QStackedWidget()

        # Istanziamo le pagine
        self.page_start = HomePage()
        self.page_setting_dataset = PageSettingDataset()
        self.page_setting_slide = PageSettingSlide()
        self.page_show_patch = PageShowPatch()
        self.page_set_grid = PageSetGrid()
        self.page_show_slide = PageShowSlide()

        # Aggiungiamo allo stack
        self.stack.addWidget(self.page_start)
        self.stack.addWidget(self.page_setting_dataset)
        self.stack.addWidget(self.page_setting_slide)
        self.stack.addWidget(self.page_set_grid)
        self.stack.addWidget(self.page_show_patch)
        self.stack.addWidget(self.page_show_slide)

        # Mappatura pagine
        self.pages_map = {
            PageID.START:self.page_start,
            PageID.SET_DATASET:self.page_setting_dataset,
            PageID.SET_SLIDE:self.page_setting_slide,
            PageID.SET_GRID:self.page_set_grid,
            PageID.SHOW_PATCH:self.page_show_patch,
            PageID.SHOW_SLIDE:self.page_show_slide
        }


        # Setup Layout
        main_layout.addWidget(self.stack)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)


    def switch_page(self, page_id: PageID):
        if page_id in self.pages_map:
            widget = self.pages_map[page_id]
            self.stack.setCurrentWidget(widget)
        else:
            print(f"Errore: Pagina {page_id} non trovata!")

    def show_info_message(self, message):
        QMessageBox.information(self, "Info", message)

    def closeEvent(self, event: QCloseEvent):

        risposta = QMessageBox.question(
            self,
            "Conferma Uscita",
            "Sei sicuro di voler chiudere?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No # Tasto di defaul per sicurezza
        )

        if risposta == QMessageBox.Yes:
            self.richiesta_uscita.emit()
            event.accept()
        else:
            event.ignore()



