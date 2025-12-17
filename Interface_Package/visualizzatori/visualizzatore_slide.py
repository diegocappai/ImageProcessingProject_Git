from .visualizzatore_base import VisualizzatoreBase
from Interface_Package.widgets.grid_overlay_label import GridOverlayLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Signal, Qt, QSize

class VisualizzatoreSlide(VisualizzatoreBase):

    # Segnale doppio-click con coordinate
    seg_doppio_click = Signal(int, int)

    def __init__(self):
        # Iniettiamo la label CUSTOM per disegnare griglia sopra l'immagine
        super().__init__(GridOverlayLabel())

        # Inizializzo variabili dimensione tile
        self.current_w = None
        self.current_h = None

        # Dimensioni reali immagine
        self.real_size = QSize(1,1)

    # Riceve la miniatura (pixmap) e le dimensioni originali della slide
    def mostra_immagine(self, pixmap: QPixmap, original_w: int, original_h: int):
        self.original_pixmap = pixmap
        # Memorizzo dimensioni reali
        self.real_img_size = QSize(original_w, original_h)

        # Controllo di sicurezza
        if self.original_pixmap.isNull():
            self.image_widget.setText("Errore caricamento")
            return

        # Chiama metodo genitore per resettare lo zoom e centrare l'immagine
        self.adatta_a_finestra()

        # Calcola griglia e posizioni
        self.aggiorna_visualizzazione()

        # Imposta l'immagine nel widget
        self.image_widget.setPixmap(self.original_pixmap)

    # ---- OVERRIDE ----
    def aggiorna_visualizzazione(self):
        super().aggiorna_visualizzazione()

        # Logica specifica per disegnare la griglia
        if self.original_pixmap and not self.real_img_size.isEmpty():
            # Calcoliamo il rapporto: Larghezza Thumbnail / Larghezza Originale
            thumb_w = self.original_pixmap.width()
            orig_w = self.real_img_size.width()
            orig_h = self.real_img_size.height()

            # Calcola rapporto di scala tra miniatura e slide
            current_ratio = thumb_w / orig_w if orig_w > thumb_w > 0 else 1.0

            # Passa i dati alla GridOverlayLabel
            self.image_widget.set_grid_params(
                w = self.current_w,
                h = self.current_h,
                orig_w = orig_w,
                orig_h = orig_h,
                scale = self.scale_factor,
                ratio = current_ratio
            )

    # --- LOGICA DOPPIO CLICK ---
    def mouseDoubleClickEvent(self, event):
        if self.original_pixmap and event.button() == Qt.LeftButton:
            # Trasforma le coordinate finestra a coordinate dell'immagine
            pos_label = self.image_widget.mapFrom(self, event.pos())
            # Dimensioni attuali visualizzate (zoom)
            w_cur = self.image_widget.width()
            h_cur = self.image_widget.height()
            # Dimensioni della miniatura
            w_orig = self.original_pixmap.width()
            h_orig = self.original_pixmap.height()

            if w_cur > 0 and h_cur > 0:
                # conversione da zoom a reale
                real_x = int(pos_label.x() * (w_orig / w_cur))
                real_y = int(pos_label.y() * (h_orig / h_cur))

                # assicura che non escano dai bordi
                real_x = max(0, min(real_x, w_orig - 1))
                real_y = max(0, min(real_y, h_orig - 1))

                print(f"click: {real_x}, {real_y}") # DEBUG

                # Emissione del segnale
                self.seg_doppio_click.emit(real_x, real_y)

        # Passa l'evento al genitore
        super().mouseDoubleClickEvent(event)