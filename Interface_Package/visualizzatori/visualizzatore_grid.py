from .visualizzatore_base import VisualizzatoreBase
from Interface_Package.widgets.grid_overlay_label import GridOverlayLabel

from PySide6.QtGui import QPixmap
from PySide6.QtCore import QSize



class VisualizzatoreGriglia(VisualizzatoreBase):

    def __init__(self):
        # Iniettiamo la label CUSTOM
        super().__init__(GridOverlayLabel())
        self.current_w = 50  # Default
        self.current_h = 50

        # Dimensioni reali dell'immagine
        self.real_img_size = QSize(1, 1)

    def set_grid_dims(self, w: int, h: int):
        self.current_w = w
        self.current_h = h
        # Forziamo un aggiornamento per ridisegnare la griglia
        self.aggiorna_visualizzazione()

    def set_grid_w(self, w: int):
        self.current_w = w
        self.aggiorna_visualizzazione()

    def set_grid_h(self, h: int):
        self.current_h = h
        self.aggiorna_visualizzazione()

    # TODO valutare un unico modo set_grid

    def mostra_immagine(self, pixmap: QPixmap, original_w: int, original_h: int):
        # Qui accettiamo Pixmap
        self.original_pixmap = pixmap
        self.real_img_size = QSize(original_w, original_h)

        if self.original_pixmap.isNull():
            self.image_widget.setText("Nessuna immagine")
            return

        self.adatta_a_finestra()
        self.aggiorna_visualizzazione()
        self.image_widget.setPixmap(self.original_pixmap)

    # --- OVERRIDE ---
    def aggiorna_visualizzazione(self):
        # Facciamo quello che fa la classe base (resize widget)
        super().aggiorna_visualizzazione()

        # AGGIUNGIAMO la logica specifica della griglia
        if self.original_pixmap and not self.real_img_size.isEmpty():
            # Calcoliamo il rapporto: Larghezza Thumbnail / Larghezza Originale
            thumb_w = self.original_pixmap.width()
            orig_w = self.real_img_size.width()
            orig_h = self.real_img_size.height()

            current_ratio = thumb_w / orig_w if orig_w > thumb_w > 0 else 1.0



            self.image_widget.set_grid_params(
                w = self.current_w,
                h = self.current_h,
                orig_w = orig_w,
                orig_h = orig_h,
                scale = self.scale_factor,
                ratio = current_ratio
            )

