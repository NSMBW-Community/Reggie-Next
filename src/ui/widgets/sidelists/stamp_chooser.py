from PyQt6 import QtCore, QtWidgets

from src.data.stamp.stamp_list import StampListModel


class StampChooserWidget(QtWidgets.QListView):
    """
    Widget that shows a list of available stamps
    """
    selectionChangedSignal = QtCore.pyqtSignal()

    def __init__(self):
        """
        Initializes the widget
        """
        QtWidgets.QListView.__init__(self)

        self.setFlow(QtWidgets.QListView.Flow.LeftToRight)
        self.setLayoutMode(QtWidgets.QListView.LayoutMode.SinglePass)
        self.setMovement(QtWidgets.QListView.Movement.Static)
        self.setResizeMode(QtWidgets.QListView.ResizeMode.Adjust)
        self.setWrapping(True)

        self.setModel(StampListModel())

        self.setItemDelegate(StampChooserWidget.StampItemDelegate())

    class StampItemDelegate(QtWidgets.QStyledItemDelegate):
        """
        Handles stamp rendering
        """

        def __init__(self):
            """
            Initializes the delegate
            """
            QtWidgets.QStyledItemDelegate.__init__(self)

        def createEditor(self, parent, option, index):
            """
            Creates a stamp name editor
            """
            return QtWidgets.QLineEdit(parent)

        def setEditorData(self, editor, index):
            """
            Sets the data for the stamp name editor from the data at index
            """
            model = index.model()
            if editor is None or model is None:
                return

            editor.setText(model.data(index, QtCore.Qt.ItemDataRole.UserRole + 1))

        def setModelData(self, editor, model, index):
            """
            Set the data in the model for the data at index
            """
            indexed_model = index.model()
            if indexed_model is None or editor is None:
                return

            indexed_model.setData(index, editor.text())

        def paint(self, painter, option, index):
            """
            Paints a stamp
            """
            model = index.model()
            if painter is None or model is None:
                return

            if option.state & QtWidgets.QStyle.StateFlag.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())

            painter.drawPixmap(option.rect.x() + 2, option.rect.y() + 2, model.data(index, QtCore.Qt.ItemDataRole.DecorationRole))

        def sizeHint(self, option, index):
            """
            Returns the size for the stamp
            """
            model = index.model()
            if model is None:
                return QtCore.QSize(0, 0)

            return model.data(index, QtCore.Qt.ItemDataRole.DecorationRole).size() + QtCore.QSize(4, 4)

    def addStamp(self, stamp):
        """
        Adds a stamp
        """
        model = self.model()
        if not isinstance(model, StampListModel):
            return

        model.addStamp(stamp)

    def removeStamp(self, stamp):
        """
        Removes a stamp
        """

        model = self.model()
        if not isinstance(model, StampListModel):
            return

        model.removeStamp(stamp)

    def currentlySelectedStamp(self):
        """
        Returns the currently selected stamp
        """
        idxobj = self.currentIndex()
        if idxobj.row() == -1: return
        model = self.model()
        if not isinstance(model, StampListModel):
            return

        return model.items[idxobj.row()]

    def selectionChanged(self, selected, deselected):
        """
        Called when the selection changes.
        """
        val = super().selectionChanged(selected, deselected)
        self.selectionChangedSignal.emit()
        return val
