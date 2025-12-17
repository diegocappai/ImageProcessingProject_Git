from .abc_slide_manager import SlideManager
from Utils.set_pyvips import setup_vips
import pyvips
import numpy as np


class VipsSlideManager(SlideManager):
    def __init__(self, input_path, tile_w, tile_h):
        super().__init__(input_path, tile_w, tile_h)
        self.vips_image = pyvips.Image.new_from_file(input_path, access='random')

    @property
    def width(self): return self.vips_image.width

    @property
    def height(self): return self.vips_image.height

    def extract_patch(self, tile_coords):
        return self.vips_image.crop(tile_coords)

    def load_thumbnail_rgb(self, max_width=1024):
        # Carica in modalità sequenziale
        stream_image = pyvips.Image.new_from_file(self.input_path, access='sequential')
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


