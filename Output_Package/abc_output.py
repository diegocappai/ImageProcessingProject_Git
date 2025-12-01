import os
from abc import ABC, abstractmethod


class DatasetSaver(ABC):
    def __init__(self, output_path):
        self.output_path = output_path

        # Crea cartella se non esiste
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

    @abstractmethod
    def save_patch(self, patch, coords_tile, etichetta, ID):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass