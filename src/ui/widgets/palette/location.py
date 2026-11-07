from typing import cast

from PyQt6 import QtWidgets

from data import globals_
from data.level.items.location import LocationItem
from ui.widgets.generic.list_with_tool_tip_signal import ListWidgetWithToolTipSignal
from ui.widgets.item_sorts_by_other import ListWidgetItem_SortsByOther


class LocationTab(QtWidgets.QWidget):
    """
    Represents the Locations tab in the palette
    """
    def __init__(self) -> None:
        super().__init__(None)
        label = QtWidgets.QLabel(globals_.trans.string('palette.location.info'))
        label.setWordWrap(True)

        self.location_list = ListWidgetWithToolTipSignal()
        self.location_list.itemActivated.connect(self.location_selected)
        self.location_list.toolTipAboutToShow.connect(self.location_hovered)
        self.location_list.setSortingEnabled(True)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(label)
        main_layout.addWidget(self.location_list)
        self.setLayout(main_layout)

    def location_selected(self, item: ListWidgetItem_SortsByOther) -> None:
        """
        Handle a location being selected from the list
        """
        if globals_.mainWindow.UpdateFlag:
            return

        loc: LocationItem = cast(LocationItem, item.reference)
        loc.ensureVisible(xMargin=192, yMargin=192)
        globals_.mainWindow.scene.clearSelection()
        loc.setSelected(True)

    def location_hovered(self, item: ListWidgetItem_SortsByOther) -> None:
        """
        Handle a location being hovered in the list
        """
        item.reference.UpdateListItem(True)

    def set_item(self, item: LocationItem) -> None:
        """
        Set the selected item
        """
        main_window = globals_.mainWindow
        main_window.palette_dock.set_tab(3)

        main_window.UpdateFlag = True
        self.location_list.setCurrentItem(item.listitem)
        main_window.UpdateFlag = False
