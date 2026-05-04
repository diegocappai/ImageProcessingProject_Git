from ImageManager_Package import get_manager


class EtichettaturaController:
    """
    Controller per l'interfaccia di annotazione
    """

    def __init__(self, project_manager, view):
        self.model = project_manager
        self.view = view

        # =============================================================
        # DIPENDENZE
        # =============================================================
        self.naviga_alla_dashboard = None

        # =============================================================
        # STATO DEL CONTROLLER
        # =============================================================
        self.lista_patch = self.model.data.get("patches", [])

        # Filtriamo in memoria solo le patch eleggibili per la revisione
        self.patches_da_mostrare = [p for p in self.lista_patch if p.get("is_sampled", False)]
        self.indice_corrente = 0

        # Posiziona l'utente sull'ultima patch non ancora vista
        self.trova_punto_di_ripresa()

        # Inizializza il lettore di immagini
        self._inizializza_image_manager()

        self.collega_segnali()
        self.aggiorna_vista()

    def _inizializza_image_manager(self):
        """
        Legge i metadati dal JSON e crea il Manager di immagini appropriato
        """
        percorso_base = self.model.data.get("source_path", "")
        tipo_sorgente = self.model.data.get("source_type", "")

        if not percorso_base:
            print("[DEBUG - ERROR] Etichettatura: Percorso sorgente mancante nel JSON.")
            return

        # Supporto retrocompatibile
        if tipo_sorgente in ["patch_folder", "Folder"]:
            self.image_manager = get_manager(method='Folder', input_path=percorso_base)
            print("[DEBUG] Inizializzato manager Folder per etichettatura")

        elif tipo_sorgente in ["whole_image", "Slide"]:
            dimensione_patch = self.model.data.get("patching_config", {}).get("patch_size", 512)
            self.image_manager = get_manager(
                method='Slide',
                input_path=percorso_base,
                tile_w=dimensione_patch,
                tile_h=dimensione_patch
            )
            print("[DEBUG] Inizializzato manager Slide (WSI) per l'etichettatura.")

    def collega_segnali(self):
        """Collega gli eventi generati dall'utente ai metodi del Controller"""
        self.view.richiesta_indietro.connect(self.vai_indietro)
        self.view.richiesta_avanti.connect(self.vai_avanti)
        self.view.btn_salva.clicked.connect(self.salva_ed_esci)

        # Intercetta il click su qualsiasi RadioButton che rappresenta un'etichetta
        self.view.etichetta_selezionata.connect(self.gestisci_etichettatura)

    # ==========================================
    # LOGICA DI NAVIGAZIONE E STATO
    # ==========================================
    def trova_punto_di_ripresa(self):
        """
        Analizza la lista filtrata e imposta l'indice sulla prima patch che non ha il flag 'shown_to_user = True'
        """
        for i, patch in enumerate(self.patches_da_mostrare):
            if not patch.get("shown_to_user", False):
                self.indice_corrente = i
                return
        self.indice_corrente = 0

    def ottieni_patch_corrente(self):
        """Restituisce il dizionario della patch mostrata a schermo"""
        if not self.patches_da_mostrare:
            return None
        return self.patches_da_mostrare[self.indice_corrente]

    def aggiorna_vista(self):
        """
        Sincronizza l'Interfaccia Grafica con lo stato del Model in corrispondenza della patch corrente
        """
        patch_corrente = self.ottieni_patch_corrente()
        if not patch_corrente:
            return

        totale_da_mostrare = len(self.patches_da_mostrare)

        self.view.radio_rivedere.blockSignals(True)
        self.view.text_note.blockSignals(True)
        self.view.gruppo_etichette.blockSignals(True)

        self.view.label_counter.setText(f"{self.indice_corrente + 1} di {totale_da_mostrare}")
        self.view.aggiorna_stato_navigazione(self.indice_corrente, totale_da_mostrare)

        note_salvate = patch_corrente.get("annotation_text", "")
        self.view.text_note.setPlainText(note_salvate if note_salvate else "")

        da_rivedere = patch_corrente.get("selected_for_review", False)
        self.view.radio_rivedere.setChecked(da_rivedere)

        # Ripristino visivo dell'etichetta (se già assegnata)
        etichetta_salvata = patch_corrente.get("label")
        self.view.gruppo_etichette.setExclusive(False)
        for btn in self.view.gruppo_etichette.buttons():
            btn.setChecked(btn.text() == etichetta_salvata)
        self.view.gruppo_etichette.setExclusive(True)

        self.view.radio_rivedere.blockSignals(False)
        self.view.text_note.blockSignals(False)
        self.view.gruppo_etichette.blockSignals(False)

        # Estrazione dell'immagine
        try:
            if self.model.data.get("source_type") in ["patch_folder", "Folder"]:
                nome_file = patch_corrente.get("file_name")
                vips_image = self.image_manager.extract_patch(nome_file)
            else:
                x = patch_corrente.get("x")
                y = patch_corrente.get("y")
                w = patch_corrente.get("width")
                h = patch_corrente.get("height")

                if x is None or y is None or w is None or h is None:
                    raise ValueError(f"Coordinate mancanti per la patch {patch_corrente.get('patch_id')}")

                vips_image = self.image_manager.extract_patch((int(x), int(y), int(w), int(h)))

            # Rendering: Converte da Vips Image a Qt Pixmap
            from Utils.pyvips_to_qpixmap import pyvips_to_qpixmap
            pixmap = pyvips_to_qpixmap(vips_image)
            self.view.carica_immagine(pixmap)

        except Exception as e:
            print(f"[DEBUG - ERROR] Estrazione/Conversione Immagine fallita: {e}")
            return

        # Registriamo nel Model che l'utente ha visto questa patch
        patch_corrente["shown_to_user"] = True

    def salva_patch_attuale(self):
        """
        Legge lo stato attuale della User Interface e sovrascrive i dati della patch nel Model
        """
        patch = self.ottieni_patch_corrente()
        if not patch:
            return

        # Recupero Dati
        note_da_ui = self.view.text_note.toPlainText()
        da_rivedere_da_ui = self.view.radio_rivedere.isChecked()

        label_selezionata = None
        bottone_premuto = self.view.gruppo_etichette.checkedButton()
        if bottone_premuto:
            label_selezionata = bottone_premuto.text()

        # Aggiornamento tramite ProjectManager
        self.model.aggiorna_patch(
            patch_id=patch["patch_id"],
            label=label_selezionata,
            note=note_da_ui,
            da_rivedere=da_rivedere_da_ui
        )
        print(f"[DEBUG] Dati patch '{patch['patch_id']}' aggiornati su disco.")

    # ==========================================
    # AZIONI UTENTE
    # ==========================================

    def vai_avanti(self):
        """Salva lo stato corrente e avanza l'indice"""
        self.salva_patch_attuale()

        if self.indice_corrente < len(self.patches_da_mostrare) - 1:
            self.indice_corrente += 1
            self.aggiorna_vista()

    def vai_indietro(self):
        """Salva lo stato corrente e arretra l'indice"""
        self.salva_patch_attuale()

        if self.indice_corrente > 0:
            self.indice_corrente -= 1
            self.aggiorna_vista()

    def gestisci_etichettatura(self, nome_etichetta):
        """Slot chiamato al click di un RadioButton (Automatizza l'avanzamento)"""
        if not self.lista_patch:
            return

        print(f"[DEBUG] Selezionata etichetta '{nome_etichetta}', trigger automatico avanti.")
        self.vai_avanti()

    def salva_ed_esci(self):
        """Salva lo stato e naviga verso la Dashboard"""
        self.salva_patch_attuale()

        # Sincronizza eventuali altri metadati pendenti
        self.model.salva_su_disco()
        print("[DEBUG] Progressi salvati. Uscita da Etichettatura.")

        # Routing sicuro al MainController
        if self.naviga_alla_dashboard:
            self.naviga_alla_dashboard()
        else:
            raise ValueError("[ARCHITETTURA] Errore: Callback 'naviga_alla_dashboard' non iniettata!")