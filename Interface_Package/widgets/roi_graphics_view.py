from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QMenu
from PySide6.QtCore import Qt, QRectF, QLineF, Signal
from PySide6.QtGui import QPen, QColor, QBrush, QPainter


class RoiGraphicsView(QGraphicsView):
    """
    Componente visivo interattivo (View) per l'esplorazione e l'annotazione delle WSI.
    Gestisce Panning, Deep Zoom ancorato, disegno dinamico di ROI e rendering
    ottimizzato della griglia di campionamento.
    """

    # Segnali personalizzati per comunicare con il Controller (Observer Pattern)
    vista_cambiata = Signal()
    roi_modificate = Signal()

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

        self.grid_step_x = 0
        self.grid_step_y = 0
        self.mostra_griglia = True
        self.grid_offset_x = 0
        self.grid_offset_y = 0

        # =====================
        # AGGIORNAMENTO VISTA
        # =====================
        self.horizontalScrollBar().valueChanged.connect(lambda _: self.vista_cambiata.emit())
        self.verticalScrollBar().valueChanged.connect(lambda _: self.vista_cambiata.emit())

    # =======================================
    # EVENTI MOUSE
    # =======================================

    def wheelEvent(self, event):
        """
        Override: Gestisce lo Zoom (Rotellina del mouse) mantenendo immobile
        l'oggetto che si trova esattamente sotto il cursore.
        """
        zoom_in_factor = 1.15
        zoom_out_factor = 1.0 / zoom_in_factor

        # 1. Coordinate prima della trasformazione spaziale
        old_pos_view = event.position().toPoint()
        old_pos_scene = self.mapToScene(old_pos_view)

        # 2. Applicazione della matrice di scala
        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)

        # 3. Dove si trova ora quel punto a causa dello "slittamento" della matrice?
        new_pos_view = self.mapFromScene(old_pos_scene)

        # 4. Calcolo dell'errore (Delta)
        delta_x = new_pos_view.x() - old_pos_view.x()
        delta_y = new_pos_view.y() - old_pos_view.y()

        # 5. Compensazione hardware tramite le scrollbar
        self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + delta_x)
        self.verticalScrollBar().setValue(self.verticalScrollBar().value() + delta_y)

    def mousePressEvent(self, event):
        """Gestisce l'inizio delle azioni: Tasto Sinistro (Pan) o Destro (Disegno ROI)"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.panning = True
            self.last_mouse_pos = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()

        elif event.button() == Qt.MouseButton.RightButton:
            # Protezione: Se clicco su una ROI già disegnata, non iniziare a disegnarne una nuova
            item = self.itemAt(event.pos())
            if isinstance(item, QGraphicsRectItem) and item in self.roi_items:
                return

            self.drawing = True
            # Mappiamo le coordinate hardware del mouse sulla scena virtuale
            self.start_point = self.mapToScene(event.position().toPoint())

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
                self.last_valid_rect = rect_proposto
                self.current_rect_item.setRect(rect_proposto)
            else:
                self.current_rect_item.setRect(self.last_valid_rect)


            event.accept()

    def mouseReleaseEvent(self, event):
        """Conclude le azioni e consolida i dati in memoria"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            #self.vista_cambiata.emit()
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
