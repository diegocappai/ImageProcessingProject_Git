class ProjectDashboardController:
    """
    Controller per la Dashboard di Progetto
    """

    def __init__(self, project_manager, view):
        self.model = project_manager
        self.view = view

        self.naviga_a_etichettatura = None
        self.naviga_a_home = None

        self._collega_segnali()
        self.aggiorna_vista()

    def _collega_segnali(self):
        """
        Mappa i segnali emessi dalla View
        """
        self.view.richiesta_inizio_etichettatura.connect(self.gestisci_avvio_etichettatura)
        self.view.richiesta_ritorno_home.connect(self.gestisci_ritorno_home)

    def aggiorna_vista(self):
        """
        Estrae l'ultimo stato noto del JSON dal Model e lo inietta nella View
        """
        if not self.model or not self.model.data:
            print("[DEBUG - ERROR] Dashboard: Nessun dato di progetto trovato nel Model.")
            return

        # Passiamo l'intero dizionario JSON alla View
        self.view.display_project(self.model.data)

    # ==========================================
    # GESTIONE AZIONI DELL'UTENTE
    # ==========================================

    def gestisci_avvio_etichettatura(self):
        case_id = self.model.data.get('case_id', 'Sconosciuto')
        print(f"[DEBUG - DASHBOARD] Avvio sessione di etichettatura per il progetto: {case_id}")

        if self.naviga_a_etichettatura:
            self.naviga_a_etichettatura()
        else:
            raise ValueError("[ARCHITETTURA] Errore: Callback 'naviga_a_etichettatura' non iniettata!")

    def gestisci_ritorno_home(self):
        print("[DEBUG - DASHBOARD] Ritorno alla Home richiesto dall'utente.")

        if self.naviga_a_home:
            self.naviga_a_home()
        else:
            raise ValueError("[ARCHITETTURA] Errore: Callback 'naviga_a_home' non iniettata!")