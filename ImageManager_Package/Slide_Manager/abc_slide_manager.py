from abc import ABC, abstractmethod
from ImageManager_Package.abc_general_manager import ImageManager
import numpy as np
import cv2
import math


class SlideManager(ImageManager, ABC):
    """
    Classe Astratta per la gestione di Whole Slide Images
    """

    def __init__(self, input_path, tile_w, tile_h):
        super().__init__(input_path)
        self.tile_w = tile_w
        self.tile_h = tile_h

        self.patches_coords = []

    # ==========================================
    # METODI ASTRATTI
    # ==========================================
    @property
    @abstractmethod
    def width(self):
        """Restituisce la larghezza massima in pixel dell'immagine sorgente"""
        pass

    @property
    @abstractmethod
    def height(self):
        """Restituisce l'altezza massima in pixel dell'immagine sorgente"""
        pass

    @abstractmethod
    def extract_patch(self, tile_coords):
        """Estrae l'immagine reale data una coordinata (x, y, w, h)"""
        pass

    @abstractmethod
    def load_thumbnail_rgb(self, thumbnail_width):
        """Restituisce un'anteprima in formato nativo della libreria"""
        pass

    @abstractmethod
    def load_thumbnail_numpy(self, manager_thumb):
        """Converte l'anteprima nativa in un array NumPy"""
        pass

    # ==========================================
    # METODI CONCRETI
    # ==========================================
    def get_coords(self):
        """Genera la lista completa di tutte le possibili coordinate della griglia"""
        y_coords = self._calcola_coords_asse(self.height, self.tile_h)
        x_coords = self._calcola_coords_asse(self.width, self.tile_w)

        # Generatore di lista per combinare asse X e Y
        self.patches_coords = [(x, y, self.tile_w, self.tile_h) for y in y_coords for x in x_coords]
        return self.patches_coords

    def get_items(self):
        """
        Restituisce coordinate
        """
        return self.get_coords()

    def _calcola_coords_asse(self, total_size, tile_size):
        """
        Calcola i punti di inizio di ogni patch lungo un asse (X o Y)
        """
        if tile_size <= 0 or total_size <= 0:
            return []

        # Calcoliamo quante patch intere entrano nell'asse
        num_patches = math.ceil(total_size / tile_size)

        # Generiamo la lista di partenza
        coords = [i * tile_size for i in range(num_patches)]
        return coords

    def get_tissue_coords(self, target_dim=1024, tissue_coverage=0.3):
        """
        Algoritmo di segmentazione del tessuto (Otsu Thresholding su spazio HSV):
        Analizza un'anteprima dell'immagine e proietta i risultati sulla scala reale
        per scartare i riquadri contenenti solo sfondo (vetrino vuoto)
        """
        # --- PREPARAZIONE ANTEPRIMA ---
        # Lavoriamo su una miniatura
        thumb_manager = self.load_thumbnail_rgb(target_dim)
        thumb_array = self.load_thumbnail_numpy(thumb_manager)

        # --- SEGMENTAZIONE TESSUTO ---
        # Converte da RGB (Rosso, Verde, Blu) a HSV (Tonalità, Saturazione, Valore)
        # Lo sfondo del vetrino è bianco/grigio (bassissima saturazione), mentre il tessuto è viola/rosa (alta saturazione)
        hsv = cv2.cvtColor(thumb_array, cv2.COLOR_RGB2HSV)

        # Estraiamo solo il canale della Saturazione
        s_channel = hsv[:, :, 1]

        # Applica l'algoritmo di Otsu: calcola statisticamente la soglia matematica perfetta per dividere i pixel in due classi (sfondo vs tessuto)
        _, binary_mask = cv2.threshold(s_channel, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Operazione morfologica di "Chiusura": Dilata e poi erode la maschera per riempire piccoli buchi vuoti all'interno del tessuto cellulare
        kernel = np.ones((5, 5), np.uint8)
        binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        # --- CREAZIONE GRIGLIA VIRTUALE ---
        # Patch che compongono la griglia gigante reale
        n_patches_x = math.ceil(self.width / self.tile_w)
        n_patches_y = math.ceil(self.height / self.tile_h)

        if n_patches_x == 0 or n_patches_y == 0:
            return []

        # --- MAPPATURA MASCHERA -> GRIGLIA ---
        # Ridimensioniamo la maschera binaria di Otsu affinché la sua risoluzione coincida esattamente con il numero di patch della griglia.
        # (1 pixel della 'mini_mask' rappresenta 1 intera patch reale)
        # cv2.INTER_AREA fa una media dei pixel (calcolando così la percentuale di copertura)
        mini_mask = cv2.resize(binary_mask, (n_patches_x, n_patches_y), interpolation=cv2.INTER_AREA)

        # Normalizziamo i valori da [0, 255] a [0.0, 1.0] (percentuale)
        mini_mask = mini_mask / 255.0

        # --- FILTRAGGIO E PROIEZIONE ---
        # Conserviamo solo gli indici pixel la cui percentuale di tessuto supera la soglia
        valid_indices = np.argwhere(mini_mask >= tissue_coverage)
        valid_coords = []

        for row, col in valid_indices:
            # Proiettiamo l'indice del pixel della mini-maschera sulla scala gigante
            real_x = int(col * self.tile_w)
            real_y = int(row * self.tile_h)
            valid_coords.append((real_x, real_y, self.tile_w, self.tile_h))

        print(f"[SlideManager] Filtro Otsu applicato. Trovate {len(valid_coords)} patch con tessuto utile.")
        return valid_coords