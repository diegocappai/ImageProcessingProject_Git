import os
import platform
from dotenv import load_dotenv

load_dotenv()


# Percorso della cartella bin di VipsE
#VIPSHOME = r'C:\Path\vips\vips-dev-8.17\bin'



def setup_vips():
    # Configura l'ambiente per permettere a pyvips di trovare le DLL su Windows
    if platform.system() != "Windows":
        return

    vips_home = os.getenv("VIPS_HOME", r'C:\vips\vips-dev-8.17\bin')

    if os.path.exists(vips_home):
        os.environ['PATH'] = vips_home + ';' + os.environ['PATH']

        if hasattr(os, 'add_dll_directory'):
            try:
                os.add_dll_directory(vips_home)
            except Exception as e:
                    print(f"Errore caricamento DLL directory: {e}")
    else:
        print(f"ATTENZIONE: Percorso Vips non trovato: {vips_home}")


setup_vips()
