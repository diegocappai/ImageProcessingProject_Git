from abc import ABC, abstractmethod
import numpy as np
from PIL import Image


class ImageManager(ABC):
    def __init__(self, file_path, tile_w, tile_h):
        self.file_path = file_path
        self.tile_w = tile_w
        self.tile_h = tile_h
        self.patches_coords = self.get_coords()


    @property
    @abstractmethod
    def width(self):
        pass

    @property
    @abstractmethod
    def height(self):
        pass

    @abstractmethod
    def extract_patch(self, tile_coords):
        # Estrae patch da coordinate
        pass

    # Calcola tutte le coordinate delle patch
    def get_coords(self):
        y_coords = self._calcola_coords_asse(self.height, self.tile_h)
        x_coords = self._calcola_coords_asse(self.width, self.tile_w)
        self.patches_coords = [(x, y, self.tile_w, self.tile_h) for y in y_coords for x in x_coords]
        return self.patches_coords

    # Calcola coordinate patch per asse
    def _calcola_coords_asse(self, total_size, tile_size):
        coords = []
        # Gestisce caso ti patch non multiple di grandezza totale immagine
        if total_size % tile_size != 0:
            num_patches = total_size // tile_size
            start_coord = (total_size - (num_patches * tile_size)) // 2
            for _ in range(num_patches):
                coords.append(start_coord)
                start_coord += tile_size
        else:
            coords = list(range(0, total_size, tile_size))
        return coords

    # Determina le coordinate di una specifica patch
    def find_tile_coords(self, x_coord, y_coord):

        tile_coords = next((t for t in self.patches_coords if
                            t[0] <= x_coord < (t[0] + self.tile_w) and t[1] <= y_coord < (t[1] + self.tile_h)))

        if tile_coords:
            return tile_coords
        else:
            print("Coordinata non trovata!")



    # TODO implementare metodo per scartare patch senza tessuto:
    """
    # Filtrare patch senza tessuto
    def get_tessue_coords(self):
    """
