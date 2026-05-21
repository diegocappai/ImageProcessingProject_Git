from PySide6.QtWidgets import QMessageBox
import random

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
        self.view.richiesta_cambio_campionamento.connect(self.gestisci_cambio_campionamento)

    def aggiorna_vista(self):
        """
        Prendo l'ultimo stato noto del JSON dal Model e lo inietta nella View
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
        """
        Controllo di sicurezza pre sessione di etichettatura
        """
        case_id = self.model.data.get('case_id', 'Sconosciuto')
        print(f"[DEBUG - DASHBOARD] Avvio sessione di etichettatura per il progetto: {case_id}")

        patch_totali_campionate = sum(1 for p in self.model.data.get("patches", []) if p.get("is_sampled"))

        if patch_totali_campionate == 0:
            QMessageBox.warning(
                self.view,
                "Nessuna Patch Campionata",
                "Impossibile procedere.\n\n"
                "Non ci sono patch selezionate per l'etichettatura. Controlla la percentuale di campionamento impostata."
            )
            return

        if self.naviga_a_etichettatura:
            self.naviga_a_etichettatura()
        else:
            raise ValueError("[ARCHITETTURA] Errore: Callback 'naviga_a_etichettatura' non iniettata!")

    def gestisci_cambio_campionamento(self, nuova_perc: int):
        """
        Ricalcola il campionamento in base alla nuova percentuale di campionamento.
        Blocco di sicurezza se l'utente scende sotto la soglia delle patch che ha già lavorato o visualizzato
        per non corrompere il database.
        """
        data = self.model.data
        patch_list = data.get("patches", [])

        if not patch_list:
            return

        totale_assoluto = len(patch_list)

        nuovo_target = max(1, int(totale_assoluto * (nuova_perc / 100.0))) if totale_assoluto > 0 else 0

        # Identifichiamo le patch intoccabili (già etichettate o mostrate a schermo)
        intoccabili = [p for p in patch_list if p.get("status") in ["labeled", "skipped"] or p.get("shown_to_user")]
        quante_intoccabili = len(intoccabili)

        # =====================================================================
        # CONTROLLO LIMITI DI SICUREZZA
        # =====================================================================
        if nuovo_target < quante_intoccabili:
            # Calcolo matematicamente la percentuale minima ammissibile
            perc_minima_richiesta = int((quante_intoccabili / totale_assoluto) * 100)
            if (quante_intoccabili * 100) % totale_assoluto != 0:
                perc_minima_richiesta += 1

            QMessageBox.warning(
                self.view,
                "Operazione Annullata",
                f"Impossibile ridurre il campionamento al {nuova_perc}%.\n\n"
                f"Hai già lavorato o visualizzato {quante_intoccabili} patch su {totale_assoluto}.\n"
                f"Per non perdere il lavoro svolto, la percentuale minima consentita attuale è del {perc_minima_richiesta}%."
            )

            # Blocco i segnali per evitare un loop infinito quando imposto il nuovo valore nello SpinBox
            self.view.spin_perc.blockSignals(True)
            self.view.spin_perc.setValue(perc_minima_richiesta)
            self.view.spin_perc.blockSignals(False)

            self.aggiorna_vista()
            return


        attuali_campionate = [p for p in patch_list if p.get("is_sampled")]
        quante_campionate_ora = len(attuali_campionate)
        ordine = data.get("sampling_config", {}).get("ordine", "Sequenziale")

        # CASO AUMENTO CAMPIONAMENTO
        if nuovo_target > quante_campionate_ora:
            candidati_da_aggiungere = [p for p in patch_list if not p.get("is_sampled")]
            quante_da_aggiungere = min(nuovo_target - quante_campionate_ora, len(candidati_da_aggiungere))

            if quante_da_aggiungere > 0:
                if ordine == "Random":
                    da_attivare = random.sample(candidati_da_aggiungere, quante_da_aggiungere)
                else:
                    da_attivare = candidati_da_aggiungere[:quante_da_aggiungere]

                for p in da_attivare:
                    p["is_sampled"] = True
                print(f"[DEBUG] Aggiunte {quante_da_aggiungere} nuove patch al campionamento.")

        # CASO RIDUZIONE CAMPIONAMENTO
        elif nuovo_target < quante_campionate_ora:
            candidati_da_rimuovere = [p for p in attuali_campionate if p not in intoccabili]
            quante_da_rimuovere = min(quante_campionate_ora - nuovo_target, len(candidati_da_rimuovere))

            if quante_da_rimuovere > 0:
                if ordine == "Random":
                    da_disattivare = random.sample(candidati_da_rimuovere, quante_da_rimuovere)
                else:
                    da_disattivare = candidati_da_rimuovere[-quante_da_rimuovere:]

                for p in da_disattivare:
                    p["is_sampled"] = False
                print(f"[DEBUG] Rimosse {quante_da_rimuovere} patch non lavorate in eccedenza.")

        # Scrittura mpdifiche nel JSON e salvataggio
        if "sampling_config" not in data:
            data["sampling_config"] = {}
        data["sampling_config"]["sampling_percentage"] = nuova_perc

        if hasattr(self.model, "salva_su_disco"):
            self.model.salva_su_disco()

        self.aggiorna_vista()

    def gestisci_ritorno_home(self):
        """
        Uscita dalla Dashboard e ritorno alla schermata Home
        """
        print("[DEBUG - DASHBOARD] Ritorno alla Home richiesto dall'utente.")

        if self.naviga_a_home:
            self.naviga_a_home()
        else:
            raise ValueError("Errore: Callback 'naviga_a_home' non iniettata!")