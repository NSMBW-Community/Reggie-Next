from PyQt6 import QtWidgets

from data import globals_

from data.level.items.location import LocationItem
from ui.widgets.generic.list_with_tool_tip_signal import ListWidgetWithToolTipSignal

class LocationTab(QtWidgets.QWidget):
    """
    Represents the Locations tab in the palette
    """
    def __init__(self):
        super().__init__(None)
        label = QtWidgets.QLabel(globals_.trans.string('Palette', 12))
        label.setWordWrap(True)

        self.location_list = ListWidgetWithToolTipSignal()
        self.location_list.itemActivated.connect(self.location_selected)
        self.location_list.toolTipAboutToShow.connect(self.location_hovered)
        self.location_list.setSortingEnabled(True)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(label)
        main_layout.addWidget(self.location_list)
        self.setLayout(main_layout)

    def location_selected(self, item):
        """
        Handle a location being selected from the list
        """
        if globals_.mainWindow is None:
            return
        if globals_.mainWindow.UpdateFlag:
            return

        loc: LocationItem = item.reference
        loc.ensureVisible(xMargin=192, yMargin=192)
        globals_.mainWindow.scene.clearSelection()
        loc.setSelected(True)

    def location_hovered(self, item):
        """
        Handle a location being hovered in the list
        """
        item.reference.UpdateListItem(True)
