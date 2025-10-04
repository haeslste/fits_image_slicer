
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QDialogButtonBox, QLabel
)

class ConfirmAddFilesDialog(QDialog):
    def __init__(self, new_files, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Files Found")
        self.layout = QVBoxLayout(self)
        self.setMinimumWidth(450)

        self.layout.addWidget(QLabel("The following new FITS files were found. Add them to the project?"))

        self.file_list = QListWidget()
        self.file_list.addItems(new_files)
        self.layout.addWidget(self.file_list)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Yes | QDialogButtonBox.No)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)
