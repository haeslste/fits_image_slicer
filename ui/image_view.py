
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QRubberBand
from PySide6.QtGui import QPixmap, QImage, QPen, QColor, QPainter
from PySide6.QtCore import Signal, Qt, QRect, QPoint, QRectF, QSize
from PySide6.QtCore import Signal, Qt, QRect, QPoint
import numpy as np

class ImageView(QGraphicsView):
    region_selected = Signal(QRect)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setOptimizationFlags(QGraphicsView.DontAdjustForAntialiasing | QGraphicsView.DontSavePainterState)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)

        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()
        self._pixmap_item = None
        self._patch_items = []

    def set_image(self, image_data: np.ndarray, reset_view=False):
        height, width = image_data.shape
        image_data_u8 = (image_data * 255).astype(np.uint8)
        q_image = QImage(image_data_u8.data, width, height, width, QImage.Format_Grayscale8)
        q_image.ndarray = image_data_u8
        pixmap = QPixmap.fromImage(q_image)

        if self._pixmap_item is None:
            self._pixmap_item = self.scene.addPixmap(pixmap)
        else:
            self._pixmap_item.setPixmap(pixmap)

        if reset_view:
            self.fitInView(self._pixmap_item, Qt.KeepAspectRatio)

    def clear_patches(self):
        for item in self._patch_items:
            self.scene.removeItem(item)
        self._patch_items = []

    def add_patch_overlay(self, x0, y0, w, h, color="lime", linewidth=1.0):
        pen = QPen(QColor(color))
        pen.setWidthF(linewidth)
        rect_item = self.scene.addRect(QRectF(x0, y0, w, h), pen)
        self._patch_items.append(rect_item)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._pixmap_item:
            self.origin = self.mapToScene(event.pos())
            self.rubber_band.setGeometry(QRect(event.pos(), QSize()))
            self.rubber_band.show()
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self.origin.isNull():
            end_point_scene = self.mapToScene(event.pos())
            rect_scene = QRectF(self.origin, end_point_scene).normalized()
            self.rubber_band.setGeometry(
                self.mapFromScene(rect_scene).boundingRect()
            )
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and not self.origin.isNull():
            self.rubber_band.hide()
            end_point_scene = self.mapToScene(event.pos())
            rect_scene = QRectF(self.origin, end_point_scene).normalized()
            self.region_selected.emit(rect_scene.toRect())
            self.origin = QPoint()
        super().mouseReleaseEvent(event)

    def zoom_in(self):
        self.scale(1.2, 1.2)

    def zoom_out(self):
        self.scale(1 / 1.2, 1 / 1.2)

    def resizeEvent(self, event):
        if self._pixmap_item:
            self.fitInView(self._pixmap_item, Qt.KeepAspectRatio)
        super().resizeEvent(event)
