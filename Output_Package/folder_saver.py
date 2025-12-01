from .abc_output import DatasetSaver
import csv
import os


class FolderDataSetSaver(DatasetSaver):
    def __init__(self, output_path):
        super().__init__(output_path)
        self.csv_buffer = []



    def __enter__(self):
        # Garantire scrittura del file .csv
        return self


    def save_patch(self, patch, coords_tile, etichetta, ID):
        """ Salva patch e metadati in memoria """

        # Definiamo nome file_patch
        image_filename = f"patch_{coords_tile}.png"

        # Definiamo percorso completo patch (cartella/file_patch)
        full_path = os.path.join(self.output_path, image_filename)

        # Salviamo immagine su disco
        patch.write_to_file(full_path)

        self.csv_buffer.append([image_filename, coords_tile, etichetta, ID])

        print(f"Dati patch salvati correttamente!")


    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Crea il file metadati.csv nella stessa cartella delle patch"""

        # Definiamo percorso completo (cartella/file.csv)
        csv_path = os.path.join(self.output_path, 'metadati.csv')

        try:
            with open(csv_path, 'w', newline='') as file:
                writer = csv.writer(file)
                # Definiamo l'header
                writer.writerow(['Nome patch', 'Coordinate','Etichetta', 'ID'])
                # Scrivi tutti i dati accumulati
                writer.writerows(self.csv_buffer)
            print(f"File CSV salvato correttamente!")
        except Exception as e:
            print(f"Errore durante il salvataggio: {e}")
