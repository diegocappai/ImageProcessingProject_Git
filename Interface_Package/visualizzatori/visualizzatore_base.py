from PySide6.QtWidgets import QScrollArea, QWidget
from PySide6.QtCore import Qt, QPoint



class VisualizzatoreBase(QScrollArea):
    """
    Classe base astratta che gestisce Zoom, Panning (trascinamento)
    e calcoli delle coordinate.
    """


    def __init__(self, internal_widget: QWidget):
        # Ereditiamo QScrollArea per gestire automaticamente le barre di scorrimento
        super().__init__()

        # Setup base della ScrollArea
        self.setAlignment(Qt.AlignCenter)
        self.setWidgetResizable(False)
        self.setCursor(Qt.OpenHandCursor)

        # Variabili di stato
        self.last_mouse_pos = QPoint()
        self.is_dragging = False
        self.scale_factor = 1.0
        self.original_pixmap = None

        # Il widget interno viene iniettato dalla sottoclasse
        self.image_widget = internal_widget
        self.image_widget.setAlignment(Qt.AlignCenter)
        self.image_widget.setScaledContents(True)
        self.setWidget(self.image_widget)

    # --- LOGICA ZOOM ---
    def wheelEvent(self, event):
        if not self.original_pixmap:
            return

        # Verso rotazione rotella
        if event.angleDelta().y() > 0:
            self.scale_factor *= 1.2
        else:
            self.scale_factor *= 0.8

        # Limiti zoom
        self.scale_factor = max(0.1, min(self.scale_factor, 10.0))

        self.aggiorna_visualizzazione()

        # Aggiusta scrollbar per centrare lo zoom
        self.adjust_scrollbar(self.horizontalScrollBar(), 1.2 if event.angleDelta().y() > 0 else 0.8)
        self.adjust_scrollbar(self.verticalScrollBar(), 1.2 if event.angleDelta().y() > 0 else 0.8)

    # --- LOGICA PANNING ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.last_mouse_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    # Trascinamento
    def mouseMoveEvent(self, event):
        if self.is_dragging:
            # Calcolo spostamento
            delta = event.pos() - self.last_mouse_pos

            # Logica direzione
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())

            # Aggiorno ultima posizione
            self.last_mouse_pos = event.pos()
        super().mouseMoveEvent(event)

    # Rilascio tasto
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.setCursor(Qt.OpenHandCursor)
        super().mouseReleaseEvent(event)



    # --- METODI HELPER ---
    # Centraggio zoom
    def adjust_scrollbar(self, scrollbar, factor):
        scrollbar.setValue(int(factor * scrollbar.value() + ((factor - 1) * scrollbar.pageStep() / 2)))


    def adatta_a_finestra(self):
        """Calcola lo zoom iniziale per adattare l'immagine alla view"""
        if not self.original_pixmap: return

        # Dimensioni area visibile (viewport)
        view_w = self.viewport().width() if self.viewport().width() > 0 else 800
        view_h = self.viewport().height() if self.viewport().height() > 0 else 600

        ratio = min(view_w / self.original_pixmap.width(),
                    view_h / self.original_pixmap.height()) * 0.95

        self.scale_factor = min(ratio, 1.0)  # Mai ingrandire inizialmente se l'immagine è piccola

    def aggiorna_visualizzazione(self):
        """
        Metodo che applica il resize.
        """
        if self.original_pixmap:
            new_size = self.original_pixmap.size() * self.scale_factor
            self.image_widget.resize(new_size)