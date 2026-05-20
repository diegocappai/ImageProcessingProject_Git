from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QMenu, QGraphicsPixmapItem
from PySide6.QtCore import Qt, QRectF, QLineF, Signal, QTimer
from PySide6.QtGui import QPen, QColor, QBrush, QPainter, QTransform
from Utils.pyvips_to_qpixmap import pyvips_to_qpixmap


class RoiGraphicsView(QGraphicsView):
    """
    Componente visivo interattivo (View) per l'esplorazione e l'annotazione delle WSI.
    Gestisce Panning, Deep Zoom ancorato, disegno dinamico di ROI e rendering
    ottimizzato della griglia di campionamento.
    """

    # Segnali personalizzati per comunicare con il Controller (Observer Pattern)
    vista_cambiata = Signal()
    roi_modificate = Signal()
    selezione_area = Signal(QRectF)


    def __init__(self, parent=None):
        super().__init__(parent)

        # Inizializzazione del pattern Scene-View di Qt
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Disabilitiamo i comportamenti default per gestirli manualmente in modo ottimizzato
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)  # Smussatura hardware dei pixel

        # ==========================
        # MACCHINA A STATI
        # ==========================
        self.drawing = False
        self.start_point = None
        self.current_rect_item = None
        self.last_valid_rect = None
        self.roi_items = []

        self.panning = False
        self.last_mouse_pos = None

        self.targeted_sampling = False
        self.rubber_band_item = None
        self.roi_bersaglio = None

        self.grid_step_x = 0
        self.grid_step_y = 0
        self.mostra_griglia = True
        self.grid_offset_x = 0
        self.grid_offset_y = 0

        self.image_manager = None
        self.current_hd_tile = None

        self.rois_bloccate = []

        self.disegno_abilitato = True

        self.min_zoom = 0.1
        self.max_zoom = 1.0

        self.zoom_timer = QTimer(self)
        self.zoom_timer.setSingleShot(True)
        self.zoom_timer.timeout.connect(self._renderizza_deep_zoom)

        # =====================
        # AGGIORNAMENTO VISTA
        # =====================
        self.horizontalScrollBar().valueChanged.connect(self._on_scroll_changed)
        self.verticalScrollBar().valueChanged.connect(self._on_scroll_changed)

    def _on_scroll_changed(self):
        """Emette il segnale per l'esterno e aggiorna il deep zoom all'interno"""
        self.vista_cambiata.emit()
        self.zoom_timer.start(300)

    # =======================================
    # GESTIONE IMMAGINI E DEEP ZOOM
    # =======================================

    def imposta_motore_immagini(self, manager):
        """Riceve il motore PyVips dal Controller esterno e carica il thumbnail base"""
        self.image_manager = manager
        if not self.image_manager:
            return

        try:
            vips_thumb = self.image_manager.load_thumbnail_rgb(1024)
            if vips_thumb:
                pixmap = pyvips_to_qpixmap(vips_thumb)

                self.scene.clear()
                self.roi_items.clear()
                self.current_hd_tile = None

                sfondo_item = QGraphicsPixmapItem(pixmap)
                sfondo_item.setZValue(-1.0)

                w_reale = self.image_manager.width
                h_reale = self.image_manager.height

                scala_x = w_reale / pixmap.width()
                scala_y = h_reale / pixmap.height()

                sfondo_item.setTransform(QTransform().scale(scala_x, scala_y))

                self.scene.addItem(sfondo_item)

                self.setSceneRect(0, 0, w_reale, h_reale)
                self.reset_view()
        except Exception as e:
            print(f"[DEBUG - ERROR] Errore caricamento sfondo WSI: {e}")

    def reset_view(self):
        """Adatta l'immagine alla View e imposta il limite minimo di zoom"""
        if not self.sceneRect().isValid():
            return

        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        # Il min_zoom diventa lo zoom attuale dopo il fit (l'immagine occupa tutto lo spazio)
        self.min_zoom = self.transform().m11()
        # Il max_zoom è 1.0 (risoluzione nativa per non sgranare le patch)
        self.max_zoom = 1.0

    def _renderizza_deep_zoom(self):
        """Metodo interno che auto-gestisce l'estrazione ad alta risoluzione"""
        if not self.image_manager:
            return

        # 1. Pulisci la RAM dal vecchio frame
        if self.current_hd_tile:
            self.scene.removeItem(self.current_hd_tile)
            self.current_hd_tile = None

        area = self.get_area_visibile_pura()
        if not area:
            return

        # 2. Ottimizzazione: Non estrarre l'HD se vediamo l'80% del vetrino
        if area['w'] > area['scene_w'] * 0.8:
            return

        # 3. Estrai e renderizza
        try:
            vips_crop = self.image_manager.get_high_res_crop(
                area['x'], area['y'], area['w'], area['h'],
                area['scene_w'], area['scene_h']
            )

            if vips_crop:
                pixmap_hd = pyvips_to_qpixmap(vips_crop)
                self.current_hd_tile = QGraphicsPixmapItem(pixmap_hd)
                self.current_hd_tile.setPos(area['x'], area['y'])

                scala_x = area['w'] / pixmap_hd.width()
                scala_y = area['h'] / pixmap_hd.height()

                self.current_hd_tile.setTransform(QTransform().scale(scala_x, scala_y))
                self.current_hd_tile.setZValue(-0.5)

                self.scene.addItem(self.current_hd_tile)

        except Exception as e:
            print(f"[DEBUG - ERROR] Deep Zoom fallito: {e}")

    # =======================================
    # EVENTI MOUSE
    # =======================================

    def wheelEvent(self, event):
        """
        Override: Gestisce lo Zoom (Rotellina del mouse) mantenendo immobile
        l'oggetto che si trova esattamente sotto il cursore e rispettando i limiti.
        """
        zoom_in_factor = 1.15
        zoom_out_factor = 1.0 / zoom_in_factor

        # 1. Calcoliamo il fattore di scala base
        fattore = zoom_in_factor if event.angleDelta().y() > 0 else zoom_out_factor

        # 2. Calcoliamo quale sarebbe lo zoom finale
        zoom_attuale = self.transform().m11()
        zoom_futuro = zoom_attuale * fattore

        # 3. 🟢 BLOCCO LIMITI ZOOM
        if zoom_futuro < self.min_zoom:
            fattore = self.min_zoom / zoom_attuale
        elif zoom_futuro > self.max_zoom:
            fattore = self.max_zoom / zoom_attuale

        # 4. Applichiamo lo zoom solo se permesso dai limiti
        # (Se fattore == 1.0 significa che abbiamo sbattuto contro il limite massimo o minimo)
        if abs(fattore - 1.0) > 0.0001:
            # Coordinate prima della trasformazione
            old_pos_view = event.position().toPoint()
            old_pos_scene = self.mapToScene(old_pos_view)

            # Applicazione della matrice di scala controllata
            self.scale(fattore, fattore)

            # Dove si trova ora quel punto a causa della matrice?
            new_pos_view = self.mapFromScene(old_pos_scene)

            # Calcolo dell'errore (Delta) per compensare lo slittamento
            delta_x = new_pos_view.x() - old_pos_view.x()
            delta_y = new_pos_view.y() - old_pos_view.y()

            # Compensazione hardware tramite le scrollbar (Mantiene il cursore ancorato)
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + delta_x)
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + delta_y)

    def mousePressEvent(self, event):
        """Gestisce l'inizio delle azioni: Tasto Sinistro (Pan) o Destro (Disegno ROI)"""
        if event.button() == Qt.MouseButton.LeftButton:
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                self.start_point = self.mapToScene(event.position().toPoint())

                roi_trovata_rect = None
                for roi_esistente in self.roi_items:
                    if roi_esistente.rect().contains(self.start_point):
                        roi_trovata_rect = roi_esistente.rect()
                        break

                if not roi_trovata_rect:
                    for rect_bloccato in self.rois_bloccate:
                        if rect_bloccato.contains(self.start_point):
                            roi_trovata_rect = rect_bloccato
                            break

                if not roi_trovata_rect:
                    event.accept()
                    return

                self.targeted_sampling = True
                self.roi_bersaglio = roi_trovata_rect
                # Creiamo il rettangolo di selezione (Stile: Arancione Tratteggiato)
                self.rubber_band_item = QGraphicsRectItem()
                pen = QPen(QColor(255, 165, 0), 2, Qt.PenStyle.DashLine)
                pen.setCosmetic(True)
                brush = QBrush(QColor(255, 165, 0, 50))  # Arancione semitrasparente

                self.rubber_band_item.setPen(pen)
                self.rubber_band_item.setBrush(brush)
                self.rubber_band_item.setZValue(100)  # Lo mettiamo sopra a tutto
                self.scene.addItem(self.rubber_band_item)
                event.accept()
            else:
                # Comportamento normale (Panning)
                self.panning = True
                self.last_mouse_pos = event.position().toPoint()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                event.accept()

        elif event.button() == Qt.MouseButton.RightButton and self.disegno_abilitato:
            # Protezione: Se clicco su una ROI già disegnata, non iniziare a disegnarne una nuova
            self.start_point = self.mapToScene(event.position().toPoint())

            for rect_bloccato in self.rois_bloccate:
                if rect_bloccato.contains(self.start_point):
                    return

            item = self.itemAt(event.pos())
            if isinstance(item, QGraphicsRectItem) and item in self.roi_items:
                return

            self.drawing = True
            # Mappiamo le coordinate hardware del mouse sulla scena virtuale

            self.last_valid_rect = QRectF(self.start_point, self.start_point)
            self.current_rect_item = QGraphicsRectItem()

            # Stile della nuova ROI
            pen = QPen(QColor(0, 255, 0), 1)
            pen.setCosmetic(True)  # Il bordo non si ingrossa durante lo zoom
            brush = QBrush(QColor(0, 255, 0, 30))

            self.current_rect_item.setPen(pen)
            self.current_rect_item.setBrush(brush)

            self.scene.addItem(self.current_rect_item)
            event.accept()

    def mouseMoveEvent(self, event):
        """Aggiorna la grafica 60 volte al secondo durante il trascinamento"""
        if self.targeted_sampling and self.rubber_band_item:
            current_point = self.mapToScene(event.position().toPoint())
            rect_proposto = QRectF(self.start_point, current_point).normalized()
            if self.roi_bersaglio:
                rect_proposto = rect_proposto.intersected(self.roi_bersaglio)

            self.rubber_band_item.setRect(rect_proposto)
            event.accept()

        if self.panning:
            current_mouse_pos = event.position().toPoint()
            delta = current_mouse_pos - self.last_mouse_pos

            # Muoviamo letteralmente la telecamera (scrollbar)
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())

            self.last_mouse_pos = current_mouse_pos
            event.accept()

        elif self.drawing and self.current_rect_item:
            current_point = self.mapToScene(event.position().toPoint())

            rect_proposto = QRectF(self.start_point, current_point).normalized()
            rect_proposto = rect_proposto.intersected(self.sceneRect())

            collisione = False
            for roi_esistente in self.roi_items:
                if rect_proposto.intersects(roi_esistente.rect()):
                    collisione = True
                    break

            if not collisione:
                for rect_bloccato in self.rois_bloccate:
                    if rect_proposto.intersects(rect_bloccato):
                        collisione = True
                        break

            if not collisione:
                self.last_valid_rect = rect_proposto
                self.current_rect_item.setRect(rect_proposto)
            else:
                self.current_rect_item.setRect(self.last_valid_rect)


            event.accept()

    def mouseReleaseEvent(self, event):
        """Conclude le azioni e consolida i dati in memoria"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Conclusione della selezione mirata
            if self.targeted_sampling:
                self.targeted_sampling = False
                self.roi_bersaglio = None

                if self.rubber_band_item:
                    rect_finale = self.rubber_band_item.rect()

                    # Eliminiamo il rettangolo arancione dalla scena (era solo un tool visivo)
                    self.scene.removeItem(self.rubber_band_item)
                    self.rubber_band_item = None

                    # Se la selezione non è un click accidentale (minimo 5x5 px), emettiamo il segnale!
                    if rect_finale.width() > 5 and rect_finale.height() > 5:
                        self.selezione_area.emit(rect_finale)
                event.accept()

            elif self.panning:
                self.panning = False
                self.setCursor(Qt.CursorShape.ArrowCursor)
                event.accept()

        elif event.button() == Qt.MouseButton.RightButton:
            if self.drawing:
                self.drawing = False

                if self.current_rect_item:
                    rect = self.current_rect_item.rect()

                    # Prevenzione di click accidentali (micro-roi invisibili)
                    if rect.width() > 5 and rect.height() > 5:
                        self.roi_items.append(self.current_rect_item)
                        self.roi_modificate.emit()
                    else:
                        self.scene.removeItem(self.current_rect_item)

                self.current_rect_item = None
                event.accept()

    def mouseDoubleClickEvent(self, event):
        """Gestisce l'eliminazione mirata tramite Menù Contestuale"""
        if event.button() == Qt.MouseButton.RightButton:
            item = self.itemAt(event.pos())

            if isinstance(item, QGraphicsRectItem) and item in self.roi_items:
                menu = QMenu(self)
                azione_elimina = menu.addAction("🗑 Elimina ROI")
                azione_scelta = menu.exec(event.globalPosition().toPoint())

                if azione_scelta == azione_elimina:
                    self.rimuovi_roi_specifica(item)
            event.accept()

    def contextMenuEvent(self, event):
        """Disabilita i menu contestuali di default per non interferire con il disegno"""
        event.accept()

    # ==========================================
    # EVENTI TASTIERA
    # ==========================================

    def keyPressEvent(self, event):
        """
        Gestisce la navigazione nell'immagine tramite le frecce direzionali
        """
        step = 50
        h_bar = self.horizontalScrollBar()
        v_bar = self.verticalScrollBar()

        if event.key() == Qt.Key.Key_Left:
            h_bar.setValue(h_bar.value() - step)
        elif event.key() == Qt.Key.Key_Right:
            h_bar.setValue(h_bar.value() + step)
        elif event.key() == Qt.Key.Key_Up:
            v_bar.setValue(v_bar.value() - step)
        elif event.key() == Qt.Key.Key_Down:
            v_bar.setValue(v_bar.value() + step)
        else:
            super().keyPressEvent(event)
            return

        event.accept()


    # ==========================================
    # RENDERING OTTIMIZZATO DELLA GRIGLIA
    # ==========================================
    def set_grid_step(self, step_x, step_y, offset_x=0, offset_y=0):
        self.grid_step_x = step_x
        self.grid_step_y = step_y
        self.grid_offset_x = offset_x
        self.grid_offset_y = offset_y
        self.viewport().update()  # Forza il ridisegno

    def drawForeground(self, painter, rect):
        """
        Disegna SOLO le linee che cadono nel "rect" attualmente inquadrato
        """
        if not self.mostra_griglia or self.grid_step_x <= 0 or self.grid_step_y <= 0:
            return

        super().drawForeground(painter, rect)

        # Sicurezza anti-lag: se facciamo troppo zoom out (le linee sarebbero troppo fitte e sovrapposte)
        livello_zoom = self.transform().m11()
        if self.grid_step_x * livello_zoom < 4:
            return

        rect_disegno = rect.intersected(self.sceneRect())
        if rect_disegno.isEmpty():
            return

        # Stile della griglia
        pen = QPen(QColor(0, 255, 0, 180))
        pen.setWidth(2)
        pen.setCosmetic(True)  # Mantiene lo spessore intatto indipendentemente dallo zoom
        pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(pen)

        # Delimitazione dell'area visibile
        left, right = int(rect_disegno.left()), int(rect_disegno.right())
        top, bottom = int(rect_disegno.top()), int(rect_disegno.bottom())

        # Matematica Modulare: trova la prima coordinata della griglia che cade nell'area visibile
        start_x = left - ((left - self.grid_offset_x) % self.grid_step_x)
        start_y = top - ((top - self.grid_offset_y) % self.grid_step_y)

        # Batch Rendering: accumuliamo in un array per processarle simultaneamente
        lines = []

        x = start_x
        while x <= right:
            lines.append(QLineF(x, top, x, bottom))
            x += self.grid_step_x

        y = start_y
        while y <= bottom:
            lines.append(QLineF(left, y, right, y))
            y += self.grid_step_y

        painter.drawLines(lines)  # Disegno vettoriale accelerato

    def imposta_visibilita_griglia(self, visibile):
        self.mostra_griglia = visibile
        self.scene.invalidate(self.sceneRect(), QGraphicsScene.SceneLayer.ForegroundLayer)

    def set_zoom_grid(self):
        """
        Calcola e applica automaticamente il livello di zoom minimo richiesto
        per superare il blocco di sicurezza anti-lag e rendere visibile la griglia.
        """
        if self.grid_step_x <= 0:
            return

        # La condizione anti-lag è: grid_step_x * zoom >= 4
        # Quindi il livello di zoom minimo richiesto è: 4 / grid_step_x
        # Aggiungiamo un piccolo margine (es. 1.2) per essere sicuri che si veda chiaramente
        zoom_minimo_richiesto = (4.0 / self.grid_step_x) * 1.2

        zoom_attuale = self.transform().m11()

        # Se lo zoom attuale è già sufficiente, non facciamo nulla.
        # Altrimenti applichiamo la matrice di scala necessaria.
        if zoom_attuale < zoom_minimo_richiesto:
            fattore_da_applicare = zoom_minimo_richiesto / zoom_attuale
            self.scale(fattore_da_applicare, fattore_da_applicare)

            # Opzionale: centra la vista al centro della slide dopo lo zoom
            self.centerOn(self.sceneRect().center())

    def resizeEvent(self, event):
        """Se la finestra cambia dimensione, aggiorna il limite minimo di zoom"""
        # Se eravamo al minimo (vista intera), manteniamo la vista intera
        al_minimo = (abs(self.transform().m11() - self.min_zoom) < 0.001)

        # Ricalcoliamo il nuovo limite basato sulla nuova dimensione del widget
        if self.sceneRect().isValid():
            # Calcoliamo temporaneamente quanto sarebbe lo zoom per il fit
            rect_view = self.viewport().rect()
            sc_w = rect_view.width() / self.sceneRect().width()
            sc_h = rect_view.height() / self.sceneRect().height()
            self.min_zoom = min(sc_w, sc_h)

            if al_minimo:
                self.reset_view()

        super().resizeEvent(event)

    # ==========================================
    # API PUBBLICHE PER IL CONTROLLER
    # ==========================================

    def get_area_visibile_pura(self):
        """
        Traspone le coordinate fisiche dello schermo in coordinate spaziali
        della Scena. Restituisce un dizionario puro per evitare passaggi
        di oggetti Qt tra View e Controller.
        """
        viewport_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        valid_rect = viewport_rect.intersected(self.sceneRect())

        if valid_rect.isEmpty() or valid_rect.width() <= 0 or valid_rect.height() <= 0:
            return None

        return {
            'x': valid_rect.x(), 'y': valid_rect.y(),
            'w': valid_rect.width(), 'h': valid_rect.height(),
            'scene_w': self.sceneRect().width(), 'scene_h': self.sceneRect().height()
        }

    def get_dimensioni_scena(self):
        rect = self.sceneRect()
        return rect.width(), rect.height()

    def get_roi_rects(self):
        return [item.rect() for item in self.roi_items]

    def clear_all_rois(self):
        for item in self.roi_items:
            self.scene.removeItem(item)
        self.roi_items.clear()
        self.roi_modificate.emit()

    def undo_last_roi(self):
        if self.roi_items:
            last_item = self.roi_items.pop()
            self.scene.removeItem(last_item)
            self.roi_modificate.emit()

    def rimuovi_roi_specifica(self, item):
        if item in self.roi_items:
            self.scene.removeItem(item)
            self.roi_items.remove(item)
            self.roi_modificate.emit()

    def imposta_roi_bloccate(self, lista_rectf):
        self.rois_bloccate = lista_rectf

    def imposta_modalita_disegno(self, abilitato: bool):
        self.disegno_abilitato = abilitato