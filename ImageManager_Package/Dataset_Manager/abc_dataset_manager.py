from ImageManager_Package.abc_general_manager import ImageManager
from abc import ABC, abstractmethod
import os
import random

from main_test import input_path


class DatasetManager(ImageManager, ABC):
    def __init__(self, input_path):
        super().__init__(input_path)
        self.patches_list = self.get_items()

    @abstractmethod
    def extract_patches(self, file_name):
        # Dato il nome file resituisce un'oggetto patch
        pass

    def get_items(self):
        valid_ext = ['.jpg', '.jpeg', '.png', '.tif', '.tiff']

        patches_list = [p for p in os.listdir(input_path) if p.lower().endswith(tuple(valid_ext))]
        sorted_patches_list = sorted(patches_list)
        return sorted_patches_list

    def extract_iterator_patches(self, method):
        patch_list = self.get_items()

        # TODO Valutare se necassari random/sequential
        if method == 'random':
            random.shuffle(self.patch_list)
        elif method == 'sequential':
            patch_list = patch_list
        else:
            raise NotImplementedError

        for file_name in patch_list:
            patch = self.extract_patches(file_name)
            # TODO Ragionare su output metodo
            yield patch, file_name
