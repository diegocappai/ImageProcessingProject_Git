from Interface_Package.views.setting_new_slide_view import ImpostazioniSlideDialog


class SetupSlideController:
    """
    Controller per il Setup dei progetti Whole Slide Image (WSI)
    """

    def __init__(self, model, view: ImpostazioniSlideDialog):
        self.model = model
        self.view = view
        self.configurazione_salvata = False

        self.collega_segnali()
        self._inizializza_vista_slide()

    def collega_segnali(self):
        """Mappa gli eventi causati dall'utente"""
        self.view.aggiorna_grandezza_patch.connect(self.gestisci_cambio_grandezza)
        self.view.accepted.connect(self.salva_configurazione)
        self.view.griglia_toggled.connect(self.gestisci_visibilita_griglia)

    def _inizializza_vista_slide(self):
        """Carica l'immagine iniziale a bassa risoluzione (Livello più alto della piramide)"""
        print(f"[DEBUG - SETUP SLIDE] Caricamento anteprima da: {self.model.percorso_slide}")

        self.view.roi_view.imposta_motore_immagini(self.model.manager)

        # Il Model deve sapere le dimensioni originali per i calcoli successivi
        self.model.larghezza_originale = self.model.manager.width
        self.model.altezza_originale = self.model.manager.height

        valore_iniziale = self.view.get_grandezza_patch()
        self.gestisci_cambio_grandezza(valore_iniziale)

    def gestisci_visibilita_griglia(self, stato_checked):
        self.view.set_griglia_visiva(stato_checked)

    def gestisci_cambio_grandezza(self, nuova_grandezza):
        """Aggiorna il disegno della griglia verde quando l'utente cambia risoluzione"""
        self.model.imposta_grandezza_patch(nuova_grandezza)

        totale_teorico = self.model.calcola_patch_totali()
        self.view.aggiorna_totale_patch(f"{totale_teorico} (Max Teorico)")

        self.view.orig_w = self.model.larghezza_originale
        self.view.orig_h = self.model.altezza_originale

        w_scena, h_scena = self.view.get_dimensioni_miniatura()
        self.view.thumb_w = w_scena
        self.view.thumb_h = h_scena

        self.view.aggiorna_griglia_visiva(nuova_grandezza, 0, 0)

    def salva_configurazione(self):
        """
        Motore di Mappatura Spaziale:
        Traspone le ROI disegnate dall'utente sulla miniatura in coordinate
        assolute basate sulle dimensioni della vera Whole Slide Image
        """
        grandezza_patch = self.view.get_grandezza_patch()

        # Aggiornamento Model
        self.model.roi_list = []
        self.model.imposta_grandezza_patch(grandezza_patch)

        if hasattr(self.model, 'imposta_parametri_comuni'):
            self.model.imposta_parametri_comuni("100%", "Sequenziale")

        print("[DEBUG - SETUP SLIDE] Configurazione base salvata. Pronti per la Dashboard.")
        self.configurazione_salvata = True



        self.configurazione_salvata = True

    def esegui(self):
        self.view.exec()
        return self.configurazione_salvata