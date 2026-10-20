from PyQt6 import QtWidgets

from data.level.items.zone import ZoneItem
from ui.layouts.background_editor import BackgroundEditorLayout

class BackgroundTab(QtWidgets.QWidget):
    """
    Tab representing a Zone's bgA and bgB
    """

    def __init__(self, zone: ZoneItem) -> None:
        """
        Initializes the tab
        """
        super().__init__()
        self.scenery = BackgroundEditorLayout(zone, False)
        self.backdrop = BackgroundEditorLayout(zone, True)

        main_layout = QtWidgets.QGridLayout()
        main_layout.addLayout(self.scenery, 0, 0)
        main_layout.addLayout(self.backdrop, 1, 0)
        self.setLayout(main_layout)
