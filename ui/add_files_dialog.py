
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFileDialog,
    QListWidget, QDialogButtonBox, QPushButton
)

class AddFilesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Files to Project")
        self.layout = QVBoxLayout(self)
        self.setMinimumWidth(400)

        self.file_list = QListWidget()
        self.layout.addWidget(self.file_list)
        
        file_buttons_layout = QHBoxLayout()
        self.add_files_button = QPushButton("Add Files...")
        self.add_folder_button = QPushButton("Add Folder...")
        file_buttons_layout.addWidget(self.add_files_button)
        file_buttons_layout.addWidget(self.add_folder_button)
        self.layout.addLayout(file_buttons_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.layout.addWidget(self.button_box)

        self.add_files_button.clicked.connect(self.add_files)
        self.add_folder_button.clicked.connect(self.add_folder)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select FITS Files", "", "FITS Files (*.fits *.fit *.fz)")
        if files:
            self.file_list.addItems(files)

    def add_folder(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Folder")
        if directory:
            for filename in os.listdir(directory):
                if filename.lower().endswith(('.fits', '.fit', '.fz')):
                    self.file_list.addItem(os.path.join(directory, filename))

    def get_files(self):
        return [self.file_list.item(i).text() for i in range(self.file_list.count())]
