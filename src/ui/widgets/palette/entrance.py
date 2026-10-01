from PyQt6 import QtWidgets

from data import globals_

from data.level.items.entrance import EntranceItem
from ui.widgets.generic.list_with_tool_tip_signal import ListWidgetWithToolTipSignal

class EntranceTab(QtWidgets.QWidget):
    """
    Represents the Entrances tab in the palette
    """
    def __init__(self):
        super().__init__(None)
        label = QtWidgets.QLabel(globals_.trans.string('Palette', 8))
        label.setWordWrap(True)

        self.entrance_list = ListWidgetWithToolTipSignal()
        self.entrance_list.itemActivated.connect(self.entrance_selected)
        self.entrance_list.toolTipAboutToShow.connect(self.entrance_hovered)
        self.entrance_list.setSortingEnabled(True)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(label)
        main_layout.addWidget(self.entrance_list)

    def entrance_selected(self, item):
        """
        Handle an entrance being selected from the list
        """
        if globals_.mainWindow is None:
            return
        if globals_.mainWindow.UpdateFlag:
            return

        ent: EntranceItem = item.reference
        ent.ensureVisible(xMargin=192, yMargin=192)
        globals_.mainWindow.scene.clearSelection()
        ent.setSelected(True)

    def entrance_hovered(self, item: EntranceItem):
        """
        Handle an entrance being hovered in the list
        """
        ent: EntranceItem
        for ent in globals_.Area.entrances:
            if ent.listitem == item:
                ent.UpdateListItem(True)
                break
