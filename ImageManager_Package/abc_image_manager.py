from abc import ABC, abstractmethod
import numpy as np
import cv2
import random



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

    @abstractmethod
    def load_thumbnail_rgb(self, thumbnail_width):
        # Converte in immagine RGB
        pass

    @abstractmethod
    def is_patch_valid(self, patch, min_tissue_percent):
        # Controlla che la patch abbia abbastanza tessuto
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


    # Filtra patch senza tessuto (Filtro Veloce)
    # Valore 0.9 molto alto (provato nei test)
    def get_tissue_coords(self, thumbnail_width=1024, tissue_coverage=0.9):
        # Carica versione ridotta immagine
        thumb_rgb = self.load_thumbnail_rgb(thumbnail_width)

        # Converte immagine da RGB a HSV (Tinta saturazione valore)
        hsv = cv2.cvtColor(thumb_rgb, cv2.COLOR_RGB2HSV)

        # Estrae solo il Canale S = Saturazione, indice 1
        s_channel = hsv[:, :, 1]

        # Utilizza algoritmo OTSU per separare sfondo da primo piano
        # Restituisce 'binary_mask': immagine fatta solo di bianco (Tessuto) e nero (Sfondo)
        _, binary_mask = cv2.threshold(s_channel, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Definisce pennello quadrato di 7x7 pixel
        kernel = np.ones((7, 7), np.uint8)

        # Apllica "Chisura morfologica"
        # Chiude piccoli buchi neri dentro aree bianche di tessuto
        binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel, iterations=1)

        # Calcola quante patch ci stanno nell'imamgine originale
        n_patches_x = self.width // self.tile_w
        n_patches_y = self.height // self.tile_h

        # Controllo di sicurezza se size_immagine<size_tile
        if n_patches_x == 0 or n_patches_y == 0: return []

        # Resize maschera binaria affinchè diventi grande esattamente come la griglia delle patch
        mini_mask = cv2.resize(binary_mask, (n_patches_x, n_patches_y), interpolation=cv2.INTER_AREA) / 255.0

        # Trova coordinate nella mini-griglia dove la percetnuale di tessuto è maggiore o uguale a tissue_coverage
        valid_indices = np.argwhere(mini_mask >= tissue_coverage)

        valid_coords = []

        # Itera su tutti gli indici trovati
        for row, col in valid_indices:
            # Converte indice griglia in pixel immagine reale
            real_x = col * self.tile_w
            real_y = row * self.tile_h
            # Aggiunge a lista finale
            valid_coords.append((real_x, real_y, self.tile_w, self.tile_h))

        # --- DEBUG: SALVATAGGIO MASCHERA PER CONTROLLO ---
        cv2.imwrite("debug_mask_tessuto.jpg", binary_mask)

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



