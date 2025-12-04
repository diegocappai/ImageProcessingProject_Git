from abc import ABC, abstractmethod



class ImageManager(ABC):
    def __init__(self, input_path):
        self.input_path = input_path


    @abstractmethod
    def get_items(self):
        # Restituisce lista elementi da processare (patch_dataset/coords_slide)
        pass

    @abstractmethod
    def extract_patch(self, item_identifier):
        # Dato un nome file o coord resituisce oggetto patch
        pass

    @abstractmethod
    def extract_iterator_patches(self, method):
        pass

    def is_patch_valid(self, patch, min_tissue_percent=0.5):
        # Controlla se la patch reale contiene abbastanza tessuto.
        # min_tissue_percent: Percentuale minima di tessuto richiesta

        # Converte in sRGB
        if patch.interpretation != 'srgb':
            patch = patch.colourspace('srgb')

        # Separa i canali
        r, g, b = patch[0], patch[1], patch[2]

        # Calcola la saturazione approssimata: differenza tra canali
        # Il grigio/bianco ha R=G=B (diff quasi 0). Il rosa ha R>G>B (diff alta).
        # Metodo semplice: Se (R-G) > 15 oppure (R-B) > 15 c'è colore (rosa)
        # Il bianco (255,255,255) darà 0. Il tessuto (220, 180, 200) darà > 20.

        diff1 = (r - g).abs()
        diff2 = (r - b).abs()

        # Crea una maschera: Vero se c'è abbastanza differenza di colore (>15)
        mask = (diff1 > 15) | (diff2 > 15)

        # Calcola percentuale e verifica condizione
        return (mask.avg() / 255.0) >= min_tissue_percent
