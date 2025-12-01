import os


# Percorso della cartella bin di VipsE
VIPSHOME = r'C:\Path\vips\vips-dev-8.17\bin'


def setup_vips():
    # Configura l'ambiente per permettere a pyvips di trovare le DLL su Windows
    if os.path.exists(VIPSHOME):
        # Aggiunge al PATH
        os.environ['PATH'] = VIPSHOME + ';' + os.environ['PATH']

        # Passaggio per Python 3.8+
        if hasattr(os, 'add_dll_directory'):
            try:
                os.add_dll_directory(VIPSHOME)
            except Exception as e:
                    print(f"Errore caricamento DLL directory: {e}")
    else:
        print(f"ATTENZIONE: Percorso Vips non trovato: {VIPSHOME}")


# Esegue la configurazione appena questo file viene importato
setup_vips()
