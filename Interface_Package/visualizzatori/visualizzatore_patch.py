from .visualizzatore_base import VisualizzatoreBase
from PySide6.QtWidgets import QLabel
from PySide6.QtGui import Qt


class VisualizzatorePatch(VisualizzatoreBase):
    def __init__(self):
        label_immagine = QLabel()
        label_immagine.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_immagine.setScaledContents(True)

        # Iniettiamo una QLabel standard
        super().__init__(label_immagine)


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

        # Chiamando questo metodo, la classe Base calcolerà la dimensione,
        # applicherà lo SmoothTransformation e la setterà sulla Label!
        self.aggiorna_visualizzazione()

    """def resizeEvent(self, event):
        super().resizeEvent(event)

        # 🟢 LA MAGIA GEOMETRICA
        # Prende l'altezza attuale (calcolata dinamicamente dal layout del monitor)
        # e forza la larghezza MASSIMA ad essere esattamente identica.
        # Questo spinge via il margine destro vuoto, cedendolo alla History!
        lato_quadrato = self.height()
        self.setMaximumWidth(lato_quadrato)"""

    def mostra_loading(self):
        self.message_label.setText("Caricamento patch successiva...")
        self.message_label.show()
        self.message_label.raise_()

        self.repaint()