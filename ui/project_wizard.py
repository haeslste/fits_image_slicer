
from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton

class ProjectWizard(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Project Wizard")
        self.layout = QVBoxLayout(self)
        self.choice = None

        self.new_project_button = QPushButton("Create New Project")
        self.open_project_button = QPushButton("Open Existing Project")

        self.layout.addWidget(self.new_project_button)
        self.layout.addWidget(self.open_project_button)

        self.new_project_button.clicked.connect(self.select_new)
        self.open_project_button.clicked.connect(self.select_open)

    def select_new(self):
        self.choice = "new"
        self.accept()

    def select_open(self):
        self.choice = "open"
        self.accept()
