from Interface_Package.views.setting_new_folder_view import ImpostazioniDialog


class SetupFolderController:
    """
    Controller dedicato esclusivamente all'impostazione di un progetto basato su Cartelle (Dataset di immagini pre-processate)
    """

    def __init__(self, model, view: ImpostazioniDialog):
        self.model = model
        self.view = view

        self.configurazione_salvata = False

        self.collega_segnali()

    def collega_segnali(self):
        """
        Cablaggio segnali
        """
        self.view.accepted.connect(self.salva_configurazione)

    def salva_configurazione(self):
        """
        Estrae le scelte dall'utente e le inietta nel Model
        """
        # Lettura dei widget dalla UI
        percentuale = self.view.combo_perc.currentText()
        ordine = "Sequenziale" if self.view.radio_seq.isChecked() else "Random"

        # Aggiornamento dello stato nel Model
        self.model.imposta_parametri_comuni(percentuale, ordine)

        print(f"[DEBUG - SETUP FOLDER] Utente ha confermato parametri: {percentuale}, {ordine}")

        self.configurazione_salvata = True

    def esegui(self):
        self.view.exec()
        return self.configurazione_salvata