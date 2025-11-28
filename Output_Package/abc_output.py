from abc import ABC, abstractmethod


class DatasetSaver(ABC):
    @abstractmethod
    def save_patch(self, patch, coords_tile, etichetta, ID):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass