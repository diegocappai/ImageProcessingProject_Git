from .visualizzatore_base import VisualizzatoreBase
from PySide6.QtWidgets import QLabel
from PySide6.QtGui import Qt


class VisualizzatorePatch(VisualizzatoreBase):
    def __init__(self):
        # Iniettiamo una QLabel standard
        super().__init__(QLabel())


    def reset_interfaccia(self):

        self.image_widget.setText("Fai doppio click sulla patch per selezionarla!")
        self.image_widget.setAlignment(Qt.AlignCenter)
        self.image_widget.setStyleSheet("QLabel { color: white; font-size: 14px; font-weight: bold; }")

    def pulisci_visualizzazione(self):
        self.image_widget.setText("Caricamento patch successiva")
        #self.image_widget.clear()
        #self.reset_interfaccia()


    def mostra_immagine(self, pixmap):
        self.original_pixmap = pixmap
        if self.original_pixmap.isNull():
            self.image_widget.setText("Errore caricamento")
            return

        self.adatta_a_finestra()
        self.aggiorna_visualizzazione()
        self.image_widget.setPixmap(self.original_pixmap)

    def mostra_loading(self):
        self.message_label.setText("Caricamento patch successiva...")
        self.message_label.show()
        self.message_label.raise_()

        self.repaint()