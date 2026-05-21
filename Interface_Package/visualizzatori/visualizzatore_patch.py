from .visualizzatore_base import VisualizzatoreBase
from PySide6.QtWidgets import QLabel


class VisualizzatorePatch(VisualizzatoreBase):
    """
    Classe specifica per la visualizzazione delle singole Patch.
    """

    def __init__(self):
        label_immagine = QLabel()
        label_immagine.setScaledContents(True)

        # Inietto nella classe base
        super().__init__(label_immagine)

    #TODO: valutare se eliminare questo metodo
    def mostra_loading(self):
        """
        Feedback visivo bloccante. Rassicura l'utente che il programma sta estraendo
        l'immagine ad alta risoluzione e non si è bloccato.
        """
        self.image_widget.setStyleSheet("")
        self.image_widget.setText("Caricamento in corso, attendere...")

        # Forzo l'aggiornamento immediato dello schermo
        self.repaint()

    def mostra_immagine(self, pixmap):
        """
        Riceve la Pixmap e invoca il motore di ridimensionamento della classe genitore.
        """
        self.original_pixmap = pixmap

        if self.original_pixmap.isNull():
            self.image_widget.setText("Errore: Impossibile caricare l'immagine.")
            return

        self.image_widget.setText("")

        self.adatta_a_finestra()
        self.aggiorna_visualizzazione()


