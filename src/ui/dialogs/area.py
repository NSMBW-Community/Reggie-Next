from PyQt6 import QtWidgets

from data import globals_
from data.level.dirty import SetDirty
from ui.theme.reggie_theme import GetIcon

from ui.widgets.area.tilesets import TilesetsTab
from ui.widgets.area.settings import SettingsTab
from ui.widgets.area.loaded_sprites import LoadedSpritesTab

class AreaOptionsDialog(QtWidgets.QDialog):
    """
    Dialog which lets you choose among various area options from tabs
    """

    def __init__(self) -> None:
        """
        Creates and initializes the tab dialog
        """
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle(globals_.trans.string('AreaDlg', 0))
        self.setWindowIcon(GetIcon('wooden-box'))

        self.tilesets_tab = TilesetsTab()
        self.settings_tab = SettingsTab()
        self.loaded_sprites_tab = LoadedSpritesTab()

        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.addTab(self.tilesets_tab, GetIcon('document-block'), globals_.trans.string('AreaDlg', 1))
        self.tab_widget.addTab(self.settings_tab, GetIcon('gear'), globals_.trans.string('AreaDlg', 2))
        self.tab_widget.addTab(self.loaded_sprites_tab, GetIcon('rocket-exclamation-red'), globals_.trans.string('AreaDlg', 46))

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # Make space for the previews, if necessary
        if globals_.ShowTilesetPreview:
            self.setMinimumWidth(852)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self.tab_widget)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)

    def save(self) -> None:
        """
        Saves everything back to the area
        """
        self.tilesets_tab.save()
        self.settings_tab.save()
        self.loaded_sprites_tab.save()
        SetDirty()
