
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QRubberBand
from PySide6.QtGui import QPixmap, QImage, QPen
from PySide6.QtCore import Signal, Qt, QRect, QPoint
import numpy as np

class ImageView(QGraphicsView):
    region_selected = Signal(int, int, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()

    def set_image(self, image_data: np.ndarray):
        self.scene.clear()
        height, width = image_data.shape

        # The data should already be normalized to [0, 1]
        image_data_u8 = (image_data * 255).astype(np.uint8)
        
        q_image = QImage(image_data_u8.data, width, height, width, QImage.Format_Grayscale8)
        
        # Keep a reference to the numpy array
        q_image.ndarray = image_data_u8
        
        pixmap = QPixmap.fromImage(q_image)
        self.scene.addPixmap(pixmap)
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.origin = event.pos()
            self.rubber_band.setGeometry(QRect(self.origin, QPoint()))
            self.rubber_band.show()

    def mouseMoveEvent(self, event):
        if not self.origin.isNull():
            self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and not self.origin.isNull():
            self.rubber_band.hide()
            rect = self.rubber_band.geometry()
            self.region_selected.emit(
                rect.left(), rect.top(), rect.right(), rect.bottom()
            )
            self.origin = QPoint()

    def add_patch_overlay(self, x0, y0, w, h, color="lime", linewidth=1.0):
        pen = QPen(color)
        pen.setWidthF(linewidth)
        rect_item = QGraphicsRectItem(x0, y0, w, h)
        rect_item.setPen(pen)
        self.scene.addItem(rect_item)

    def zoom_in(self):
        self.scale(1.2, 1.2)

    def zoom_out(self):
        self.scale(1 / 1.2, 1 / 1.2)
