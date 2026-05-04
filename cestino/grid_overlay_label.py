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

        view_w = self.width()
        view_h = self.height()
        factor = self.ratio * self.scale_factor

        # ==========================================
        # HELPER INTERNO PER UNIFICARE GLI ASSI
        # ==========================================
        def disegna_assi(orig_dim, grid_dim, view_limit, is_vertical):
            step = grid_dim * factor

            # Se le linee sono troppo fitte (es. < 3px), saltiamo il disegno per non freezare l'app
            if step <= 3:
                return

            num_lines = orig_dim // grid_dim
            offset_orig = (orig_dim % grid_dim) // 2
            start_pos = offset_orig * factor

            for i in range(num_lines + 1):
                pos = int(start_pos + (i * step))

                # Controllo di sicurezza: disegniamo solo se la linea cade dentro la finestra visibile
                if 0 <= pos <= view_limit:
                    if is_vertical:
                        # Asse X: Disegna una linea in verticale dall'alto (0) al basso (view_h)
                        painter.drawLine(pos, 0, pos, view_h)
                    else:
                        # Asse Y: Disegna una linea in orizzontale da sinistra (0) a destra (view_w)
                        painter.drawLine(0, pos, view_w, pos)

        # Richiamiamo la funzione per l'Asse X (Linee Verticali)
        # Il limite visivo è view_w
        disegna_assi(self.orig_w, self.grid_w, view_w, is_vertical=True)

        # Richiamiamo la funzione per l'Asse Y (Linee Orizzontali)
        # Il limite visivo è view_h
        disegna_assi(self.orig_h, self.grid_h, view_h, is_vertical=False)

        painter.end()