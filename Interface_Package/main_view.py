from PySide6.QtWidgets import QMainWindow, QStackedWidget, QMessageBox
from PySide6.QtGui import QCloseEvent


class MainWindow(QMainWindow):
    """
    Finestra Madre dell'applicazione
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Digital Pathology Lab - Image Processing")
        self.setMinimumSize(1024, 768)

        # ==========================================
        # CORE ROUTING VISIVO
        # ==========================================
        # Il QStackedWidget gestisce le schermate come un mazzo di carte.
        # L'AppController deciderà quale "carta" (View) mostrare in cima.
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

    def closeEvent(self, event: QCloseEvent):
        """
        Override del metodo nativo di chiusura finestra
        """
        box = QMessageBox(self)
        box.setWindowTitle("Conferma Uscita")
        box.setText(
            "Sei sicuro di voler uscire dal programma?")

        box.setIcon(QMessageBox.Icon.Warning)

        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.No)

        risposta = box.exec()

        if risposta == QMessageBox.StandardButton.Yes:
            print("[DEBUG - MAIN VIEW] Uscita confermata dall'utente. Terminazione processo.")
            event.accept()
        else:
            event.ignore()