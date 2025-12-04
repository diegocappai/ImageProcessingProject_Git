import os
from abc import ABC, abstractmethod


class DatasetSaver(ABC):
    def __init__(self, output_path):
        self.output_path = output_path


    @abstractmethod
    def save_patch_Slide(self, patch, coords_tile, etichetta, ID):
        pass

    @abstractmethod
    def save_patch_Dataset(self, file_name, etichetta):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass