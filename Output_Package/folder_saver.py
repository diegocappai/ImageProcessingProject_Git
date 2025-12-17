from .abc_output import DatasetSaver
import csv
import os


class FolderDataSetSaver(DatasetSaver):
    def __init__(self, base_path):
        self.output_path = self._calcola_cartella_univoca(base_path)
        super().__init__(self.output_path)

        self.csv_buffer = []
        self.row_header = None

        os.makedirs(self.output_path, exist_ok=True)


    def _calcola_cartella_univoca(self, base_path):
            folder_name = "ImageProcessingResults"
            full_path = os.path.join(base_path, folder_name)

            if not os.path.exists(full_path):
                return full_path

            counter = 1
            while True:
                new_name = f"{folder_name}({counter})"
                new_full_path = os.path.join(base_path, new_name)

                if not os.path.exists(new_full_path):
                    return new_full_path

                counter += 1


    def __enter__(self):
        # Garantire scrittura del file .csv
        return self


    def save_patch_Slide(self, patch, coords_tile, etichetta, ID):
        """ Salva patch e metadati in memoria """

        # Definiamo header file .csv per Patch da WSI
        if self.row_header is None:
            self.row_header = ['Nome patch', 'Coordinate', 'Etichetta', 'ID']

        # Definiamo nome file_patch
        image_filename = f"patch_{coords_tile}.png"

        # Definiamo percorso completo patch (cartella/file_patch)
        full_path = os.path.join(self.output_path, image_filename)

        # Salviamo immagine su disco
        patch.write_to_file(full_path)

        self.csv_buffer.append([image_filename, coords_tile, etichetta, ID])

        print(f"Dati patch salvati correttamente!")

    def save_patch_Dataset(self, file_name, etichetta):
        """ Salva etichetta patch (Dataset) su file .csv"""
        # Definiamo header file .csv per Patch da Dataser
        if self.row_header is None:
            self.row_header = ['Nome patch', 'Etichetta']
        self.csv_buffer.append([file_name, etichetta])
        print(f"Dati patch salvati correttamente!")


    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Crea il file metadati.csv nella stessa cartella delle patch"""

        # Definiamo percorso completo (cartella/file.csv)
        csv_path = os.path.join(self.output_path, 'metadati.csv')

        try:
            with open(csv_path, 'w', newline='') as file:
                writer = csv.writer(file)

                # Definiamo l'header
                if self.row_header:
                    writer.writerow(self.row_header)

                # Scrivi tutti i dati accumulati
                writer.writerows(self.csv_buffer)
            print(f"File CSV salvato correttamente!")
        except Exception as e:
            print(f"Errore durante il salvataggio: {e}")
