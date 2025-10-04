
from PySide6.QtWidgets import QTableView
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex

class PatchTableModel(QAbstractTableModel):
    def __init__(self, data=None, headers=None, parent=None):
        super().__init__(parent)
        self._data = data or []
        self._headers = headers or []

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            self._data[index.row()][index.column()] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def flags(self, index):
        flags = super().flags(index)
        if index.column() == self._headers.index("label"):
            flags |= Qt.ItemIsEditable
        return flags

class PatchTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = PatchTableModel(headers=["patch_id", "label"])
        self.setModel(self.model)

    def set_patches(self, patches_meta):
        data = [[p.get("patch_id"), p.get("label")] for p in patches_meta]
        self.model = PatchTableModel(data=data, headers=["patch_id", "label"])
        self.setModel(self.model)
