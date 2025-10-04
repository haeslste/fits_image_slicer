
from PySide6.QtWidgets import QStyledItemDelegate, QComboBox

class LabelDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, labels=None):
        super().__init__(parent)
        self.labels = labels or []

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(self.labels)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, 0)
        if value:
            editor.setCurrentText(value)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), 0)
