import sys
import tiffslide

# --- MONKEY PATCHING ---
sys.modules['openslide'] = tiffslide
from tiffslide import TiffSlide
tiffslide.OpenSlide = TiffSlide
# -----------------------

from histolab.tiler import GridTiler
from histolab.slide import Slide


def create_patch(input_path):
    # Definiamo la cartella RELATIVA (dentro il progetto)
    cartella_output = "./patch"

    slide = Slide(path=input_path, processed_path=cartella_output)

    # Configurazione e Estrazione
    tiler = GridTiler(
        tile_size=(512, 512),
        level=0,
        check_tissue=True,
        pixel_overlap=0,
        suffix=".png"
    )

    tiler.extract(slide)
    print("COMPLETATO!")
    print("Patch salvate nella cartella 'patch'.")

    return cartella_output

