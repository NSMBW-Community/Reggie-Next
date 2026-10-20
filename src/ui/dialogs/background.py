from PyQt6 import QtWidgets

from data import globals_
from data.level.dirty import SetDirty
from ui.theme.reggie_theme import GetIcon
from ui.widgets.background_tab import BackgroundTab

class BackgroundDialog(QtWidgets.QDialog):
    """
    Dialog which lets you modify backgrounds
    """

    def __init__(self) -> None:
        """
        Creates and initializes the tab dialog
        """
        super().__init__()

        self.setWindowTitle(globals_.trans.string('BGDlg', 0))
        self.setWindowIcon(GetIcon('pictures'))

        self.tab_widget = QtWidgets.QTabWidget()
        self.tabs: list[BackgroundTab] = []

        for i, zone in enumerate(globals_.Area.zones):
            tab = BackgroundTab(zone)
            self.tabs.append(tab)

            name = globals_.trans.string('BGDlg', 2, '[num]', i + 1)
            self.tab_widget.addTab(tab, name)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self.tab_widget)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)

    def save(self) -> None:
        """
        Saves the background settings
        """
        SetDirty()

        for tab, zone in zip(self.tabs, globals_.Area.zones):
            scenery = tab.scenery
            backdrop = tab.backdrop

            zone.bg1A = scenery.hex_boxes[0].value()
            zone.bg2A = scenery.hex_boxes[1].value()
            zone.bg3A = scenery.hex_boxes[2].value()

            zone.XpositionA = scenery.pos_boxes[0].value()
            zone.YpositionA = -scenery.pos_boxes[1].value()

            zone.XscrollA = scenery.scroll_boxes[0].currentIndex()
            zone.YscrollA = scenery.scroll_boxes[1].currentIndex()

            zone.ZoomA = scenery.zoom_box.currentIndex()

            
            zone.bg1B = backdrop.hex_boxes[0].value()
            zone.bg2B = backdrop.hex_boxes[1].value()
            zone.bg3B = backdrop.hex_boxes[2].value()

            zone.XpositionB = backdrop.pos_boxes[0].value()
            zone.YpositionB = -backdrop.pos_boxes[1].value()

            zone.XscrollB = backdrop.scroll_boxes[0].currentIndex()
            zone.YscrollB = backdrop.scroll_boxes[1].currentIndex()

            zone.ZoomB = backdrop.zoom_box.currentIndex()
