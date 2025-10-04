
import os
from PySide6.QtCore import QObject, Slot, QRect
from PySide6.QtWidgets import QMessageBox
from ui.main_window import MainWindow
from ui.assign_label_dialog import AssignLabelDialog
from ui.add_files_dialog import AddFilesDialog
from models import FitsImageModel, PatchExporter
from project import Project, _normalize_path

class Controller(QObject):
    def __init__(self, main_window: MainWindow, project: Project):
        super().__init__()
        self.main_window = main_window
        self.project = project
        self.cfg = project.config
        self.current_file_index = 0
        self.fits_image_model: FitsImageModel = None
        self.patch_exporter: PatchExporter = None

        self._connect_signals()
        self.load_current_file()

    def _connect_signals(self):
        self.main_window.image_view.region_selected.connect(self.on_region_selected)
        
        # Connect toolbar actions
        self.main_window.next_action.triggered.connect(self.next_file)
        self.main_window.prev_action.triggered.connect(self.prev_file)
        self.main_window.file_combo.currentIndexChanged.connect(self.jump_to_file)
        
        self.main_window.zoom_in_action.triggered.connect(self.main_window.image_view.zoom_in)
        self.main_window.zoom_out_action.triggered.connect(self.main_window.image_view.zoom_out)
        self.main_window.stretch_combo.currentTextChanged.connect(self.change_stretch_mode)

        self.main_window.undo_action.triggered.connect(self.undo_last_patch)
        self.main_window.clear_action.triggered.connect(self.clear_all_patches)
        self.main_window.edit_labels_action.triggered.connect(self.edit_labels)
        self.main_window.add_files_action.triggered.connect(self.add_files_to_project)

    def load_current_file(self):
        self._update_file_combo()
        
        self.main_window.stretch_combo.blockSignals(True)
        self.main_window.stretch_combo.setCurrentText(self.cfg.stretch_mode.title())
        self.main_window.stretch_combo.blockSignals(False)
        
        file_path = self.project.files[self.current_file_index]
        try:
            self.fits_image_model = FitsImageModel(file_path)
            self.patch_exporter = PatchExporter(self.cfg, self.fits_image_model)
            
            current_patches = self.project.patches.get(_normalize_path(file_path), [])
            self.patch_exporter.patches_meta = current_patches
            
            image_data = self.fits_image_model.get_normalized_image_data(
                stretch_mode=self.cfg.stretch_mode
            )
            self.main_window.image_view.set_image(image_data, reset_view=True)
            self.main_window.update_status(f"Loaded {os.path.basename(file_path)}")
            self.main_window.setWindowTitle(f"{self.project.name} - FITS Image Slicer")
            self._refresh_overlays()
        except Exception as e:
            QMessageBox.critical(self.main_window, "Error", f"Error loading FITS file: {e}")

    def _refresh_overlays(self):
        self.main_window.image_view.clear_patches()
        for patch_meta in self.patch_exporter.patches_meta:
            color = self.cfg.get_color_for_label(patch_meta.get("label"))
            self.main_window.image_view.add_patch_overlay(
                patch_meta["x0"],
                patch_meta["y0"],
                patch_meta["width"],
                patch_meta["height"],
                color=color,
                linewidth=self.cfg.overlay_linewidth,
            )
        self.main_window.patch_table_view.set_patches(self.patch_exporter.patches_meta)

    def _update_file_combo(self):
        self.main_window.file_combo.blockSignals(True)
        self.main_window.file_combo.clear()
        self.main_window.file_combo.addItems([os.path.basename(f) for f in self.project.files])
        self.main_window.file_combo.setCurrentIndex(self.current_file_index)
        self.main_window.file_combo.blockSignals(False)

    @Slot()
    def next_file(self):
        if self.current_file_index < len(self.project.files) - 1:
            self.current_file_index += 1
            self.load_current_file()

    @Slot()
    def prev_file(self):
        if self.current_file_index > 0:
            self.current_file_index -= 1
            self.load_current_file()
            
    @Slot(int)
    def jump_to_file(self, index):
        if self.current_file_index != index and 0 <= index < len(self.project.files):
            self.current_file_index = index
            self.load_current_file()

    @Slot(QRect)
    def on_region_selected(self, rect: QRect):
        if self.patch_exporter:
            x0, y0, x1, y1 = rect.left(), rect.top(), rect.right(), rect.bottom()
            
            label = None
            if self.cfg.labels:
                dialog = AssignLabelDialog(self.main_window, self.cfg.labels)
                if dialog.exec():
                    label = dialog.get_selected_label()
                else:
                    return # User cancelled
            
            patch_meta = self.patch_exporter.save_patch(x0, y0, x1, y1, label)

            if patch_meta:
                self._update_project_patches()
                self._refresh_overlays()

    def _update_project_patches(self):
        file_path = _normalize_path(self.project.files[self.current_file_index])
        self.project.patches[file_path] = self.patch_exporter.patches_meta
        self.project.save()

    @Slot()
    def undo_last_patch(self):
        if self.patch_exporter:
            self.patch_exporter.undo_last_patch()
            self._update_project_patches()
            self._refresh_overlays()

    @Slot()
    def clear_all_patches(self):
        if self.patch_exporter:
            self.patch_exporter.clear_all_patches()
            self._update_project_patches()
            self._refresh_overlays()

    @Slot(str)
    def change_stretch_mode(self, mode):
        mode_map = {
            "Z-Scale": "zscale",
            "Linear": "linear",
            "Log": "log",
            "Hist. Eq.": "histeq"
        }
        self.cfg.stretch_mode = mode_map.get(mode, "zscale")
        
        if self.fits_image_model:
            image_data = self.fits_image_model.get_normalized_image_data(
                stretch_mode=self.cfg.stretch_mode
            )
            self.main_window.image_view.set_image(image_data, reset_view=False)


    @Slot()
    def edit_labels(self):
        dialog = LabelDialog(self.main_window, self.cfg.labels)
        if dialog.exec():
            self.cfg.labels = dialog.get_labels()
            self.project.save()

    @Slot()
    def add_files_to_project(self):
        dialog = AddFilesDialog(self.main_window)
        if dialog.exec():
            new_files = dialog.get_files()
            if new_files:
                self.project.add_files(new_files)
                self._update_file_combo() # Refresh file list
