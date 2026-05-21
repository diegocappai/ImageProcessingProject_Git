import os
import json
from typing import List


class HomeModel:
    """
    Gestisce lo stato e la persistenza dei dati per la schermata Home
    """

    def __init__(self):
        # Definisco il nome del file JSON locale in cui salvare la cronologia dei progetti
        self.file_recenti = "progetti_recenti.json"
        self.progetti_recenti: List[str] = []

        self.carica_recenti()

    def carica_recenti(self):
        """Legge il file JSON dei progetti recenti se esiste"""
        if os.path.exists(self.file_recenti):
            try:
                with open(self.file_recenti, 'r', encoding='utf-8') as f:
                    self.progetti_recenti = json.load(f)
            except Exception as e:
                print(f"[DEBUG - ERROR] Errore nella lettura dei recenti: {e}")
                self.progetti_recenti = []

    def salva_recenti(self):
        """Prende la lista dei percorsi memorizzati in RAM e gli scrive nel JSON"""
        try:
            with open(self.file_recenti, 'w', encoding='utf-8') as f:
                json.dump(self.progetti_recenti, f, indent=4)
        except Exception as e:
            print(f"[DEBUG - ERROR] Errore nel salvataggio dei recenti: {e}")

    def aggiungi_progetto(self, percorso: str):
        """
        Aggiunge un progetto in cima alla lista. Se esiste già, lo sposta in alto
        """
        # Se esiste già lo rimuovo
        if percorso in self.progetti_recenti:
            self.progetti_recenti.remove(percorso)

        self.progetti_recenti.insert(0, percorso)

        # Limite ultimi 10 progetti
        self.progetti_recenti = self.progetti_recenti[:10]

        self.salva_recenti()

    @staticmethod
    def is_progetto_valido(cartella: str) -> bool:
        """
        Verifica l'esistenza della cartella, ispeziona il JSON e controlla che sia del formato esatto (chiavi)
        """
        if not os.path.exists(cartella):
            return False

        try:
            file_json_trovati = [f for f in os.listdir(cartella) if f.endswith('_data.json')]

            # Fallback: se non lo trovo con '_data.json', prendo il primo '.json'
            if not file_json_trovati:
                file_json_trovati = [f for f in os.listdir(cartella) if f.endswith('.json')]
                if not file_json_trovati:
                    return False

            # Ispeziono primo '_data.JSON' trovato nella cartella
            percorso_json = os.path.join(cartella, file_json_trovati[0])
            with open(percorso_json, 'r', encoding='utf-8') as f:
                dati = json.load(f)

            # Il JSON deve obbligatoriamente aprirsi come un dizionario di chiavi-valori
            if not isinstance(dati, dict):
                return False

            # Definisco lo scheletro minimo che il database deve avere per non far crashare l'app
            chiavi_obbligatorie = ["schema_version", "source_type", "patches", "progress"]

            for chiave in chiavi_obbligatorie:
                if chiave not in dati:
                    print(f"[DEBUG - VALIDATION] Fallita: Manca '{chiave}' nel JSON in {cartella}.")
                    return False

            return True

        except json.JSONDecodeError:
            print(f"[DEBUG - ERROR] Il file in {cartella} è un JSON corrotto.")
            return False
        except Exception as e:
            print(f"[DEBUG - ERROR] Errore sconosciuto durante la validazione in {cartella}: {e}")
            return False

    def rimuovi_progetto(self, percorso: str):
        """Rimuove un percorso specifico di un progetto dalla cronologia"""
        if percorso in self.progetti_recenti:
            self.progetti_recenti.remove(percorso)
            self.salva_recenti()