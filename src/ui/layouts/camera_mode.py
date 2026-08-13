from PyQt6 import QtWidgets, QtCore
from typing import cast

import common
import globals_
from ui import GetIcon
from levelitems import ZoneItem

class CameraModeZoomSettingsLayout(QtWidgets.QFormLayout):
    """
    A layout that shows the camera mode / zoom settings for editing.
    Separate from Zone Options so it can be reused for Camera Profiles
    """
    edited = QtCore.pyqtSignal()
    updating = False

    def __init__(self, showCamMode5: bool):
        super().__init__()
        self.updating = True

        comboboxSizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.zoomMode = -1

        self.modeButtonGroup = QtWidgets.QButtonGroup()
        modeButtons = []
        for i, name, tooltip in [
                    (0, globals_.trans.string('ZonesDlg', 85), globals_.trans.string('ZonesDlg', 86)),  # Normal
                    (3, globals_.trans.string('ZonesDlg', 87), globals_.trans.string('ZonesDlg', 88)),  # Static
                    (4, globals_.trans.string('ZonesDlg', 89), globals_.trans.string('ZonesDlg', 90)),  # Static, Y Track
                    (5, globals_.trans.string('ZonesDlg', 91), globals_.trans.string('ZonesDlg', 92)),  # Static, Event
                    (6, globals_.trans.string('ZonesDlg', 93), globals_.trans.string('ZonesDlg', 94)),  # X Track
                    (7, globals_.trans.string('ZonesDlg', 95), globals_.trans.string('ZonesDlg', 96)),  # X Expand
                    (1, globals_.trans.string('ZonesDlg', 97), globals_.trans.string('ZonesDlg', 98)),  # Y Track
                    (2, globals_.trans.string('ZonesDlg', 99), globals_.trans.string('ZonesDlg', 100)), # Y Expand
                ]:
            rb = QtWidgets.QRadioButton(name)
            rb.setToolTip(f'<b>{name}:</b><br>{tooltip}')
            self.modeButtonGroup.addButton(rb, i)
            modeButtons.append(rb)

            # Hides "Static Zoom, Event Controlled"
            if i == 5 and not showCamMode5:
                rb.setVisible(False)

            rb.clicked.connect(self.changeCamModeList)
            rb.clicked.connect(self.handleModeChanged)

        self.screenSizes = QtWidgets.QComboBox()
        self.screenSizes.setToolTip(globals_.trans.string('ZonesDlg', 102))
        self.screenSizes.setSizePolicy(comboboxSizePolicy)

        self.screenSizes.currentIndexChanged.connect(self.handleScreenSizesChanged)

        modesLyt = QtWidgets.QGridLayout()
        for i, btn in enumerate(modeButtons):
            modesLyt.addWidget(btn, i % 4, i // 4)

        self.addRow(modesLyt)
        self.addRow(globals_.trans.string('ZonesDlg', 101), self.screenSizes)

        self.updating = False

    def changeCamModeList(self):
        """
        Handles changing the available Screen Heights items
        """
        mode = self.modeButtonGroup.checkedId()
        oldListChoice = [1, 1, 2, 3, 3, 3, 1, 1][self.zoomMode]
        newListChoice = [1, 1, 2, 3, 3, 3, 1, 1][mode]

        if self.zoomMode != -1 and oldListChoice == newListChoice:
            return

        if newListChoice == 1:
            sizes = [
                ([14, 19], ''),
                ([14, 19, 24], ''),
                ([14, 19, 28], ''),
                ([20, 24], ''),
                ([19, 24, 28], ''),
                ([17, 24], ''),
                ([17, 24, 28], ''),
                ([17, 20], ''),
                ([7, 11, 28], '**'),
                ([17, 20.5, 24], ''),
                ([17, 20, 28], ''),
            ]
        elif newListChoice == 2:
            sizes = [
                ([14, 19], ''),
                ([14, 19, 24], ''),
                ([14, 19, 28], ''),
                ([19, 19, 24], ''),
                ([19, 24, 28], ''),
                ([19, 24, 28], ''),
                ([17, 24, 28], ''),
                ([17, 20.5, 24], ''),
            ]
        else:
            sizes = [
                ([14], ''),
                ([19], ''),
                ([24], ''),
                ([28], ''),
                ([17], ''),
                ([20], ''),
                ([16], ''),
                ([28], ''),
                ([7], '*'),
                ([10.5], '*'),
            ]

        items = []
        for i, (options, asterisk) in enumerate(sizes):
            items.append(', '.join(str(o) for o in options) + asterisk)

        self.screenSizes.clear()
        self.screenSizes.addItems(items)
        self.screenSizes.setCurrentIndex(0)
        self.zoomMode = mode

    def setValues(self, camMode, camZoom):
        self.updating = True
        camMode = common.clamp(camMode, 0, 7)

        button = self.modeButtonGroup.button(camMode)
        if button is not None:
            button.setChecked(True)
        self.changeCamModeList()

        camZoom = common.clamp(camZoom, 0, self.screenSizes.count())

        self.screenSizes.setCurrentIndex(camZoom)
        self.updating = False

    def handleModeChanged(self):
        """
        Handles the camera mode being changed
        """
        if self.updating:
            return
        self.changeCamModeList()
        self.edited.emit()

    def handleScreenSizesChanged(self):
        """
        Handles the screen size being changed
        """
        if self.updating:
            return
        self.edited.emit()
