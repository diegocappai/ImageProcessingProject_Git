from abc import ABC, abstractmethod
from ImageManager_Package.abc_general_manager import ImageManager
import numpy as np
import cv2
import random



class SlideManager(ImageManager, ABC):
    def __init__(self, input_path, tile_w, tile_h):
        super().__init__(input_path)
        self.tile_w = tile_w
        self.tile_h = tile_h
        if self.tile_w > 0 and self.tile_h > 0:
            self.patches_coords = self.get_coords()
        else:
            self.patches_coords = []


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

    @abstractmethod
    def load_thumbnail_rgb(self, thumbnail_width):
        # Converte in immagine RGB
        pass

    @abstractmethod
    def load_thumbnail_numpy(self, manager_thumb):
        pass

    # Calcola tutte le coordinate delle patch
    def get_coords(self):
        y_coords = self._calcola_coords_asse(self.height, self.tile_h)
        x_coords = self._calcola_coords_asse(self.width, self.tile_w)
        self.patches_coords = [(x, y, self.tile_w, self.tile_h) for y in y_coords for x in x_coords]
        return self.patches_coords

    # TODO ragionare se scelta migliore o evitabile
    def get_items(self):
        return self.get_coords()

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


    # Filtra patch senza tessuto (Filtro Veloce)
    def get_tissue_coords(self, target_dim=1024, tissue_coverage=0.1):
        # --- PREPARAZIONE ANTEPRIMA ---
        # Carica thumbnail (RGB) dell'immagine
        thumb_manager = self.load_thumbnail_rgb(target_dim)
        # Converte l'oggetto pyvips in un array NumPy per poter usare OpenCV
        thumb_array = self.load_thumbnail_numpy(thumb_manager)

        # --- SEGMENTAZIONE TESSUTO ---
        # Converte l'immagine da RGB a HVS
        hsv = cv2.cvtColor(thumb_array, cv2.COLOR_RGB2HSV)

        # Prende il canale S (Saturazione)
        s_channel = hsv[:, :, 1]

        # Applica la soglia di Otsu: un algoritmo che trova automaticamente il punto di sperazione tra pixel "chiari" e "scuri"
        _, binary_mask = cv2.threshold(s_channel, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Chiusura buchi all'interno del tessuto e unione zone frammentate
        kernel = np.ones((5, 5), np.uint8)
        binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        # --- CREAZIONE GRIGLIA VIRTUALE ---
        # Calcola numero patch nell'immagine reale a piena risoluzione
        n_patches_x = self.width // self.tile_w
        n_patches_y = self.height // self.tile_h

        if n_patches_x == 0 or n_patches_y == 0: return []

        # --- MAPPATURA MASCHERA -> GRIGLIA ---
        # Resize maschera in modo che ogni pixel corrisponda a una patch della griglia
        mini_mask = cv2.resize(binary_mask, (n_patches_x, n_patches_y), interpolation=cv2.INTER_NEAREST)

        # Normalizza i valori da [0, 255] a [0, 1]
        mini_mask = mini_mask / 255.0

        # --- FILTRAGGIO E CONVERSIONE COORDINATE ---
        # Trova gli indici dove la percentual di tessuto è superiore alla soglia
        valid_indices = np.argwhere(mini_mask >= tissue_coverage)
        valid_coords = []

        for row, col in valid_indices:
            # Trasforma le coordinate della "mini-maschera" nelle coordinate reali
            real_x = int(col * self.tile_w)
            real_y = int(row * self.tile_h)
            valid_coords.append((real_x, real_y, self.tile_w, self.tile_h))

        print(f"DEBUG: Generate {len(valid_coords)} coordinate valide.")
        return valid_coords


    def extract_iterator_patches(self, method):
        # Ottieni tutte le coordinate valide
        coords = self.get_tissue_coords()

        if method == "random":
            # Mescola coordinate
            random.shuffle(coords)
        elif method == "sequential":
            coords = coords
        else:
            raise ValueError("Method non valido")

        for (x, y, w, h) in coords:
            patch = self.extract_patch((x, y, w, h))
            yield patch, (x, y, w, h)



