#import set_pyvips
import pyvips
import numpy as np
from .abc_image_manager import ImageManager

class VipsImageManager(ImageManager):
    def __init__(self, file_path, tile_w, tile_h):
        super().__init__(file_path, tile_w, tile_h)
        self.vips_image = pyvips.Image.new_from_file(file_path, access='random')

    @property
    def width(self): return self.vips_image.width

    @property
    def height(self): return self.vips_image.height

    def extract_patch(self, tile_coords):
        return self.vips_image.crop(tile_coords)

    def load_thumbnail_rgb(self, max_width=1024):
        # Carica in modalità sequenziale
        stream_image = pyvips.Image.new_from_file(self.file_path, access='sequential')
        thumb = stream_image.thumbnail_image(max_width)

        # IMPORTANTE: Assicuriamoci che sia sRGB (3 canali)
        # Alcune immagini mediche potrebbero essere CMYK o altro
        if thumb.bands != 3:
            thumb = thumb.colourspace('srgb')

        mem = thumb.write_to_memory()

        # Crea array NumPy 3D (Altezza, Larghezza, 3 Canali)
        img_np = np.ndarray(buffer=mem, dtype=np.uint8,
                            shape=[thumb.height, thumb.width, 3])
        return img_np

    def is_patch_valid(self, patch, min_tissue_percent=0.5):
        # Controlla se la patch reale contiene abbastanza tessuto.
        # min_tissue_percent: Percentuale minima di tessuto richiesta

        # Converte in sRGB
        if patch.interpretation != 'srgb':
            patch = patch.colourspace('srgb')

        # Separa i canali
        r, g, b = patch[0], patch[1], patch[2]

        # Calcola la saturazione approssimata: differenza tra canali
        # Il grigio/bianco ha R=G=B (diff quasi 0). Il rosa ha R>G>B (diff alta).
        # Metodo semplice: Se (R-G) > 15 oppure (R-B) > 15 c'è colore (rosa)
        # Il bianco (255,255,255) darà 0. Il tessuto (220, 180, 200) darà > 20.

        diff1 = (r - g).abs()
        diff2 = (r - b).abs()

        # Crea una maschera: Vero se c'è abbastanza differenza di colore (>15)
        mask = (diff1 > 15) | (diff2 > 15)

        # Calcola percentuale e verifica condizione
        return (mask.avg() / 255.0) >= min_tissue_percent
