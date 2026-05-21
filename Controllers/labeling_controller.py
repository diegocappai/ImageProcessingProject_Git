import random
import gc
import datetime
from collections import deque

from PySide6.QtWidgets import QMessageBox, QApplication
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, Qt
from PySide6.QtCore import QRect, Qt, QTimer

from ImageManager_Package import get_manager
from Utils.ui_settings import PALETTE_COLORI
from Utils.pyvips_to_qpixmap import pyvips_to_qpixmap


class EtichettaturaController:
    """
    Controller della Sessione di Etichettatura
    """

    def __init__(self, project_manager, view, roi_selezionate=None, patch_selezionate=None):
        # Inizializzo lo stato di abse
        self.model = project_manager
        self.view = view
        self.roi_selezionate = roi_selezionate
        self.patch_selezionate = patch_selezionate
        self.naviga_alla_dashboard = None

        self.patches_da_mostrare = []
        self.indice_corrente = 0
        self.image_manager = None
        self.current_patch_pixmap = None

        self.is_slide_source = self.model.data.get("source_type") in ["whole_image"]

        # Filtro le patch e preparo la sessione
        self._inizializza_sessione()

        # Se ci sono dati validi, continuo con l'inizializzazione
        if self.patches_da_mostrare:
            self.history_queue = deque(maxlen=10)
            self.trova_punto_di_ripresa()
            self._inizializza_image_manager()
            self._ripristina_cronologia_sessione()
            self.collega_segnali()
            self.aggiorna_vista()


    def _inizializza_sessione(self):
        """
        Prepara l'interfaccia assegnando i colori alle classi e filtra l'elenco totale delle patch
        per selezionare solo quelle della sessione
        """
        classi_salvate = self.model.data["labeling_config"]["classes"]

        # Associo ad ogni classe un colore univoco
        color_map_history = {
            classe: PALETTE_COLORI[i % len(PALETTE_COLORI)]
            for i, classe in enumerate(classi_salvate)
        }
        self.view.imposta_etichette_da_json(classi_salvate, color_map_history)

        tutte_le_patch = self.model.data.get("patches", [])
        self.patches_da_mostrare = []

        #  --- Gestione Input da Slide Intera ---
        if self.is_slide_source:
            if self.patch_selezionate:
                # Caso di Campionamento mirato
                self.patches_da_mostrare = [p for p in tutte_le_patch if p.get("patch_id") in self.patch_selezionate]
                self.patches_da_mostrare.sort(key=lambda p: (p.get("y", 0), p.get("x",0)))
            else:
                # Caso Navigazione su ROI
                lista_config_roi = self.model.data.get("sampling_config", {}).get("roi_list", [])
                rois_da_processare = self.roi_selezionate or [r["id"] for r in lista_config_roi]

                for roi_id in rois_da_processare:
                    roi_info = next((r for r in lista_config_roi if r["id"] == roi_id), {})
                    ordine = roi_info.get("show_order", "sequential")

                    patch_della_roi = [p for p in tutte_le_patch if p.get("is_sampled") and p.get("roi_id") == roi_id]
                    if not patch_della_roi:
                        continue

                    # Ordino lista patch
                    patch_della_roi.sort(key=lambda p: (p.get("y", 0), p.get("x", 0)))

                    if ordine.lower() == "random":
                        random.Random(roi_id).shuffle(patch_della_roi)

                    self.patches_da_mostrare.extend(patch_della_roi)
        # --- Gestione Inpput da Cartella di Patch (preprocessate) ---
        else:
            self.patches_da_mostrare = [
                p for p in tutte_le_patch
                if isinstance(p, dict) and p.get("is_sampled", True) is not False
            ]

            # Applico l'ordine di visualizzazione impostato dall'utente
            ordine = self.model.data.get("sampling_config", {}).get("show_order", "sequential")
            if "random" in ordine.lower():
                random.shuffle(self.patches_da_mostrare)
            else:
                self.patches_da_mostrare.sort(key=lambda p: str(p.get("file_name") or p.get("patch_id") or ""))

        # Controllo Sicurezza
        if not self.patches_da_mostrare:
            QMessageBox.information(
                self.view,
                "Sessione Completata",
                "Non ci sono patch da etichettare per la selezione attuale."
            )
            QTimer.singleShot(100, lambda: self.naviga_alla_dashboard() if self.naviga_alla_dashboard else None)

    def _inizializza_image_manager(self):
        """Legge i metadati dal JSON e istanzia lk'ImageManager"""
        percorso_base = self.model.data.get("source_path", "")
        tipo_sorgente = self.model.data.get("source_type", "")

        if not percorso_base:
            print("[DEBUG - ERROR] Etichettatura: Percorso sorgente mancante nel JSON.")
            return

        if tipo_sorgente in ["patch_folder", "Folder"]:
            self.image_manager = get_manager(method='Folder', input_path=percorso_base)

        elif tipo_sorgente in ["whole_image", "Slide"]:
            dimensione_patch = self.model.data.get("patching_config", {}).get("patch_size", 512)
            self.image_manager = get_manager(
                method='Slide',
                input_path=percorso_base,
                tile_w=dimensione_patch,
                tile_h=dimensione_patch
            )

    def _ripristina_cronologia_sessione(self):
        """
        Recupera le ultime patch etichettate dal JSON (basandosi sul tempo di revisione)
        e le inserisce nella history per mantenere il contesto visivo.
        """
        # Filtriamo solo le patch che sono già state etichettate nel set corrente
        gia_etichettate = [
            p for p in self.patches_da_mostrare
            if p.get("status") == "labeled" and p.get("reviewed_at")
        ]

        if not gia_etichettate:
            return

        # Ordiniamo per data di revisione (dalla più vecchia alla più recente)
        gia_etichettate.sort(key=lambda p: p["reviewed_at"])

        ultime_patch = gia_etichettate[-10:]

        for patch in ultime_patch:
            try:
                # Estrazione thumbnail
                if self.is_slide_source:
                    vips_image = self.image_manager.extract_patch(
                        (patch["x"], patch["y"], patch["width"], patch["height"]))
                else:
                    vips_image = self.image_manager.extract_patch(patch["file_name"])

                # Ridimensionamento
                dim_thumb = 150
                if vips_image.width > dim_thumb or vips_image.height > dim_thumb:
                    try:
                        vips_image = vips_image.thumbnail_image(dim_thumb)
                    except AttributeError:
                        scala = dim_thumb / max(vips_image.width, vips_image.height)
                        vips_image = vips_image.resize(scala)

                thumb_pixmap = pyvips_to_qpixmap(vips_image)
                del vips_image

                # Assemblo i dati
                nome_etichetta = patch.get("label")
                colore_hex = self.view.color_map.get(nome_etichetta, "#0078d7")
                patch_id = patch.get("patch_id")

                self.history_queue.appendleft((patch_id, thumb_pixmap, nome_etichetta, colore_hex))

            except Exception as e:
                print(f"[DEBUG - WARNING] Impossibile ripristinare patch {patch.get('patch_id')} in history: {e}")

        # Inietto cronologia nella UI
        if self.history_queue:
            dati_per_view = list(self.history_queue)
            self.view.aggiorna_cronologia(dati_per_view)

    def collega_segnali(self):
        """Collega gli eventi generati dall'utente nell'Interafaccia ai metodi del Controller"""
        self.view.richiesta_indietro.connect(self.vai_indietro)
        self.view.richiesta_avanti.connect(self.vai_avanti)
        self.view.btn_dashboard.clicked.connect(self.salva_ed_esci)
        self.view.etichetta_selezionata.connect(self.gestisci_etichettatura)
        self.view.richiesta_salto.connect(self.vai_a_patch_specifica)
        self.view.richiesta_contesto.connect(self._gestisci_zoom_contesto)
        self.view.richiesta_rimozione_etichetta.connect(self.rimuovi_etichetta)
        self.view.combo_filtri.currentIndexChanged.connect(self._al_cambio_filtro)

    def _al_cambio_filtro(self, index):
        """Scatta quando l'utente cambia imposta un filtro di visualizzazione"""
        self.salva_patch_attuale()

        # Conto se ci sono patch valide con il nuovo filtro
        patch_valide = sum(1 for p in self.patches_da_mostrare if self._is_patch_valida(p))

        if patch_valide == 0 and index != 0:
            QMessageBox.warning(self.view, "Attenzione", "Nessuna patch soddisfa questo filtro nella sessione attuale.")
            self.view.combo_filtri.blockSignals(True)
            self.view.combo_filtri.setCurrentIndex(0)
            self.view.combo_filtri.blockSignals(False)
            self._aggiorna_contatore_e_bottoni()
            return

        # Saltiamo alla prima patch valida trovata
        for i, p in enumerate(self.patches_da_mostrare):
            if self._is_patch_valida(p):
                self.indice_corrente = i
                break

        self.aggiorna_vista()

    # ==========================================
    # LOGICA DI NAVIGAZIONE E STATO
    # ==========================================
    def trova_punto_di_ripresa(self):
        """Imposta l'indice sull'ultima patch mostrata del set filtrato, se la sessione è nuova parte dalla patch con indice 0"""
        for i, patch in enumerate(self.patches_da_mostrare):
            if not patch.get("shown_to_user", False):
                self.indice_corrente = max(0, i - 1)
                return
        self.indice_corrente = 0

    def _is_patch_valida(self, patch):
        """Motore di calcolo: verifica se una patch è compatibile al filtro di visualizzazione"""
        filtro = self.view.combo_filtri.currentIndex()

        if filtro == 1 and patch.get("shown_to_user", False): return False
        if filtro == 2 and patch.get("label"): return False
        if filtro == 3 and not patch.get("selected_for_review", False): return False

        return True

    def _aggiorna_contatore_e_bottoni(self):
        """Calcola dinamicamente la posizione relativa della patch in base ai filtri accesi"""
        # Estraiamo gli indici assoluti di tutte le patch compatibili al filtro
        indici_validi = [i for i, p in enumerate(self.patches_da_mostrare) if self._is_patch_valida(p)]
        totale_valide = len(indici_validi)

        filtri_attivi = self.view.combo_filtri.currentIndex() > 0

        # Caso limite: nessuna patch supera il filtro
        if totale_valide == 0:
            self.view.label_counter.setText("0 di 0")
            self.view.btn_prev.setEnabled(False)
            self.view.btn_next.setEnabled(False)
            return

        # Calcolo posizione relativa in base al filtro
        if self.indice_corrente in indici_validi:
            pos_relativa = indici_validi.index(self.indice_corrente)

            testo = f"{pos_relativa + 1} di {totale_valide}"
            if filtri_attivi:
                testo += " (Filtrate)"

            self.view.label_counter.setText(testo)
            self.view.btn_prev.setEnabled(pos_relativa > 0)
            self.view.btn_next.setEnabled(pos_relativa < totale_valide - 1)

        else:
            testo = f"- di {totale_valide}"
            if filtri_attivi:
                testo += " (Filtrate)"

            self.view.label_counter.setText(testo)
            self.view.btn_prev.setEnabled(any(i < self.indice_corrente for i in indici_validi))
            self.view.btn_next.setEnabled(any(i > self.indice_corrente for i in indici_validi))

    def ottieni_patch_corrente(self):
        """Restituisce il dizionario della patch mostrata a schermo"""
        return self.patches_da_mostrare[self.indice_corrente] if self.patches_da_mostrare else None

    def aggiorna_vista(self):
        """
        Legge lo stato della patch dal Model e lo inietta nella View
        """
        patch = self.ottieni_patch_corrente()
        if not patch:
            return

        self._aggiorna_contatore_e_bottoni()

        self.view.radio_rivedere.blockSignals(True)
        self.view.text_note.blockSignals(True)
        self.view.gruppo_etichette.blockSignals(True)

        self.view.text_note.setPlainText(patch.get("annotation_text", ""))
        self.view.radio_rivedere.setChecked(patch.get("selected_for_review", False))
        self.view.mostra_etichetta_selezionata(patch.get("label"))

        self.view.radio_rivedere.blockSignals(False)
        self.view.text_note.blockSignals(False)
        self.view.gruppo_etichette.blockSignals(False)

        self.current_patch_pixmap = None
        gc.collect()

        try:
            if self.is_slide_source:
                vips_image = self.image_manager.extract_patch((patch["x"], patch["y"], patch["width"], patch["height"]))
            else:
                vips_image = self.image_manager.extract_patch(patch["file_name"])

            # Ridimensionamento
            max_dim_schermo = 2048
            if vips_image.width > max_dim_schermo or vips_image.height > max_dim_schermo:
                try:
                    vips_image = vips_image.thumbnail_image(max_dim_schermo)
                except AttributeError:
                    scala = max_dim_schermo / max(vips_image.width, vips_image.height)
                    vips_image = vips_image.resize(scala)

            pixmap_estratto = pyvips_to_qpixmap(vips_image)
            self.current_patch_pixmap = pixmap_estratto
            self.view.carica_immagine(pixmap_estratto)

            del vips_image
            gc.collect()

        except Exception as e:
            print(f"[ERROR] Estrazione fallita: {e}")

        # Aggiornamento stato patch
        if not patch.get("shown_to_user", False):
            patch["shown_to_user"] = True

            # Aggiornameto stato ROI
            if self.is_slide_source:
                roi_id_della_patch = patch.get("roi_id")
                if roi_id_della_patch:
                    lista_roi = self.model.data.get("sampling_config", {}).get("roi_list", [])
                    for roi in lista_roi:
                        if roi.get("id") == roi_id_della_patch:
                            stats = roi.setdefault("stats", {})
                            stats["shown_to_user"] = stats.get("shown_to_user", 0) + 1
                            break

            if hasattr(self.model, "salva_su_disco"):
                self.model.salva_su_disco()

    def salva_patch_attuale(self):
        """
        Sovrascrive nel Model i dati della patch ottenuti dalla View
        """
        patch = self.ottieni_patch_corrente()
        if not patch:
            return

        self.model.aggiorna_patch(
            patch_id=patch["patch_id"],
            label=self.view.get_etichetta_attiva(),
            note=self.view.text_note.toPlainText(),
            da_rivedere=self.view.radio_rivedere.isChecked()
        )

    def _gestisci_zoom_contesto(self, attivo: bool):
        """
        Estare una griglia 3x3 che mostra il contesto della patch, evidenziando quella corrente
        """
        patch_centrale = self.ottieni_patch_corrente()
        if not patch_centrale or not self.is_slide_source:
            return

        if not attivo:
            self.view.image_viewer.mostra_immagine(self.current_patch_pixmap)
            gc.collect()
            return

        QApplication.processEvents()

        try:
            w, h = patch_centrale["width"], patch_centrale["height"]
            patches = self.model.data.get("patches", [])
            if not patches:
                return

            ext_w = w * 3
            ext_h = h * 3

            ctx_x = patch_centrale["x"] - w
            ctx_y = patch_centrale["y"] - h

            max_x_slide = max(p.get("x", 0) + p.get("width", 0) for p in patches)
            max_y_slide = max(p.get("y", 0) + p.get("height", 0) for p in patches)

            ext_x = max(0, min(ctx_x, max_x_slide - ext_w))
            ext_y = max(0, min(ctx_y, max_y_slide - ext_h))

            vips_image = self.image_manager.extract_patch(
                (ext_x, ext_y, ext_w, ext_h),
                target_size=2048
            )

            fattore_scala = vips_image.width / ext_w

            pixmap_contesto = pyvips_to_qpixmap(vips_image)
            del vips_image

            painter = QPainter(pixmap_contesto)

            for p in patches:
                if (ext_x <= p["x"] < ext_x + ext_w and
                        ext_y <= p["y"] < ext_y + ext_h):

                    local_x = int((p["x"] - ext_x) * fattore_scala)
                    local_y = int((p["y"] - ext_y) * fattore_scala)
                    rect_w = int(p["width"] * fattore_scala)
                    rect_h = int(p["height"] * fattore_scala)

                    rect_patch = QRect(local_x, local_y, rect_w, rect_h)

                    # Evidenzio la patch corrente
                    if p["patch_id"] == patch_centrale["patch_id"]:
                        pen = QPen(QColor(255, 255, 0))
                        pen.setWidth(max(2, int(4 * fattore_scala)))
                        painter.setPen(pen)
                        painter.setBrush(Qt.BrushStyle.NoBrush)
                        painter.drawRect(rect_patch)
                    # Evidenzio le patch del contesto già etichettate
                    elif p.get("label"):
                        colore_hex = self.view.color_map.get(p["label"], "#0078d7")
                        colore = QColor(colore_hex)
                        colore.setAlpha(60)

                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.setBrush(QBrush(colore))
                        painter.drawRect(rect_patch)

            painter.end()
            self.view.image_viewer.mostra_immagine(pixmap_contesto)

        except Exception as e:
            print(f"[ERROR] Zoom contesto fallito: {e}")
    # ==========================================
    #  COMANDI DI NAVIDAZIONE
    # ==========================================

    def vai_avanti(self):
        """
        Salva la patch attuale e va avanti fino alla successiva valida
        """
        self.salva_patch_attuale()

        step = 1
        while self.indice_corrente + step < len(self.patches_da_mostrare):
            next_index = self.indice_corrente + step
            next_patch = self.patches_da_mostrare[next_index]

            if not self._is_patch_valida(next_patch):
                step += 1
                continue

            self.indice_corrente = next_index
            self.aggiorna_vista()
            return

    def vai_indietro(self):
        """
        Salva la patch attuale e torna indietro fino alla precedente valida
        """
        self.salva_patch_attuale()

        step = 1
        while self.indice_corrente - step >= 0:
            next_index = self.indice_corrente - step
            next_patch = self.patches_da_mostrare[next_index]

            if not self._is_patch_valida(next_patch):
                step += 1
                continue

            self.indice_corrente = next_index
            self.aggiorna_vista()

            return

    def vai_a_patch_specifica(self, patch_id):
        """Permette il salto diretto a una patch specifica (es. cliccandola nella cronologia visiva)."""
        self.salva_patch_attuale()

        for i, p in enumerate(self.patches_da_mostrare):
            if p.get("patch_id") == patch_id:
                self.indice_corrente = i
                self.aggiorna_vista()
                return

    # =========================================
    # LOGICA DI ETICHETTATURA E SALVATAGGIO
    # =========================================

    def gestisci_etichettatura(self, nome_etichetta, da_shortcut=False):
        """
        Applico l'etichetta alla patch. Se clicco un'etichetta attiva viene deselezionata, a meno che non stia usando la tastiera.
        """
        patch_corrente = self.ottieni_patch_corrente()
        if not patch_corrente:
            return

        if patch_corrente.get("label") == nome_etichetta:
            if da_shortcut:
                pass
            else:
                self.rimuovi_etichetta()
                return

        self.view.mostra_etichetta_selezionata(nome_etichetta)

        patch_corrente["status"] = "labeled"
        patch_corrente["reviewed_at"] = datetime.datetime.now().isoformat()

        # Aggiorno la History
        if self.current_patch_pixmap:
            colore_hex = self.view.color_map.get(nome_etichetta, "#0078d7")
            patch_id = patch_corrente.get("patch_id")

            # Se la patch era già nella History la riporto in cima
            elemento_esistente = next((item for item in self.history_queue if item[0] == patch_id), None)
            if elemento_esistente:
                self.history_queue.remove(elemento_esistente)

            thumb_pixmap = self.current_patch_pixmap.scaled(
                150,150,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            self.history_queue.appendleft((patch_id, thumb_pixmap, nome_etichetta, colore_hex))

            if hasattr(self.view, 'aggiorna_cronologia'):
                dati_per_view = [(pid, pixmap, nome, colore) for pid, pixmap, nome, colore in self.history_queue]
                self.view.aggiorna_cronologia(dati_per_view)

        is_ultima_patch = (self.indice_corrente == len(self.patches_da_mostrare) - 1)

        if is_ultima_patch:
            self.salva_patch_attuale()
            self.aggiorna_vista()

            torna_a_dashboard = self.view.mostra_avviso_fine_sessione()
            if torna_a_dashboard:
                self.salva_ed_esci()
        else:
            self.vai_avanti()

    def rimuovi_etichetta(self):
        """
        Se viene deselezionata un'etichetta, ripulisco lo stato della patch
        """
        patch_corrente = self.ottieni_patch_corrente()
        if not patch_corrente or "label" not in patch_corrente:
            return

        patch_corrente.pop("label", None)
        patch_corrente.pop("reviewed_at", None)
        patch_corrente["status"] = "skipped"

        self.model.aggiorna_patch(
            patch_id=patch_corrente["patch_id"],
            label=None,
            note=self.view.text_note.toPlainText(),
            da_rivedere=self.view.radio_rivedere.isChecked()
        )

        # Salviamo fisicamente il JSON
        if hasattr(self.model, "salva_su_disco"):
            self.model.salva_su_disco()

        patch_id = patch_corrente.get("patch_id")
        elemento_esistente = next((item for item in self.history_queue if item[0] == patch_id), None)

        if elemento_esistente:
            self.history_queue.remove(elemento_esistente)
            dati_per_view = [(pid, pixmap, nome, colore) for pid, pixmap, nome, colore in self.history_queue]
            if hasattr(self.view, 'aggiorna_cronologia'):
                self.view.aggiorna_cronologia(dati_per_view)

        self.aggiorna_vista()

    def salva_ed_esci(self):
        """
        Salva la patch e torna alla Dashboard
        """
        self.salva_patch_attuale()
        self.model.salva_su_disco()
        if self.naviga_alla_dashboard:
            self.naviga_alla_dashboard()