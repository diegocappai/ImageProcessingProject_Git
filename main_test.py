from Output_modules import get_writer
from ImageHistolabManager.ImageManager_Package import get_manager


input_path = input("Inserisci percorso immagine: ")
ID = input("Inserisci ID paziente")
tile_w = int(input("Inserisci larghezza patch:"))
tile_h = int(input("Inserisci altezza patch:"))
method_manager = input("Inserisci metodo di elaborazione (PyVips/TiffSlide): ")
manager = get_manager(method_manager, input_path, tile_w, tile_h)

method_show = input("Inserisci metodo di visualizzazione (sequentail/random): ")
patch_generator = manager.extract_iterator_patches(method_show)

output_path = input("Inserisci cartella salvataggio dati: ")
method_output = "Cartella"
writer = get_writer(method_output,output_path)

#counter = 0
with writer:
    for patch, coords in patch_generator:
        if not manager.is_patch_valid(patch, min_tissue_percent=0.5):
            continue

        #etichetta = input("Etichetta: ")
        etichetta = "eticehtta"
        #counter += 1

        writer.save_patch(patch, coords, etichetta, ID)


#print(counter)