from PyQt6 import QtCore, QtWidgets, QtGui
import os

import globals_
from dirty import setting
from levelitems import Path, CommentItem
from misc2 import LevelViewWidget
from src.ui.theme.reggie_theme import ReggieTheme

from src.ui.widgets.preferences.widgets.preference_tab import PreferenceTabWidget

class AppearanceTab(PreferenceTabWidget):
    """
    Appearance Tab
    """

    def __init__(self, info_text):
        """
        Initializes the Appearance Tab
        """
        super().__init__(info_text)

        # Get the current and available themes
        self.theme_id = globals_.theme.themeName
        self.themes = self.get_themes

        # Create the theme box
        self.theme_combo = QtWidgets.QComboBox()
        for name, theme_obj in self.themes:
            self.theme_combo.addItem(name)

        index = self.theme_combo.findText(setting('Theme'), QtCore.Qt.MatchFlag.MatchFixedString)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

        self.theme_combo.currentIndexChanged.connect(self.update_preview)

        # Create the window style options
        keys = QtWidgets.QStyleFactory().keys()
        self.window_style = QtWidgets.QComboBox()
        self.window_style.setToolTip(globals_.trans.string('PrefsDlg', 24))
        self.window_style.addItems(keys)

        ui_style = setting('uiStyle', "Fusion")
        if ui_style in keys:
            self.window_style.setCurrentIndex(keys.index(ui_style))

        # Use Rounded Rectangles
        self.rounded_rects = QtWidgets.QCheckBox(globals_.trans.string('PrefsDlg', 45))
        self.rounded_rects.setToolTip(globals_.trans.string('PrefsDlg', 46))
        self.rounded_rects.setChecked(globals_.UseRoundedRectangles)
        self.rounded_rects.clicked.connect(self.update_preview)

        # Dark Mode
        self.dark_mode = QtWidgets.QCheckBox(globals_.trans.string('PrefsDlg', 47))
        self.dark_mode.setToolTip(globals_.trans.string('PrefsDlg', 48))
        self.dark_mode.setChecked(globals_.DarkMode)

        # Tilesets Tab Position
        self.tileset_tab_pos = QtWidgets.QComboBox()
        self.tileset_tab_pos.setToolTip(globals_.trans.string('PrefsDlg', 67))
        self.tileset_tab_pos.addItems(globals_.trans.stringList('PrefsDlg', 68))
        self.tileset_tab_pos.setCurrentIndex(globals_.TilesetTabPos)

        settings_box = QtWidgets.QGroupBox(globals_.trans.string('PrefsDlg', 40))
        L = QtWidgets.QFormLayout()
        L.addRow(globals_.trans.string('PrefsDlg', 41), self.theme_combo)
        L.addRow(globals_.trans.string('PrefsDlg', 25), self.window_style)
        L.addRow(self.dark_mode)
        L.addRow(self.rounded_rects)
        L.addRow(globals_.trans.string('PrefsDlg', 66), self.tileset_tab_pos)
        L2 = QtWidgets.QGridLayout()
        L2.addLayout(L, 0, 0)
        settings_box.setLayout(L2)

        # Temp options to modify the preview rendering
        self.preview_selected = QtWidgets.QCheckBox(globals_.trans.string('PrefsDlg', 50))
        self.preview_selected.clicked.connect(self.update_preview)

        curr_grid = 0
        if globals_.GridType is not None:
            if globals_.GridType == 'grid':
                curr_grid = 1
            else:
                curr_grid = 2

        self.preview_grid_type = QtWidgets.QComboBox()
        self.preview_grid_type.addItems(globals_.trans.stringList('PrefsDlg', 52))
        self.preview_grid_type.setCurrentIndex(curr_grid)
        self.preview_grid_type.currentIndexChanged.connect(self.update_preview)

        L = QtWidgets.QHBoxLayout()
        L.addWidget(QtWidgets.QLabel(globals_.trans.string('PrefsDlg', 51)))
        L.addWidget(self.preview_grid_type)
        L.addSpacing(5)
        L.addWidget(self.preview_selected)
        L.addStretch(1)

        # Create the preview labels and groupbox
        self.preview = QtWidgets.QLabel()
        self.description = QtWidgets.QLabel()
        L2 = QtWidgets.QVBoxLayout()
        L2.addLayout(L)
        L2.addWidget(self.preview)
        L2.addWidget(self.description)
        L2.addStretch(1)

        preview_box = QtWidgets.QGroupBox(globals_.trans.string('PrefsDlg', 22))
        preview_box.setLayout(L2)

        # Create a main layout
        main_layout = QtWidgets.QGridLayout()
        main_layout.addWidget(settings_box, 0, 0)
        main_layout.addWidget(preview_box, 0, 1)
        main_layout.setRowStretch(1, 1)
        self.setLayout(main_layout)

        # Update the preview image
        self.update_preview()

    @property
    def get_themes(self):
        """
        Searches the Themes folder and returns a list of theme filepaths.
        Automatically adds 'Classic' to the list.
        """
        theme_path = os.path.join('reggiedata', 'themes')
        theme_list = [('Classic', ReggieTheme())]

        for theme_name in os.listdir(theme_path):
            if not os.path.isdir(os.path.join(theme_path, theme_name)):
                continue

            try:
                theme = ReggieTheme(theme_name)
            except Exception:
                continue

            theme_list.append((theme_name, theme))

        return tuple(theme_list)

    def update_preview(self):
        """
        Updates the preview and theme box
        """
        for name, themeObj in self.themes:
            if name == self.theme_combo.currentText():
                t = themeObj
                self.preview.setPixmap(self.draw_preview(t))
                text = globals_.trans.string('PrefsDlg', 26, '[name]', t.themeName, '[version]', t.version,
                                    '[creator]', t.creator, '[description]', t.description)
                self.description.setText(text)

    def draw_preview(self, theme):
        """
        Returns a preview pixmap for the given theme
        """
        if globals_.mainWindow is None:
            pixmap = QtGui.QPixmap(32 * 16, 17 * 16)
            pixmap.fill(theme.color('bg'))
            return pixmap

        scene = QtWidgets.QGraphicsScene(0, 0, 32 * 16, 17 * 16, self)
        old_theme, old_real_view, old_round_rect, old_grid = globals_.theme, globals_.RealViewEnabled, globals_.UseRoundedRectangles, globals_.GridType
        globals_.theme = theme
        globals_.UseRoundedRectangles = self.rounded_rects.isChecked()
        globals_.RealViewEnabled = False  # Disable so the zone looks 'plain'
        set_select = self.preview_selected.isChecked()

        grid_type = self.preview_grid_type.currentIndex()
        types = [None, 'grid', 'checker']
        globals_.GridType = types[grid_type]

        # Sprite [38] at (11, 4)
        sprite = globals_.mainWindow.CreateSprite(11 * 16, 4 * 16, 38, data=bytes(8), add_to_scene=False)
        scene.addItem(sprite)

        # Sprite [53] at (1, 6)
        sprite = globals_.mainWindow.CreateSprite(1 * 16, 6 * 16, 53, data=bytes(8), add_to_scene=False)
        scene.addItem(sprite)

        # Entrance [0] at (13, 8)
        ent = globals_.mainWindow.CreateEntrance(13 * 16, 8 * 16, 0, add_to_scene=False)
        scene.addItem(ent)

        # Location [1] at (1, 9) size (6, 2)
        loc = globals_.mainWindow.CreateLocation(1 * 16, 9 * 16, 6 * 16, 2 * 16, 1, add_to_scene=False)
        scene.addItem(loc)

        # Zone [1] at (8.5, 3.25) size (16, 7.5)
        zone = globals_.mainWindow.CreateZone(8.5 * 16, 3.25 * 16, 16 * 16, int(7.5 * 16), id_=1, add_to_scene=False)
        scene.addItem(zone)

        # Path [1] making a rectangle shape between (13, 5) and (18, 9)
        path = Path(1, scene, loops=True)

        for x, y in ((13, 5), (18, 5), (18, 9), (13, 9)):
            path.add_node(x * 16, y * 16, add_to_list=False)

        # Empty comment at (2, 3)
        comment = CommentItem(2 * 16, 3 * 16, '')
        scene.addItem(comment)

        # Toggle item selection
        for item in scene.items():
            item.setSelected(set_select)

        # Take a screenshot
        pixmap = QtGui.QPixmap(32 * 16, 17 * 16)
        pixmap.fill(theme.color('bg'))

        rect = QtCore.QRectF(0, 0, 32 * 16, 17 * 16)

        painter = QtGui.QPainter(pixmap)
        scene.render(painter, rect, rect)

        # Add grid
        temp_widget = LevelViewWidget(scene, None)
        temp_widget.drawForeground(painter, rect)

        painter.end()

        # Restore globals that were changed
        globals_.theme = old_theme
        globals_.RealViewEnabled = old_real_view
        globals_.UseRoundedRectangles = old_round_rect
        globals_.GridType = old_grid

        return pixmap
