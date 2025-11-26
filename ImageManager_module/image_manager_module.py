import numpy as np
from PIL import Image

class Immagine:
    def __init__(self, image_path):
        self.image_obj = Image.open(image_path)
        # funzione Image.open() è lazy finché non si utilizzano altre funzioni di manipolazione
        # TODO se immagine molto grande può dare problemi (progettare versione successiva)

        self.size = self.image_obj.size #restituisce una tupla (width, height)

        self.patches = [] #le patch non dovranno essere memorizzate nella versione finale
        self.patches_coords = [] #lista coordinate sup-SX della patch

        #TODO implementare:
        #self.IDpaziente
        #self.etichetta_patologia
        #self.grado_patologia

    #metodo divide in patch
    def create_patches(self, tile_w, tile_h):
        w, h = self.size
        x_coords = []
        y_coords = []


        # Determina coordinate di partenza per y
        # Se altezza patch non è multiplo di altezza immagine
        if h % tile_h != 0:
            num_patches = h // tile_h
            used_size = tile_h * num_patches
            starded_patches = (h - used_size) // 2
            current_start = starded_patches
            for _ in range(num_patches):
                y_coords.append(current_start)
                current_start += tile_h
        else:
            y_coords = list(range(0, h, tile_h))

        # Determina coordinate di partenza per x
        # Se larghezza patch non è multiplo di larghezza immagine
        if w % tile_w != 0:
            num_patches = w // tile_w
            used_size = tile_w * num_patches
            starded_patches = (w - used_size) // 2
            current_start = starded_patches
            for _ in range(num_patches):
                x_coords.append(current_start)
                current_start += tile_h
        else:
            x_coords = list(range(0, w, tile_w))

        # Crea una lista con le coordinate di ogni singola patch
        self.patches_coords = [(x, y) for x in x_coords for y in y_coords]





## PROVA FUNZIONAMENTO CLASSE E METODI ##
"""
immagine1 = Immagine(image_path)

tile_w=int(input("Inserisci larghezza patch:"))
tile_h=int(input("Inserisci altezza patch:"))

immagine1.create_patches(tile_w, tile_h)"""
