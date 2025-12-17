from Utils.set_pyvips import setup_vips
import pyvips
import os

from .abc_dataset_manager import DatasetManager


class VipsDatasetManager(DatasetManager):
    def __init__(self, input_path):
        super().__init__(input_path)
        self.patches_list = self.get_items()


    def extract_patches(self, file_name):
        full_path = os.path.join(self.input_path, file_name)
        image = pyvips.Image.new_from_file(full_path)

        return image
