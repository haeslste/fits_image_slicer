
from PySide6.QtWidgets import QDialog, QVBoxLayout, QComboBox, QDialogButtonBox

class AssignLabelDialog(QDialog):
    def __init__(self, parent=None, labels=None):
        super().__init__(parent)
        self.setWindowTitle("Assign Label")
        self.layout = QVBoxLayout(self)

        self.combo_box = QComboBox()
        if labels:
            self.combo_box.addItems(labels)
        self.layout.addWidget(self.combo_box)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_selected_label(self):
        return self.combo_box.currentText()
