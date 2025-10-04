
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QMenuBar, QFileDialog, QDockWidget,
    QStatusBar, QToolBar, QComboBox
)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt, Signal
from .image_view import ImageView
from .patch_table_view import PatchTableView

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FITS Image Slicer")
        self.resize(860, 640)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.image_view = ImageView()
        self.layout.addWidget(self.image_view)

        self.setStatusBar(QStatusBar(self))
        self._create_toolbar()
        self._create_patch_table_dock()
        self._create_menus()

    def _create_toolbar(self):
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.toolbar)

        self.prev_action = QAction("Previous", self)
        self.toolbar.addAction(self.prev_action)

        self.file_combo = QComboBox()
        self.toolbar.addWidget(self.file_combo)

        self.next_action = QAction("Next", self)
        self.toolbar.addAction(self.next_action)
        
        self.toolbar.addSeparator()

        self.zoom_in_action = QAction(QIcon.fromTheme("zoom-in"), "Zoom In", self)
        self.toolbar.addAction(self.zoom_in_action)
        
        self.zoom_out_action = QAction(QIcon.fromTheme("zoom-out"), "Zoom Out", self)
        self.toolbar.addAction(self.zoom_out_action)

        self.toolbar.addSeparator()

        self.stretch_combo = QComboBox()
        self.stretch_combo.addItems(["Z-Scale", "Linear", "Log", "Hist. Eq."])
        self.toolbar.addWidget(self.stretch_combo)

    def _create_menus(self):
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)

        file_menu = self.menu_bar.addMenu("&File")
        exit_action = QAction("&Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        project_menu = self.menu_bar.addMenu("&Project")
        self.add_files_action = QAction("&Add Files...", self)
        project_menu.addAction(self.add_files_action)

        edit_menu = self.menu_bar.addMenu("&Edit")
        self.undo_action = QAction("&Undo Last Patch", self)
        edit_menu.addAction(self.undo_action)
        self.clear_action = QAction("&Clear All Patches", self)
        edit_menu.addAction(self.clear_action)

        labels_menu = self.menu_bar.addMenu("&Labels")
        self.edit_labels_action = QAction("&Edit Labels...", self)
        labels_menu.addAction(self.edit_labels_action)

        view_menu = self.menu_bar.addMenu("&View")
        self.zscale_action = QAction("&Z-Scale", self)
        self.zscale_action.setCheckable(True)
        self.zscale_action.setChecked(True)
        view_menu.addAction(self.zscale_action)

        self.patch_table_dock_action = self.patch_table_dock.toggleViewAction()
        self.patch_table_dock_action.setText("&Patch Table")
        view_menu.addAction(self.patch_table_dock_action)

    def _create_patch_table_dock(self):
        self.patch_table_dock = QDockWidget("Patch Table", self)
        self.patch_table_view = PatchTableView()
        self.patch_table_dock.setWidget(self.patch_table_view)
        self.addDockWidget(Qt.RightDockWidgetArea, self.patch_table_dock)

    def update_status(self, message):
        self.statusBar().showMessage(message)
