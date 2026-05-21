import os
from PySide6.QtWidgets import QFileDialog, QMessageBox


class HomeController:
    """
    Controller per la pagina Home
    """
    def __init__(self, model, view, on_nuovo_progetto=None, on_carica_progetto=None):
        self.model = model
        self.view = view

        self.on_nuovo_progetto = on_nuovo_progetto
        self.on_carica_progetto = on_carica_progetto

        # Cablaggio dei Segnali
        self.view.richiesta_creazione.connect(self.apri_crea_progetto)
        self.view.richiesta_caricamento.connect(self.sfoglia_e_carica_progetto)
        self.view.progetto_recente_cliccato.connect(self.carica_progetto_esistente)
        self.view.progetto_recente_eliminato.connect(self.gestisci_eliminazione_recente)

        self.aggiorna_view()

    def aggiorna_view(self):
        """
        Interroga il Model per ottenere la lista aggiornata dei progetti recenti e forza la View ad aggiornarsi
        """
        self.view.aggiorna_lista_recenti(self.model.progetti_recenti)

    def apri_crea_progetto(self):
        """
        Invocato quando l'utente richiede di creare un nuovo progetto
        """
        print("[DEBUG - HOME] Ricevuta richiesta per Nuovo Progetto")

        if self.on_nuovo_progetto:
            self.on_nuovo_progetto()
        else:
            raise ValueError("Errore: Callback 'on_nuovo_progetto' non iniettata!")

    def sfoglia_e_carica_progetto(self):
        """
        Apre il File System per permettere all'utente di cercare una cartella di progetto
        """
        cartella = QFileDialog.getExistingDirectory(self.view, "Seleziona cartella del Progetto")

        if cartella:
            self.valida_e_carica(cartella)

    def valida_e_carica(self, cartella):
        """
        Validazione: controllo che la cartella scelta contenga un progetto valido.
        """
        if self.model.is_progetto_valido(cartella):
            print(f"[DEBUG - HOME] Successo: Progetto valido trovato in {cartella}")

            # Mette il progetto in cima alla lista recenti
            self.model.aggiungi_progetto(cartella)
            self.aggiorna_view()

            # Passaggio al MainController
            if self.on_carica_progetto:
                self.on_carica_progetto(cartella)
            else:
                raise ValueError("[ARCHITETTURA] Errore: Callback 'on_carica_progetto' non iniettata!")

        else:
            # Gestione Errore Validazione
            QMessageBox.warning(
                self.view,
                "Errore Caricamento",
                "La cartella selezionata non è un progetto valido.\nAssicurati che contenga un file JSON dei metadati valido."
            )
            # Se la cartella non valida era nella lista dei recenti la rimuoviamo per mantenere pulita la cronologia.
            self.model.rimuovi_progetto(cartella)
            self.aggiorna_view()

    def carica_progetto_esistente(self, percorso):
        """
        Invocato quando l'utente fa doppio click su un elemento della lista dei progetti recenti
        """
        if os.path.exists(percorso):
            self.valida_e_carica(percorso)
        else:
            QMessageBox.critical(
                self.view,
                "Errore di Percorso",
                "La cartella del progetto non esiste più nel computer. Potrebbe essere stata spostata o eliminata."
            )
            self.model.rimuovi_progetto(percorso)
            self.aggiorna_view()

    def aggiungi_nuovo_progetto_ai_recenti(self, percorso_cartella):
        """
        Aggiorna la schermata Home in background subito dopo avere creato un nuovo progetto
        """
        self.model.aggiungi_progetto(percorso_cartella)
        self.aggiorna_view()
        print(f"[HomeController] Sincronizzata nuova cartella ai recenti: {percorso_cartella}")

    def gestisci_eliminazione_recente(self, percorso):
        """
        Rimuove una voce dalla lista dei recenti
        """
        risposta = QMessageBox.question(
            self.view,
            "Conferma Rimozione",
            "Vuoi rimuovere questo progetto dalla cronologia?\n(I file originali sul disco NON verranno cancellati)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if risposta == QMessageBox.StandardButton.Yes:
            self.model.rimuovi_progetto(percorso)
            self.aggiorna_view()