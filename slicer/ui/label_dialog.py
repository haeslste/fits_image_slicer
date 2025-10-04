
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QLineEdit, QPushButton, QInputDialog

class LabelDialog(QDialog):
    def __init__(self, parent=None, labels=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Labels")
        self.layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        if labels:
            self.list_widget.addItems(labels)
        self.layout.addWidget(self.list_widget)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add")
        self.edit_button = QPushButton("Edit")
        self.remove_button = QPushButton("Remove")
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.remove_button)
        self.layout.addLayout(button_layout)

        self.add_button.clicked.connect(self.add_label)
        self.edit_button.clicked.connect(self.edit_label)
        self.remove_button.clicked.connect(self.remove_label)

    def add_label(self):
        text, ok = QInputDialog.getText(self, "Add Label", "Label name:")
        if ok and text:
            self.list_widget.addItem(text)

    def edit_label(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            text, ok = QInputDialog.getText(
                self, "Edit Label", "New label name:", QLineEdit.Normal, current_item.text()
            )
            if ok and text:
                current_item.setText(text)

    def remove_label(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            self.list_widget.takeItem(self.list_widget.row(current_item))

    def get_labels(self):
        return [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
