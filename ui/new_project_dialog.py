
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QFileDialog,
    QListWidget, QDialogButtonBox, QLabel
)

class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Project")
        self.layout = QVBoxLayout(self)
        self.setMinimumWidth(400)

        # Project Name
        self.layout.addWidget(QLabel("Project Name:"))
        self.project_name = QLineEdit()
        self.layout.addWidget(self.project_name)

        # Project Directory
        self.layout.addWidget(QLabel("Project Directory:"))
        dir_layout = QHBoxLayout()
        self.project_dir = QLineEdit()
        self.browse_button = QPushButton("Browse...")
        dir_layout.addWidget(self.project_dir)
        dir_layout.addWidget(self.browse_button)
        self.layout.addLayout(dir_layout)

        # FITS Files
        self.layout.addWidget(QLabel("FITS Files:"))
        self.file_list = QListWidget()
        self.layout.addWidget(self.file_list)
        
        file_buttons_layout = QHBoxLayout()
        self.add_files_button = QPushButton("Add Files...")
        self.add_folder_button = QPushButton("Add Folder...")
        file_buttons_layout.addWidget(self.add_files_button)
        file_buttons_layout.addWidget(self.add_folder_button)
        self.layout.addLayout(file_buttons_layout)

        # Dialog Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.layout.addWidget(self.button_box)

        # Connections
        self.browse_button.clicked.connect(self.browse_directory)
        self.add_files_button.clicked.connect(self.add_files)
        self.add_folder_button.clicked.connect(self.add_folder)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if directory:
            self.project_dir.setText(directory)

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

    def get_project_details(self):
        return {
            "name": self.project_name.text(),
            "directory": self.project_dir.text(),
            "files": [self.file_list.item(i).text() for i in range(self.file_list.count())]
        }
