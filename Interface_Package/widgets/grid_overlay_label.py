from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPen, QPainter, QColor




class GridOverlayLabel(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)

        # Parametri di default
        self.grid_w: int = 50   # Larghezza reale patch
        self.grid_h: int = 50   # Altezza reale patch
        self.orig_w: int = 100  # Larghezza reale slide
        self.orig_h: int = 100  # Altezza reale slide

        # Fattori di conversione
        self.scale_factor: float = 1.0  # Zoom dell'utente
        self.ratio: float = 1.0         # Rapporto (Larghezza Miniatura / Larghezza Reale)
        self.show_grid: bool = True     # Mostrare/nascondere griglia

        # Settaggio penna per la griglia
        self.grid_pen = QPen(QColor(0, 255, 255, 150))  # Ciano semi-trasparente
        self.grid_pen.setWidth(1)

    def set_grid_params(self, w: int, h: int, orig_w: int, orig_h: int, scale: float, ratio: float = 1.0):
        # Aggiorna le variabili interne con i dati
        self.grid_w = max(10, w)
        self.grid_h = max(10, h)
        self.orig_w = orig_w
        self.orig_h = orig_h
        self.scale_factor = scale
        self.ratio = ratio
        self.update()  # Triggera paintEvent

    def paintEvent(self, event):
        # Disegna l'immagine (QLabel)
        super().paintEvent(event)

        if not self.pixmap() or not self.show_grid:
            return

        # Inizializza il pittore per disegnare SOPRA l'immagine
        painter = QPainter(self)
        painter.setPen(self.grid_pen)

        # Dimensioni attuali del widget a schermo
        view_w = self.width()
        view_h = self.height()

        # Moltiplica riduzione miniatura * zoom utente
        factor = self.ratio * self.scale_factor

        # CALCOLO ASSE X (centrando le tiles)
        num_cols = self.orig_w // self.grid_w

        remainder_w = self.orig_w % self.grid_w

        offset_x_orig = remainder_w // 2

        start_x = offset_x_orig * factor
        step_x = self.grid_w * factor

        if step_x > 3:
            for i in range(num_cols + 1):
                pos = int(start_x + (i * step_x))
                if 0 <= pos < view_w:
                    painter.drawLine(int(pos), 0, int(pos), view_h)


        # CALCOLO ASSE Y
        num_rows = self.orig_h // self.grid_h

        remainder_h = self.orig_h % self.grid_h

        offset_y_orig = remainder_h // 2

        start_y = offset_y_orig * factor
        step_y = self.grid_h * factor

        if step_y > 3:
            for i in range(num_rows + 1):
                pos = int(start_y + (i * step_y))
                if 0 <= pos < view_w:
                    painter.drawLine(0, int(pos), view_w, int(pos))

        # TODO ragionare su metodo unico per asse X e Y


        painter.end()
