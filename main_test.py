from Output_Package import get_writer
from ImageManager_Package import get_manager



method_input = input("Inserisci metodo di input (Slide/Dataset):  ")
if method_input == "Dataset":
    folder_path = input("Inserisci percorso cartella Dataset: ")
    manager = get_manager("Cartella",folder_path)
elif method_input == "Slide":
    input_path = input("Inserisci percorso immagine: ")
    ID = input("Inserisci ID paziente")
    tile_w = int(input("Inserisci larghezza patch:"))
    tile_h = int(input("Inserisci altezza patch:"))
    method_manager = input("Inserisci metodo di elaborazione della Slide (PyVips/TiffSlide): ")
    manager = get_manager(method_manager, input_path, tile_w, tile_h)
else:
    raise ValueError("Metodo input non valido")


method_show = input("Inserisci metodo di visualizzazione (sequentail/random): ")

patch_generator = manager.extract_iterator_patches(method_show)
output_path = input("Inserisci cartella salvataggio dati: ")
method_output = "Cartella"

writer = get_writer(method_output,output_path)

with writer:
    if method_input == "Dataset":
        for patch, file_name in patch_generator:
            if not manager.is_patch_valid(patch, min_tissue_percent=0.5):
                continue

            # etichetta = input("Etichetta: ")
            etichetta = "eticehtta"


            writer.save_file_Dataset(file_name, etichetta)

    elif method_input == "WSI":
        for patch, coords in patch_generator:
            if not manager.is_patch_valid(patch, min_tissue_percent=0.5):
                continue

            # etichetta = input("Etichetta: ")
            etichetta = "eticehtta"


            writer.save_patch_WSI(patch, coords, etichetta, ID)

    else:
        raise ValueError
