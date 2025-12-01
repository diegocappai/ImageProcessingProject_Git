#import set_pyvips
import pyvips
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
