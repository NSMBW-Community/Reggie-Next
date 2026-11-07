from PyQt6 import QtWidgets

from data import globals_

from data.level.items.path import PathItem
from ui.widgets.generic.list_with_tool_tip_signal import ListWidgetWithToolTipSignal

class PathTab(QtWidgets.QWidget):
    """
    Represents the Paths tab in the palette
    """
    def __init__(self):
        super().__init__(None)
        label = QtWidgets.QLabel(globals_.trans.string('palette.path.info'))
        label.setWordWrap(True)

        deselect_button = QtWidgets.QPushButton(globals_.trans.string('palette.path.deselect_button'))
        deselect_button.clicked.connect(self.deselect_path)

        self.path_list = ListWidgetWithToolTipSignal()
        self.path_list.itemActivated.connect(self.path_selected)
        self.path_list.toolTipAboutToShow.connect(self.path_hovered)
        self.path_list.setSortingEnabled(True)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(label)
        main_layout.addWidget(deselect_button)
        main_layout.addWidget(self.path_list)

    def deselect_path(self, checked):
        """
        Deselects selected path nodes in the list
        """
        for selecteditem in self.path_list.selectedItems():
            selecteditem.setSelected(False)

        # Also deselect nodes in the scene
        for item in globals_.mainWindow.scene.selectedItems():
            if isinstance(item, PathItem):
                item.setSelected(False)

    def path_selected(self, item):
        """
        Handle a path node being selected
        """
        path_item: PathItem = item.reference
        path_item.ensureVisible(xMargin=192, yMargin=192)
        globals_.mainWindow.scene.clearSelection()
        path_item.setSelected(True)

    def path_hovered(self, item):
        """
        Handle a path node being hovered in the list
        """
        item.reference.UpdateListItem(True)

    def set_item(self, item: PathItem) -> None:
        """
        Set the selected item
        """
        main_window = globals_.mainWindow
        main_window.palette_dock.set_tab(4)

        main_window.UpdateFlag = True
        self.path_list.setCurrentItem(item.listitem)
        main_window.UpdateFlag = False
