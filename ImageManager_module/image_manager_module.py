import numpy as np
from PIL import Image

class Immagine:
    def __init__(self, image_path):
        self.image_obj = Image.open(image_path)
        #TODO se immagine molto grande può dare problemi (progettare versione successiva)

        self.size = self.image_obj.size #restituisce una tupla (width, height)

        self.patches = [] #le patch non dovranno essere memorizzate nella versione finale
        self.patches_coords = [] #lista coordinate sup-SX della patch

        #Da implementare:
        #self.IDpaziente
        #self.etichetta_patologia
        #self.grado_patologia

    #metodo divide in patch
    def create_patches(self, tile_w, tile_h):
        w, h = self.original_size


        # Determina coordinate di partenza per y
        y_coords = list(range(0, h, tile_h))
        if h % tile_h != 0:
            y_coords.append(h - tile_h)
        y_coords = sorted(list(set(y_coords)))  # rimuove duplicati e ordina

        # Determina coordinate di partenza per x
        x_coords = list(range(0, w, tile_w))
        if w % tile_w != 0:
            x_coords.append(w - tile_w)
        x_coords = sorted(list(set(x_coords)))

        #TODO lista coords unica: [(x1, y1), (x2, y2), ..., (xn, yn)]
        #TODO end create_patches -> estrazione riservata a un altro modulo che chiama la singola patch

        self.patches_coords = []


        for y in y_coords:
            for x in x_coords:
                box = (x, y, x + tile_w, y + tile_h)

                # Se box si estende oltre (w, h) il crop ferma automaticamente al bordo dell'immagine
                # creando patch parziali
                tile = self.image_obj.crop(box)

                # converte patch in array NumPy
                self.patches.append(np.array(tile))
                self.patches_coords.append((x, y))

        return self.patches, self.patches_coords




## PROVA FUNZIONAMENTO CLASSE E METODI ##
"""
immagine1 = Immagine()

immagine1.crea_immagine()
tile_w=int(input("Inserisci larghezza patch:"))
tile_h=int(input("Inserisci altezza patch:"))

immagine1.create_patches(tile_w, tile_h)

immagine1.reconstruct_image()"""
