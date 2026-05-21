from Interface_Package.views.setting_new_folder_view import ImpostazioniDialog


class SetupFolderController:
    """
    Controller dedicato al setup di un nuovo progetto basato su Cartelle (Dataset di immagini pre-processate)
    """

    def __init__(self, model, view: ImpostazioniDialog):
        # Inizializzo Model e View
        self.model = model
        self.view = view

        # Uso un flag per tenere traccia dell'esito dell'operazione di creazione
        self.configurazione_salvata = False

        self.collega_segnali()

    def collega_segnali(self):
        """
        Cablaggio segnali della finestra ai metodi interni
        """
        self.view.accepted.connect(self.salva_configurazione)

    def salva_configurazione(self):
        """
        Estraggo le scelte dall'utente (percetnuale e ordine) e le inietto nel Model
        """
        # Lettura dei valori dalla UI
        percentuale = self.view.combo_perc.currentText()
        ordine = "sequential" if self.view.radio_seq.isChecked() else "random"

        # Aggiornamento dello stato nel Model di Setup
        self.model.imposta_parametri_comuni(percentuale, ordine)

        print(f"[DEBUG - SETUP FOLDER] Utente ha confermato parametri di campionamento: {percentuale}, {ordine}")

        # Segnalo al sistema che la configurazione è andata a buon fine
        self.configurazione_salvata = True

    def esegui(self):
        """
        Blocco l'esecuzione del programma mostrando la finestra di dialogo e restituisco l'esito finale al chiamante.
        """
        self.view.exec()
        return self.configurazione_salvata