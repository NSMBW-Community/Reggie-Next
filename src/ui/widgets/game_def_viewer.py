from PyQt6 import QtWidgets, QtGui

from ui import GetIcon, createVertLine
import globals_

class GameDefViewer(QtWidgets.QWidget):
    """
    Widget which displays basic info about the current game definition
    """

    def __init__(self):
        """
        Initializes the widget
        """
        QtWidgets.QWidget.__init__(self)

        # "Has Sprite Images" indicator
        self.sprite_img_label = QtWidgets.QLabel()
        self.sprite_img_label.setToolTip(globals_.trans.string('Gamedefs', 0))
        self.sprite_img_label.setPixmap(GetIcon('sprites', False).pixmap(16, 16))

        self.version_label = QtWidgets.QLabel()

        self.title_label = QtWidgets.QLabel()
        self.title_label.setWordWrap(True)

        self.description_label = QtWidgets.QLabel()
        self.description_label.setWordWrap(True)
        self.description_label.setMinimumHeight(40)

        # Make layouts
        left_layout = QtWidgets.QVBoxLayout()
        left_layout.addWidget(self.sprite_img_label)
        left_layout.addWidget(self.version_label)
        left_layout.addStretch(1)

        right_layout = QtWidgets.QVBoxLayout()
        right_layout.addWidget(self.title_label)
        right_layout.addWidget(self.description_label)
        right_layout.addStretch(1)

        main_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(left_layout)
        main_layout.addWidget(createVertLine())
        main_layout.addLayout(right_layout)
        main_layout.setStretch(2, 1)
        self.setLayout(main_layout)

        self.setMinimumWidth(235)
        self.setMaximumWidth(320)

        self.set_info()

    def set_info(self):
        """
        Updates all info
        """
        sprite_folders = globals_.gamedef.recursiveFiles('sprites', is_folder=True)[0]

        if not globals_.gamedef.custom or sprite_folders:
            img = GetIcon('sprites', False).pixmap(16, 16)
        else:
            img = QtGui.QPixmap(16, 16)
            img.fill(QtGui.QColor(0, 0, 0, 0))

        if globals_.gamedef.version is None:
            ver = ''
        else:
            ver = '<p style="font-size:10px;">v%s</p>' % str(globals_.gamedef.version)
        title = '<b>%s</b>' % str(globals_.gamedef.name)
        desc = str(globals_.gamedef.description)

        self.sprite_img_label.setPixmap(img)
        self.version_label.setText(ver)
        self.title_label.setText(title)
        self.description_label.setText(desc)
