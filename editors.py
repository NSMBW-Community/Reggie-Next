from PyQt5 import QtWidgets, QtCore
import sys

import globals_
from ui import createHorzLine
from dirty import SetDirty
from misc import LoadEntranceNames

class EntranceEditorWidget(QtWidgets.QWidget):
    """
    Widget for editing entrance properties
    """

    def __init__(self, defaultmode=False):
        """
        Constructor
        """
        QtWidgets.QWidget.__init__(self)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))

        LoadEntranceNames()
        self.CanUseFlag40 = {0, 1, 7, 8, 9, 12, 20, 21, 22, 23, 24, 27}
        self.CanUseFlag8 = {3, 4, 5, 6, 16, 17, 18, 19}
        self.CanUseFlag4 = {3, 4, 5, 6}

        # create widgets
        self.entranceID = QtWidgets.QSpinBox()
        self.entranceID.setRange(0, 255)
        self.entranceID.setToolTip(globals_.trans.string('EntranceDataEditor', 1))
        self.entranceID.valueChanged.connect(self.HandleEntranceIDChanged)

        self.entranceType = QtWidgets.QComboBox()
        self.entranceType.addItems(globals_.EntranceTypeNames.values())
        self.entranceType.setToolTip(globals_.trans.string('EntranceDataEditor', 3))
        self.entranceType.activated.connect(self.HandleEntranceTypeChanged)

        self.destArea = QtWidgets.QSpinBox()
        self.destArea.setRange(0, 4)
        self.destArea.setToolTip(globals_.trans.string('EntranceDataEditor', 7))
        self.destArea.valueChanged.connect(self.HandleDestAreaChanged)

        self.destEntrance = QtWidgets.QSpinBox()
        self.destEntrance.setRange(0, 255)
        self.destEntrance.setToolTip(globals_.trans.string('EntranceDataEditor', 5))
        self.destEntrance.valueChanged.connect(self.HandleDestEntranceChanged)

        self.allowEntryCheckbox = QtWidgets.QCheckBox(globals_.trans.string('EntranceDataEditor', 8))
        self.allowEntryCheckbox.setToolTip(globals_.trans.string('EntranceDataEditor', 9))
        self.allowEntryCheckbox.clicked.connect(self.HandleAllowEntryClicked)

        self.unknownFlagCheckbox = QtWidgets.QCheckBox(globals_.trans.string('EntranceDataEditor', 10))
        self.unknownFlagCheckbox.setToolTip(globals_.trans.string('EntranceDataEditor', 11))
        self.unknownFlagCheckbox.clicked.connect(self.HandleUnknownFlagClicked)

        self.connectedPipeCheckbox = QtWidgets.QCheckBox(globals_.trans.string('EntranceDataEditor', 12))
        self.connectedPipeCheckbox.setToolTip(globals_.trans.string('EntranceDataEditor', 13))
        self.connectedPipeCheckbox.clicked.connect(self.HandleConnectedPipeClicked)

        self.connectedPipeReverseCheckbox = QtWidgets.QCheckBox(globals_.trans.string('EntranceDataEditor', 14))
        self.connectedPipeReverseCheckbox.setToolTip(globals_.trans.string('EntranceDataEditor', 15))
        self.connectedPipeReverseCheckbox.clicked.connect(self.HandleConnectedPipeReverseClicked)

        self.pathID = QtWidgets.QSpinBox()
        self.pathID.setRange(0, 255)
        self.pathID.setToolTip(globals_.trans.string('EntranceDataEditor', 17))
        self.pathID.valueChanged.connect(self.HandlePathIDChanged)

        self.forwardPipeCheckbox = QtWidgets.QCheckBox(globals_.trans.string('EntranceDataEditor', 18))
        self.forwardPipeCheckbox.setToolTip(globals_.trans.string('EntranceDataEditor', 19))
        self.forwardPipeCheckbox.clicked.connect(self.HandleForwardPipeClicked)

        self.activeLayer = QtWidgets.QComboBox()
        self.activeLayer.addItems(globals_.trans.stringList('EntranceDataEditor', 21))
        self.activeLayer.setToolTip(globals_.trans.string('EntranceDataEditor', 22))
        self.activeLayer.activated.connect(self.HandleActiveLayerChanged)

        self.exit_level_checkbox = QtWidgets.QCheckBox(globals_.trans.string('EntranceDataEditor', 29))
        self.exit_level_checkbox.setToolTip(globals_.trans.string('EntranceDataEditor', 30))
        self.exit_level_checkbox.clicked.connect(self.HandleExitLevelCheckboxClicked)

        self.spawnHalfTileLeftCheckbox = QtWidgets.QCheckBox(globals_.trans.string('EntranceDataEditor', 31))
        self.spawnHalfTileLeftCheckbox.setToolTip(globals_.trans.string('EntranceDataEditor', 32))
        self.spawnHalfTileLeftCheckbox.clicked.connect(self.HandleSpawnHalfTileLeftClicked)

        self.cpDirection = QtWidgets.QComboBox()
        self.cpDirection.addItems(globals_.trans.stringList('EntranceDataEditor', 27))
        self.cpDirection.setToolTip(globals_.trans.string('EntranceDataEditor', 26))
        self.cpDirection.activated.connect(self.HandleCpDirectionChanged)

        # create a layout
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        # 'Editing Entrance #' label
        self.editingLabel = QtWidgets.QLabel('-')
        layout.addWidget(self.editingLabel, 0, 0, 1, 4, QtCore.Qt.AlignTop)

        # add labels
        layout.addWidget(QtWidgets.QLabel(globals_.trans.string('EntranceDataEditor', 0)), 3, 0, 1, 1, QtCore.Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel(globals_.trans.string('EntranceDataEditor', 2)), 1, 0, 1, 1, QtCore.Qt.AlignRight)

        layout.addWidget(createHorzLine(), 2, 0, 1, 4)

        layout.addWidget(QtWidgets.QLabel(globals_.trans.string('EntranceDataEditor', 4)), 3, 2, 1, 1, QtCore.Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel(globals_.trans.string('EntranceDataEditor', 6)), 4, 2, 1, 1, QtCore.Qt.AlignRight)

        layout.addWidget(QtWidgets.QLabel(globals_.trans.string('EntranceDataEditor', 20)), 4, 0, 1, 1, QtCore.Qt.AlignRight)

        self.pathIDLabel = QtWidgets.QLabel(globals_.trans.string('EntranceDataEditor', 16))
        self.cpDirectionLabel = QtWidgets.QLabel(globals_.trans.string('EntranceDataEditor', 25))

        # add the widgets
        layout.addWidget(self.entranceID, 3, 1, 1, 1)
        layout.addWidget(self.entranceType, 1, 1, 1, 3)

        layout.addWidget(self.destEntrance, 3, 3, 1, 1)
        layout.addWidget(self.activeLayer, 4, 1, 1, 1)
        layout.addWidget(self.destArea, 4, 3, 1, 1)
        layout.addWidget(createHorzLine(), 5, 0, 1, 4)
        layout.addWidget(self.allowEntryCheckbox, 6, 0, 1, 2)  # , QtCore.Qt.AlignRight)
        layout.addWidget(self.unknownFlagCheckbox, 6, 2, 1, 2)  # , QtCore.Qt.AlignRight)
        layout.addWidget(self.exit_level_checkbox, 7, 0, 1, 2)
        layout.addWidget(self.spawnHalfTileLeftCheckbox, 7, 2, 1, 2)
        layout.addWidget(self.forwardPipeCheckbox, 8, 0, 1, 2)  # , QtCore.Qt.AlignRight)
        layout.addWidget(self.connectedPipeCheckbox, 8, 2, 1, 2)  # , QtCore.Qt.AlignRight)

        self.cpHorzLine = createHorzLine()
        layout.addWidget(self.cpHorzLine, 9, 0, 1, 4)
        layout.addWidget(self.connectedPipeReverseCheckbox, 10, 0, 1, 2)  # , QtCore.Qt.AlignRight)
        layout.addWidget(self.pathID, 10, 3, 1, 1)
        layout.addWidget(self.pathIDLabel, 10, 2, 1, 1, QtCore.Qt.AlignRight)

        layout.addWidget(self.cpDirectionLabel, 11, 0, 1, 2, QtCore.Qt.AlignRight)
        layout.addWidget(self.cpDirection, 11, 2, 1, 2)

        self.ent = None
        self.UpdateFlag = False

    def setEntrance(self, ent):
        """
        Change the entrance being edited by the editor, update all fields
        """
        if self.ent == ent: return

        self.editingLabel.setText(globals_.trans.string('EntranceDataEditor', 23, '[id]', ent.entid))
        self.ent = ent
        self.UpdateFlag = True

        self.entranceID.setValue(ent.entid)

        idx = list(globals_.EntranceTypeNames).index(ent.enttype)
        self.entranceType.setCurrentIndex(idx)
        self.destArea.setValue(ent.destarea)
        self.destEntrance.setValue(ent.destentrance)

        self.allowEntryCheckbox.setChecked(((ent.entsettings & 0x80) == 0))
        self.unknownFlagCheckbox.setChecked(((ent.entsettings & 2) != 0))
        self.exit_level_checkbox.setChecked(ent.leave_level)

        self.spawnHalfTileLeftCheckbox.setVisible(ent.enttype in self.CanUseFlag40)
        self.spawnHalfTileLeftCheckbox.setChecked(((ent.entsettings & 0x40) != 0))

        self.connectedPipeCheckbox.setVisible(ent.enttype in self.CanUseFlag8)
        self.connectedPipeCheckbox.setChecked(((ent.entsettings & 8) != 0))

        self.connectedPipeReverseCheckbox.setVisible(ent.enttype in self.CanUseFlag8 and ((ent.entsettings & 8) != 0))
        self.connectedPipeReverseCheckbox.setChecked(((ent.entsettings & 1) != 0))

        self.forwardPipeCheckbox.setVisible(ent.enttype in self.CanUseFlag4)
        self.forwardPipeCheckbox.setChecked(((ent.entsettings & 4) != 0))

        self.pathID.setVisible(ent.enttype in self.CanUseFlag8 and ((ent.entsettings & 8) != 0))
        self.pathID.setValue(ent.entpath)
        self.pathIDLabel.setVisible(ent.enttype in self.CanUseFlag8 and ((ent.entsettings & 8) != 0))

        self.cpDirection.setVisible(ent.enttype in self.CanUseFlag8 and ((ent.entsettings & 8) != 0))
        self.cpDirection.setCurrentIndex(ent.cpdirection)
        self.cpDirectionLabel.setVisible(ent.enttype in self.CanUseFlag8 and ((ent.entsettings & 8) != 0))
        self.cpHorzLine.setVisible(ent.enttype in self.CanUseFlag8 and ((ent.entsettings & 8) != 0))

        self.activeLayer.setCurrentIndex(ent.entlayer)

        self.UpdateFlag = False

    def HandleEntranceIDChanged(self, i):
        """
        Handler for the entrance ID changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.ent.entid = i
        self.ent.update()
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()
        self.editingLabel.setText(globals_.trans.string('EntranceDataEditor', 23, '[id]', i))

    def HandleSpawnHalfTileLeftClicked(self, checked):
        """
        Handle for the Spawn Half a Tile Left checkbox being clicked
        """
        if self.UpdateFlag: return
        SetDirty()
        if checked:
            self.ent.entsettings |= 0x40
        else:
            self.ent.entsettings &= ~0x40

    def HandleEntranceTypeChanged(self, new_index):
        """
        Handler for the entrance type changing
        """
        i = list(globals_.EntranceTypeNames)[new_index]

        self.spawnHalfTileLeftCheckbox.setVisible(i in self.CanUseFlag40)
        self.connectedPipeCheckbox.setVisible(i in self.CanUseFlag8)
        self.connectedPipeReverseCheckbox.setVisible(i in self.CanUseFlag8 and ((self.ent.entsettings & 8) != 0))
        self.pathIDLabel.setVisible(i and ((self.ent.entsettings & 8) != 0))
        self.pathID.setVisible(i and ((self.ent.entsettings & 8) != 0))
        self.cpDirection.setVisible(self.ent.enttype in self.CanUseFlag8 and ((self.ent.entsettings & 8) != 0))
        self.cpDirectionLabel.setVisible(self.ent.enttype in self.CanUseFlag8 and ((self.ent.entsettings & 8) != 0))
        self.cpHorzLine.setVisible(self.ent.enttype in self.CanUseFlag8 and ((self.ent.entsettings & 8) != 0))
        self.forwardPipeCheckbox.setVisible(i in self.CanUseFlag4)
        if self.UpdateFlag: return
        SetDirty()
        self.ent.enttype = i
        self.ent.TypeChange()
        self.ent.update()
        self.ent.UpdateTooltip()
        globals_.mainWindow.scene.update()
        self.ent.UpdateListItem()

    def HandleDestAreaChanged(self, i):
        """
        Handler for the destination area changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.ent.destarea = i
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()

    def HandleDestEntranceChanged(self, i):
        """
        Handler for the destination entrance changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.ent.destentrance = i
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()

    def HandleAllowEntryClicked(self, checked):
        """
        Handle for the Allow Entry checkbox being clicked
        """
        if self.UpdateFlag: return
        SetDirty()
        if not checked:
            self.ent.entsettings |= 0x80
        else:
            self.ent.entsettings &= ~0x80
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()

    def HandleUnknownFlagClicked(self, checked):
        """
        Handle for the Unknown Flag checkbox being clicked
        """
        if self.UpdateFlag: return
        SetDirty()
        if checked:
            self.ent.entsettings |= 2
        else:
            self.ent.entsettings &= ~2

    def HandleExitLevelCheckboxClicked(self, checked):
        """
        Handle the Send to World Map checkbox being clicked
        """
        if self.UpdateFlag or self.ent.leave_level == checked: return
        SetDirty()
        self.ent.leave_level = checked
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()

    def HandleConnectedPipeClicked(self, checked):
        """
        Handle for the connected pipe checkbox being clicked
        """
        self.connectedPipeReverseCheckbox.setVisible(checked)
        self.pathID.setVisible(checked)
        self.pathIDLabel.setVisible(checked)
        self.cpDirection.setVisible(checked)
        self.cpDirectionLabel.setVisible(checked)
        self.cpHorzLine.setVisible(checked)
        if self.UpdateFlag: return
        SetDirty()
        if checked:
            self.ent.entsettings |= 8
        else:
            self.ent.entsettings &= ~8

    def HandleConnectedPipeReverseClicked(self, checked):
        """
        Handle for the connected pipe reverse checkbox being clicked
        """
        if self.UpdateFlag: return
        SetDirty()
        if checked:
            self.ent.entsettings |= 1
        else:
            self.ent.entsettings &= ~1

    def HandlePathIDChanged(self, i):
        """
        Handler for the path ID changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.ent.entpath = i

    def HandleForwardPipeClicked(self, checked):
        """
        Handle for the forward pipe checkbox being clicked
        """
        if self.UpdateFlag: return
        SetDirty()
        if checked:
            self.ent.entsettings |= 4
        else:
            self.ent.entsettings &= ~4

    def HandleActiveLayerChanged(self, i):
        """
        Handle for the active layer changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.ent.entlayer = i

    def HandleCpDirectionChanged(self, i):
        """
        Handle for CP Direction changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.ent.cpdirection = i


class PathNodeEditorWidget(QtWidgets.QWidget):
    """
    Widget for editing path node properties
    """

    def __init__(self, defaultmode=False):
        """
        Constructor
        """
        QtWidgets.QWidget.__init__(self)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))

        # Some single point float constants. Note that we cannot use the ones
        # provided by sys.float_info, since those relate to double precision
        # floats, and the speed and acceleration fields are single precision
        # floats. As such, we just hardcode these values.
        FLT_DIG = 6
        FLT_MAX = 3.402823466e+38

        # create widgets
        self.speed = QtWidgets.QDoubleSpinBox()
        self.speed.setRange(-FLT_MAX, FLT_MAX)
        self.speed.setToolTip(globals_.trans.string('PathDataEditor', 3))
        self.speed.setDecimals(FLT_DIG)
        self.speed.valueChanged.connect(self.HandleSpeedChanged)

        self.accel = QtWidgets.QDoubleSpinBox()
        self.accel.setRange(-FLT_MAX, FLT_MAX)
        self.accel.setToolTip(globals_.trans.string('PathDataEditor', 5))
        self.accel.setDecimals(FLT_DIG)
        self.accel.valueChanged.connect(self.HandleAccelChanged)

        self.delay = QtWidgets.QSpinBox()
        self.delay.setRange(0, 65535)
        self.delay.setToolTip(globals_.trans.string('PathDataEditor', 7))
        self.delay.valueChanged.connect(self.HandleDelayChanged)

        self.loops = QtWidgets.QCheckBox()
        self.loops.setToolTip(globals_.trans.string('PathDataEditor', 1))
        self.loops.stateChanged.connect(self.HandleLoopsChanged)

        # create a layout
        layout = QtWidgets.QFormLayout()
        self.setLayout(layout)

        # 'Editing Path #' label
        self.editingLabel = QtWidgets.QLabel('-')
        self.editingPathLabel = QtWidgets.QLabel('-')

        self.path_id = QtWidgets.QSpinBox()
        self.path_id.setRange(0, 255)
        self.path_id.valueChanged.connect(self.HandlePathIdChanged)

        self.node_id = QtWidgets.QSpinBox()
        self.node_id.setRange(0, 255)
        self.node_id.valueChanged.connect(self.HandleNodeIdChanged)

        layout.addRow(self.editingPathLabel)

        # add labels
        layout.addRow("Id", self.path_id)
        layout.addRow(globals_.trans.string('PathDataEditor', 0), self.loops)
        layout.addRow(createHorzLine())

        layout.addRow(self.editingLabel)
        layout.addRow("Id", self.node_id)
        layout.addRow(globals_.trans.string('PathDataEditor', 2), self.speed)
        layout.addRow(globals_.trans.string('PathDataEditor', 4), self.accel)
        layout.addRow(globals_.trans.string('PathDataEditor', 6), self.delay)

        self.path_node = None
        self.UpdateFlag = False

    def setPath(self, path_item):
        """
        Change the path being edited by the editor, update all fields
        """
        if self.path_node == path_item: return

        self.path_node = path_item

        self.editingPathLabel.setText(globals_.trans.string('PathDataEditor', 8, '[id]', path_item.pathid))
        self.editingLabel.setText(globals_.trans.string('PathDataEditor', 9, '[id]', path_item.nodeid))

        speed, accel, delay = path_item.path.get_data_for_node(path_item.nodeid)
        loops = path_item.path.get_loops()
        path_len = len(path_item.path)

        self.UpdateFlag = True

        self.node_id.setRange(0, path_len - 1)
        self.node_id.setEnabled(path_len > 1)
        self.node_id.setValue(path_item.nodeid)
        self.path_id.setValue(path_item.pathid)
        self.speed.setValue(speed)
        self.accel.setValue(accel)
        self.delay.setValue(delay)
        self.loops.setChecked(loops)

        self.UpdateFlag = False

    def UpdatePathLength(self):
        """
        The length of the path changed, so update the range of the node id editor.
        """
        self.node_id.setRange(0, len(self.path_node.path) - 1)

    def HandleSpeedChanged(self, i):
        """
        Handler for the speed changing
        """
        if self.UpdateFlag:
            return

        if self.path_node.path.set_node_data(self.path_node, speed=i):
            SetDirty()

    def HandleAccelChanged(self, i):
        """
        Handler for the accel changing
        """
        if self.UpdateFlag:
            return

        if self.path_node.path.set_node_data(self.path_node, accel=i):
            SetDirty()

    def HandleDelayChanged(self, i):
        """
        Handler for the delay changing
        """
        if self.UpdateFlag:
            return

        if self.path_node.path.set_node_data(self.path_node, delay=i):
            SetDirty()

    def HandleLoopsChanged(self, i):
        if self.UpdateFlag or self.path_node.path._loops == (i == QtCore.Qt.Checked):
            return

        if self.path_node.path.set_loops(i == QtCore.Qt.Checked):
            SetDirty()

    def HandlePathIdChanged(self, i):
        if self.UpdateFlag or self.path_node.pathid == i:
            return

        self.path_node.path.set_id(i)
        SetDirty()

    def HandleNodeIdChanged(self, i):
        if self.UpdateFlag or self.path_node.nodeid == i:
            return

        self.path_node.path.move_node(self.path_node, i)
        SetDirty()


class LocationEditorWidget(QtWidgets.QWidget):
    """
    Widget for editing location properties
    """

    def __init__(self, defaultmode=False):
        """
        Constructor
        """
        QtWidgets.QWidget.__init__(self)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))

        # create widgets
        self.locationID = QtWidgets.QSpinBox()
        self.locationID.setToolTip(globals_.trans.string('LocationDataEditor', 1))
        self.locationID.setRange(0, 255)
        self.locationID.valueChanged.connect(self.HandleLocationIDChanged)

        self.locationX = QtWidgets.QSpinBox()
        self.locationX.setToolTip(globals_.trans.string('LocationDataEditor', 3))
        self.locationX.setRange(16, 65535)
        self.locationX.valueChanged.connect(self.HandleLocationXChanged)

        self.locationY = QtWidgets.QSpinBox()
        self.locationY.setToolTip(globals_.trans.string('LocationDataEditor', 5))
        self.locationY.setRange(16, 65535)
        self.locationY.valueChanged.connect(self.HandleLocationYChanged)

        self.locationWidth = QtWidgets.QSpinBox()
        self.locationWidth.setToolTip(globals_.trans.string('LocationDataEditor', 7))
        self.locationWidth.setRange(1, 65535)
        self.locationWidth.valueChanged.connect(self.HandleLocationWidthChanged)

        self.locationHeight = QtWidgets.QSpinBox()
        self.locationHeight.setToolTip(globals_.trans.string('LocationDataEditor', 9))
        self.locationHeight.setRange(1, 65535)
        self.locationHeight.valueChanged.connect(self.HandleLocationHeightChanged)

        self.snapButton = QtWidgets.QPushButton(globals_.trans.string('LocationDataEditor', 10))
        self.snapButton.clicked.connect(self.HandleSnapToGrid)

        # create a layout
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        # 'Editing Location #' label
        self.editingLabel = QtWidgets.QLabel('-')
        layout.addWidget(self.editingLabel, 0, 0, 1, 4, QtCore.Qt.AlignTop)

        # add labels
        layout.addWidget(QtWidgets.QLabel(globals_.trans.string('LocationDataEditor', 0)), 1, 0, 1, 1, QtCore.Qt.AlignRight)

        layout.addWidget(createHorzLine(), 2, 0, 1, 4)

        layout.addWidget(QtWidgets.QLabel(globals_.trans.string('LocationDataEditor', 2)), 3, 0, 1, 1, QtCore.Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel(globals_.trans.string('LocationDataEditor', 4)), 4, 0, 1, 1, QtCore.Qt.AlignRight)

        layout.addWidget(QtWidgets.QLabel(globals_.trans.string('LocationDataEditor', 6)), 3, 2, 1, 1, QtCore.Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel(globals_.trans.string('LocationDataEditor', 8)), 4, 2, 1, 1, QtCore.Qt.AlignRight)

        # add the widgets
        layout.addWidget(self.locationID, 1, 1, 1, 1)
        layout.addWidget(self.snapButton, 1, 3, 1, 1)

        layout.addWidget(self.locationX, 3, 1, 1, 1)
        layout.addWidget(self.locationY, 4, 1, 1, 1)

        layout.addWidget(self.locationWidth, 3, 3, 1, 1)
        layout.addWidget(self.locationHeight, 4, 3, 1, 1)

        self.loc = None
        self.UpdateFlag = False

    def setLocation(self, loc):
        """
        Change the location being edited by the editor, update all fields
        """
        self.loc = loc
        self.UpdateFlag = True

        self.FixTitle()
        self.locationID.setValue(loc.id)
        self.locationX.setValue(loc.objx)
        self.locationY.setValue(loc.objy)
        self.locationWidth.setValue(loc.width)
        self.locationHeight.setValue(loc.height)

        self.UpdateFlag = False

    def FixTitle(self):
        self.editingLabel.setText(globals_.trans.string('LocationDataEditor', 11, '[id]', self.loc.id))

    def HandleLocationIDChanged(self, i):
        """
        Handler for the location ID changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.loc.id = i
        self.loc.update()
        self.loc.UpdateTitle()
        self.FixTitle()

    def HandleLocationXChanged(self, i):
        """
        Handler for the location X-pos changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.loc.objx = i
        self.loc.autoPosChange = True
        self.loc.setX(int(i * 1.5))
        self.loc.autoPosChange = False
        self.loc.UpdateRects()
        self.loc.update()

    def HandleLocationYChanged(self, i):
        """
        Handler for the location Y-pos changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.loc.objy = i
        self.loc.autoPosChange = True
        self.loc.setY(int(i * 1.5))
        self.loc.autoPosChange = False
        self.loc.UpdateRects()
        self.loc.update()

    def HandleLocationWidthChanged(self, i):
        """
        Handler for the location width changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.loc.width = i
        self.loc.UpdateRects()
        self.loc.update()

    def HandleLocationHeightChanged(self, i):
        """
        Handler for the location height changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.loc.height = i
        self.loc.UpdateRects()
        self.loc.update()

    def HandleSnapToGrid(self):
        """
        Snaps the current location to an 8x8 grid
        """
        SetDirty()

        loc = self.loc
        left = loc.objx
        top = loc.objy
        right = left + loc.width
        bottom = top + loc.height

        if left % 8 < 4:
            left -= (left % 8)
        else:
            left += 8 - (left % 8)

        if top % 8 < 4:
            top -= (top % 8)
        else:
            top += 8 - (top % 8)

        if right % 8 < 4:
            right -= (right % 8)
        else:
            right += 8 - (right % 8)

        if bottom % 8 < 4:
            bottom -= (bottom % 8)
        else:
            bottom += 8 - (bottom % 8)

        if right <= left: right += 8
        if bottom <= top: bottom += 8

        loc.objx = left
        loc.objy = top
        loc.width = right - left
        loc.height = bottom - top

        loc.setPos(int(left * 1.5), int(top * 1.5))
        loc.UpdateRects()
        loc.update()
        self.setLocation(loc)  # updates the fields

