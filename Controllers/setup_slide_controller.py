from Interface_Package.views.setting_new_slide_view import ImpostazioniSlideDialog
from Utils.pyvips_to_qpixmap import pyvips_to_qpixmap
from PySide6.QtCore import QTimer, QRectF


class SetupSlideController:
    """
    Controller per il Setup dei progetti Whole Slide Image (WSI)
    """

    def __init__(self, model, view: ImpostazioniSlideDialog):
        self.model = model
        self.view = view
        self.configurazione_salvata = False

        self.zoom_timer = QTimer()
        self.zoom_timer.setSingleShot(True)
        self.zoom_timer.timeout.connect(self.aggiorna_risoluzione_alta)

        self.collega_segnali()
        self._inizializza_vista_slide()

    def collega_segnali(self):
        """Mappa gli eventi causati dall'utente"""
        self.view.aggiorna_grandezza_patch.connect(self.gestisci_cambio_grandezza)
        self.view.accepted.connect(self.salva_configurazione)
        self.view.vista_cambiata.connect(self.gestisci_ritardo_zoom)
        self.view.griglia_toggled.connect(self.gestisci_visibilita_griglia)
        self.view.roi_modificate.connect(self.aggiorna_statistiche_roi)

    def _inizializza_vista_slide(self):
        """Carica l'immagine iniziale a bassa risoluzione (Livello più alto della piramide)"""
        print(f"[DEBUG - SETUP SLIDE] Caricamento anteprima da: {self.model.percorso_slide}")

        vips_thumb = self.model.ottieni_thumbnail(max_dim=1024)

        if vips_thumb:
            pixmap = pyvips_to_qpixmap(vips_thumb)
            self.view.imposta_immagine_anteprima(
                pixmap,
                self.model.larghezza_originale,
                self.model.altezza_originale
            )

            # Inizializza graficamente la griglia in base al valore di default della combobox
            valore_iniziale = self.view.get_grandezza_patch()
            self.gestisci_cambio_grandezza(valore_iniziale)

    def gestisci_visibilita_griglia(self, stato_checked):
        self.view.set_griglia_visiva(stato_checked)

    def gestisci_ritardo_zoom(self):
        """
        Pattern Debounce: Invocato ogni volta che l'utente sposta la visuale
        """
        self.zoom_timer.start(300)

    def aggiorna_risoluzione_alta(self):
        """
        Zoom Dinamico: Richiede alla View l'area attualmente inquadrata e la
        passa al Model per estrarre i pixel ad alta risoluzione
        """
        # Chiediamo alla View le coordinate della viewport
        area = self.view.get_area_visibile_pura()

        if not area:
            self.view.aggiorna_layer_alta_risoluzione(None, None)
            return

        # Deleghiamo al Model l'estrazione tramite PyVips
        vips_crop = self.model.estrai_area_alta_risoluzione(
            area['x'], area['y'], area['w'], area['h'],
            area['scene_w'], area['scene_h']
        )

        # Aggiorniamo la View sovrapponendo l'immagine HD
        if vips_crop:
            pixmap = pyvips_to_qpixmap(vips_crop)
            rect_da_passare = QRectF(area['x'], area['y'], area['w'], area['h'])
            self.view.aggiorna_layer_alta_risoluzione(pixmap, rect_da_passare)
        else:
            self.view.aggiorna_layer_alta_risoluzione(None, None)

    def aggiorna_statistiche_roi(self):
        """
        Chiede al Model di simulare l'incrocio tra la griglia e le ROI disegnate per mostrare all'utente una stima in tempo reale delle patch eleggibili
        """
        grandezza_patch = self.view.get_grandezza_patch()
        rois_qt = self.view.get_roi_rects()

        if not rois_qt:
            self.view.aggiorna_conteggio_roi(0)
            return

        # Trasformiamo l'oggetto Qt in un dizionario Python standard per slegare il Model dalla UI
        rois_pure = [{'x': r.x(), 'y': r.y(), 'w': r.width(), 'h': r.height()} for r in rois_qt]

        w_scena, h_scena = self.view.get_dimensioni_miniatura()

        # Fattore di conversione WSI -> Schermo
        scala_x = w_scena / self.model.larghezza_originale
        scala_y = h_scena / self.model.altezza_originale

        # Nessun offset richiesto al momento, ma predisposto per centraggi futuri
        offset_scena_x = 0
        offset_scena_y = 0

        # Passiamo le informazioni normalizzate al Model
        patch_calcolate = self.model.calcola_patch_in_roi(
            rois=rois_pure,
            scene_w=w_scena,
            scene_h=h_scena,
            step_x= grandezza_patch * scala_x,
            step_y= grandezza_patch * scala_y,
            offset_x=offset_scena_x,
            offset_y=offset_scena_y
        )

        self.view.aggiorna_conteggio_roi(len(patch_calcolate))

    def gestisci_cambio_grandezza(self, nuova_grandezza):
        """Aggiorna il disegno della griglia verde quando l'utente cambia risoluzione"""
        self.model.imposta_grandezza_patch(nuova_grandezza)

        totale_teorico = self.model.calcola_patch_totali()
        self.view.aggiorna_totale_patch(f"{totale_teorico} (Max Teorico)")

        self.view.aggiorna_griglia_visiva(nuova_grandezza, 0, 0)
        self.aggiorna_statistiche_roi()

    def salva_configurazione(self):
        """
        Motore di Mappatura Spaziale:
        Traspone le ROI disegnate dall'utente sulla miniatura in coordinate
        assolute basate sulle dimensioni della vera Whole Slide Image
        """
        # Lettura dei parametri semplici
        percentuale = self.view.get_perc_sampling()
        ordine = self.view.get_sampling_order()
        grandezza_patch = self.view.get_grandezza_patch()

        # Spazio Schermo vs Spazio Immagine Reale
        w_miniatura, h_miniatura = self.view.get_dimensioni_miniatura()

        if w_miniatura > 0 and h_miniatura > 0:
            scala_x = self.model.larghezza_originale / w_miniatura
            scala_y = self.model.altezza_originale / h_miniatura
        else:
            scala_x, scala_y = 1, 1

        roi_reali = []
        for rect in self.view.get_roi_rects():
            # Moltiplichiamo le coordinate a schermo per proiettarle sulla realtà
            roi_reali.append({
                "x": int(rect.x() * scala_x),
                "y": int(rect.y() * scala_y),
                "width": int(rect.width() * scala_x),
                "height": int(rect.height() * scala_y)
            })

        # Aggiornamento Model
        self.model.roi_list = roi_reali
        self.model.imposta_grandezza_patch(grandezza_patch)
        self.model.imposta_parametri_comuni(percentuale, ordine)

        print(f"[DEBUG - SETUP SLIDE] Coordinate ROI Reali Calcolate: {roi_reali}")
        self.configurazione_salvata = True

    def esegui(self):
        self.view.exec()
        return self.configurazione_salvata