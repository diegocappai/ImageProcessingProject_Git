import os
import json
import shutil
from .abc_output import DatasetSaver  # Assicurati che l'import combaci col tuo file


class JsonDatasetSaver(DatasetSaver):
    def __init__(self, temp_dir="./.temp_session", json_filename="annotazioni_dataset.json"):
        self.temp_dir = temp_dir
        self.json_path = os.path.join(self.temp_dir, json_filename)
        self.dati_salvati = {}


        # Crea la cartella principale se non esiste
        os.makedirs(self.output_path, exist_ok=True)

        # Carica lo storico per permettere la ripresa del lavoro
        self._carica_stato()

    def _carica_stato(self):
        """Carica il file JSON se la sessione era già stata iniziata."""
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    self.dati_salvati = json.load(f)
                print(f"Lavoro ripreso: trovate {len(self.dati_salvati)} patch già annotate.")
            except json.JSONDecodeError:
                print("Attenzione: Il file JSON sembra corrotto o vuoto. Inizio da zero.")
                self.dati_salvati = {}
        else:
            print("Nessun salvataggio precedente trovato. Nuova sessione.")
            self.dati_salvati = {}

    def _salva_stato(self):
        """Sovrascrive il file JSON con il dizionario aggiornato."""
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(self.dati_salvati, f, indent=4)

    def is_annotated(self, identifier):
        """
        Metodo extra (non in ABC) molto utile per l'interfaccia.
        Ti permette di chiedere alla classe se una patch è già stata fatta.
        """
        return str(identifier) in self.dati_salvati

    def save_patch_Slide(self, patch, coords_tile, etichetta, ID):
        """ Salva l'immagine e aggiorna il JSON """
        coords_str = str(coords_tile)

        # Prevenzione duplicati nel caso si riprenda un lavoro
        if coords_str in self.dati_salvati:
            print(f"Patch {ID} già presente nel salvataggio. Salto.")
            return

        # Definiamo nome immagine
        image_filename = f"patch_{coords_tile}.png"

        # Definiamo percorso cartella temporanea
        full_path = os.path.join(self.temp_dir, image_filename)

        # Salviamo l'immagine fisica su disco
        patch.write_to_file(full_path)

        # Salviamo i metadati nel nostro dizionario
        self.dati_salvati[coords_str] = {
            "nome_file": image_filename,
            "coordinate": coords_tile,
            "etichetta": etichetta,
            "ID": ID
        }

        # AUTOSAVE: salviamo il JSON sul disco immediatamente
        self._salva_stato()
        print(f"Dati patch {ID} salvati correttamente!")

    def save_patch_Dataset(self, file_name, etichetta):
        """ Salva solo l'etichetta associata al nome del file """
        if file_name in self.dati_salvati:
            print(f"File {file_name} già presente nel salvataggio. Salto.")
            return

        self.dati_salvati[file_name] = {
            "nome_file": file_name,
            "etichetta": etichetta
        }

        self._salva_stato()
        print(f"Etichetta per {file_name} salvata correttamente!")

    def finalize_and_move(self, final_output_path):
        print(f"Spostamento dei dati in corso verso: {final_output_path}...")

        try:
            # Crea la cartella di destinazione se è un percorso nuovo
            os.makedirs(os.path.dirname(final_output_path), exist_ok=True)

            # Sposta la cartella temporanea nel nuovo path
            shutil.move(self.temp_dir, final_output_path)

            # Svuota i riferimenti in memoria
            self.temp_dir = final_output_path
            self.json_path = os.path.join(self.temp_dir, "annotazioni_dataset.json")

            print("Salvataggio finale completato.")
        except Exception as e:
            print(f"Errore durante lo spostamento: {e}")
            print(f"I tuoi dati sono salvati nella cartella temporanea: {self.temp_dir}")


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Garantisce un ultimo salvataggio alla chiusura e notifica
        all'utente se c'è stato un crash.
        """
        self._salva_stato()

        if exc_type:
            print(f"\nSessione interrotta per errore: {exc_val}")
            print(f"Tranquillo, tutti i dati fino a un secondo fa sono salvi in: {self.json_path}")
        else:
            print(f"\nSessione conclusa regolarmente. JSON aggiornato in: {self.json_path}")