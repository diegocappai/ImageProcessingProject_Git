from .abc_output import DatasetSaver
import zipfile
import csv
import io
import os


class ZipDataSetSaver(DatasetSaver):
    def __init__(self, output_path):
        """
        Inizializza il writer e crea le cartelle necessarie.
        :param full_output_path: Percorso completo del file zip (es. 'output/2023/dataset.zip')
        """
        self.output_path = output_path
        self.zip_file = None
        self.csv_buffer = []


        # Estre la directory dal percorso (togliamo un eventuale del file .zip)
        directory = os.path.dirname(self.output_path)

        if directory:
            # Crea la cartella se non esiste
            os.makedirs(directory, exist_ok=True)
            print(f"Verificata/Creata cartella di destinazione: {directory}")


    def __enter__(self):
        # Apre il file zip usando il percorso
        self.zip_file = zipfile.ZipFile(self.output_path, 'w', zipfile.ZIP_DEFLATED)
        return self

    def save_patch(self, patch, coords_tile, etichetta, ID):
        # Salva la patch e l'etichetta nello zip.
        image_filename = f"patch_{coords_tile}.png"

        # Converte l'immagine pyvips in un buffer di byte (PNG)
        image_bytes = patch.write_to_buffer('.png')

        # Scrive l'immagine nello zip
        self.zip_file.writestr(image_filename, image_bytes)

        # Aggiunge al buffer CSV
        self.csv_buffer.append([image_filename, coords_tile, etichetta, ID])


    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.zip_file:
            # Scrittura CSV
            csv_io = io.StringIO()
            writer = csv.writer(csv_io)
            writer.writerow(['Nome patch', 'Coordinate', 'Etichetta', 'ID'])
            writer.writerows(self.csv_buffer)

            self.zip_file.writestr('metadati.csv', csv_io.getvalue())
            self.zip_file.close()
            print(f"Archivio salvato correttamente in: {self.output_path}")