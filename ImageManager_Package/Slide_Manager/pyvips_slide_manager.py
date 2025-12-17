from .abc_slide_manager import SlideManager
from Utils.set_pyvips import setup_vips
import pyvips
import numpy as np


class VipsSlideManager(SlideManager):
    def __init__(self, input_path, tile_w, tile_h):
        self.vips_image = pyvips.Image.new_from_file(input_path, access='random')
        super().__init__(input_path, tile_w, tile_h)


    @property
    def width(self): return self.vips_image.width

    @property
    def height(self): return self.vips_image.height

    def extract_patch(self, tile_coords):
        return self.vips_image.crop(tile_coords)

    def load_thumbnail_rgb(self, max_width=1024):
        best_level = 0
        loaded_thumb = None

        # --- A. RILEVAMENTO LIVELLI (Logica Pyramid) ---
        if "openslide.level-count" in self.vips_image.get_fields():
            level_count = int(self.vips_image.get("openslide.level-count"))

            for i in range(level_count):
                w = int(self.vips_image.get(f"openslide.level[{i}].width"))

                # Cerca un livello gestibile (< 5000px) ma non troppo piccolo
                if w < 5000:
                    best_level = i
                    if w <= max_width * 2:  # Trovato un candidato ottimo
                        break

            # Carica SOLO il livello specifico
            loaded_thumb = pyvips.Image.new_from_file(self.input_path, level=best_level)
        else:
            # Fallback per immagini normali (JPG/PNG)
            loaded_thumb = self.vips_image

        # --- B. RIDIMENSIONAMENTO FINALE ---
        if loaded_thumb.width > max_width:
            loaded_thumb = loaded_thumb.thumbnail_image(max_width)

        # --- C. NORMALIZZAZIONE (sRGB + No Alpha) ---
        if loaded_thumb.bands > 3:
            loaded_thumb = loaded_thumb.extract_band(0, n=3)
        if loaded_thumb.interpretation != 'srgb':
            loaded_thumb = loaded_thumb.colourspace('srgb')

        return loaded_thumb.cast("uchar")

