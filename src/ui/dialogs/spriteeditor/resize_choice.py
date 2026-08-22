from PyQt6 import QtCore, QtWidgets

import globals_
from levelitems import InstanceDefinition
from ui import GetIcon


class ResizeChoiceDialog(QtWidgets.QDialog):
    """
    Dialog for the resize option.
    """
    def __init__(self, spriteid):
        """
        Initialise the dialog
        """
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle(globals_.trans.string('ResizeChoiceDlg', 11))
        self.setWindowIcon(GetIcon('resize'))

        # Scale levels used by both Resizer modes
        self.scaleLevels =  [1.0, 0.25, 0.5, 0.75, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0]

        if 0 <= spriteid < globals_.NumSprites:
            self.sprite = globals_.Sprites[spriteid]
        else:
            self.sprite = None

        ## Slots
        used = self.getNyb5And7Availability()
        self.present = self.checkSpecialEvent()

        # Setup buttons
        self.buttongroup = QtWidgets.QButtonGroup()
        self.radio1 = QtWidgets.QRadioButton()
        self.buttongroup.addButton(self.radio1, 0)
        self.radio2 = QtWidgets.QRadioButton()
        self.buttongroup.addButton(self.radio2, 1)
        self.radio3 = QtWidgets.QRadioButton()
        self.buttongroup.addButton(self.radio3, 2)
        self.buttongroup.buttonClicked.connect(self.toggleGlbResizerScale)

        a_label = QtWidgets.QLabel(globals_.trans.string('ResizeChoiceDlg', 7))
        b_label = QtWidgets.QLabel(globals_.trans.string('ResizeChoiceDlg', 8))
        g_label = QtWidgets.QLabel(globals_.trans.string('ResizeChoiceDlg', 9))

        selDesc = QtWidgets.QLabel(globals_.trans.string('ResizeChoiceDlg', 13))
        glbDesc = QtWidgets.QLabel(globals_.trans.string('ResizeChoiceDlg', 14))

        # Display a warning if this sprite has settings on Nybbles 5 or 7
        isDispWarning = True
        warnLabel = QtWidgets.QLabel('')
        warnLabel.setStyleSheet("color: orange;")

        # Check if there are conflicts
        if len(used[5]) != 0 and len(used[7]) != 0: # Both are occupied
            warnLabel.setText(globals_.trans.string('ResizeChoiceDlg', 19))
            warnLabel.setStyleSheet("color: red;")
        elif len(used[5]) != 0: # Only 5
            warnLabel.setText(globals_.trans.string('ResizeChoiceDlg', 18, '[id]', 5))
        elif len(used[7]) != 0: # Only 7
            warnLabel.setText(globals_.trans.string('ResizeChoiceDlg', 18, '[id]', 7))
        else: # Both are available
            isDispWarning = False

        selectiveBox = QtWidgets.QGroupBox(globals_.trans.string('ResizeChoiceDlg', 15))
        selLyt = QtWidgets.QGridLayout()
        selLyt.addWidget(selDesc,     0, 0, 1, 2, QtCore.Qt.AlignmentFlag.AlignHCenter)
        selLyt.addWidget(a_label,     1, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignHCenter)
        selLyt.addWidget(self.radio1, 2, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignHCenter)
        selLyt.addWidget(b_label,     1, 1, 1, 1, QtCore.Qt.AlignmentFlag.AlignHCenter)
        selLyt.addWidget(self.radio2, 2, 1, 1, 1, QtCore.Qt.AlignmentFlag.AlignHCenter)
        if isDispWarning:
            selLyt.addWidget(warnLabel, 3, 0, 1, 2, QtCore.Qt.AlignmentFlag.AlignHCenter)
        selectiveBox.setLayout(selLyt)

        globalBox = QtWidgets.QGroupBox(globals_.trans.string('ResizeChoiceDlg', 16))
        glbLyt = QtWidgets.QGridLayout()
        glbLyt.addWidget(glbDesc,     0, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignHCenter)
        glbLyt.addWidget(g_label,     1, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignHCenter)
        glbLyt.addWidget(self.radio3, 2, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignHCenter)
        if isDispWarning: # Alignment so this looks better
            glbLyt.addWidget(QtWidgets.QLabel(''), 3, 0, 1, 2, QtCore.Qt.AlignmentFlag.AlignHCenter)
        globalBox.setLayout(glbLyt)

        # Global Resizer scale
        sliderLabel = QtWidgets.QLabel(globals_.trans.string('ResizeChoiceDlg', 17))
        self.sliderVal = QtWidgets.QLabel('x' + str(self.scaleLevels[0]))

        self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider.setMaximumHeight(20)
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(self.scaleLevels) - 1)
        self.slider.setTickInterval(1)
        self.slider.setTickPosition(self.slider.TickPosition.TicksAbove)
        self.slider.setPageStep(1)
        self.slider.setTracking(True)
        self.slider.setSliderPosition(0)
        self.slider.valueChanged.connect(self.sliderMoved)
        globalScale = self.getGlobalScale()
        if self.present and globalScale is not None:
            self.slider.setValue(globalScale)

        glbSclLyt = QtWidgets.QHBoxLayout()
        glbSclLyt.addWidget(sliderLabel)
        glbSclLyt.addWidget(self.slider)

        # This allows us to toggle the entire thing
        self.glbScaleWidget = QtWidgets.QWidget()
        self.glbScaleWidget.setLayout(glbSclLyt)
        self.glbScaleWidget.setEnabled(False)

        slotsLayout = QtWidgets.QGridLayout()
        slotsLayout.setContentsMargins(0, 0, 0, 0)
        slotsLayout.addWidget(selectiveBox,        0, 0, 1, 2, QtCore.Qt.AlignmentFlag.AlignHCenter)
        slotsLayout.addWidget(globalBox,           0, 2, 1, 1, QtCore.Qt.AlignmentFlag.AlignHCenter)
        slotsLayout.addWidget(self.glbScaleWidget, 1, 0, 1, 3)
        slotsLayout.addWidget(self.sliderVal,      1, 3, 1, 1)

        # Auto-select the relevant button
        if self.present:
            # Select our current resizer type

            # Just in case we can't find it for whatever reason
            self.radio1.setChecked(True)

            for type, sprite in self.present:
                if sprite.sprite_num != globals_.SpecialEventSpriteID:
                    continue

                type = sprite.spritedata[5] & 0xF
                if type == 5:
                    self.radio3.setChecked(True)
                    self.glbScaleWidget.setEnabled(True)
                elif type == 6:
                    if (sprite.spritedata[5] >> 4) != 0:
                        self.radio2.setChecked(True)
                    else:
                        self.radio1.setChecked(True)
        else:
            # Offer the user the 'best' option in this case
            if len(used[5]) != 0 and len(used[7]) != 0:
                self.radio3.setChecked(True)
                self.glbScaleWidget.setEnabled(True)
            elif len(used[5]) <= len(used[7]):
                self.radio1.setChecked(True)
            else:
                self.radio2.setChecked(True)

        # Action button (does the create/update behavior)
        if not self.present:
            btnText = globals_.trans.string('ResizeChoiceDlg', 4)
        else:
            btnText = globals_.trans.string('ResizeChoiceDlg', 5)

        spriteButton = QtWidgets.QPushButton(btnText)
        spriteButton.clicked.connect(self.handleResizer)

        # Create layout
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Close)
        buttonBox.rejected.connect(self.reject)
        buttonBox.addButton(spriteButton, QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(QtWidgets.QLabel(globals_.trans.string('ResizeChoiceDlg', 0)))

        # Warn the user if a Special Event exists
        if self.present:
            mainLayout.addWidget(QtWidgets.QLabel(globals_.trans.string('ResizeChoiceDlg', 2)))

        mainLayout.addLayout(slotsLayout)
        mainLayout.addWidget(buttonBox, 0, QtCore.Qt.AlignmentFlag.AlignBottom)

        self.setLayout(mainLayout)

    def getNyb5And7Availability(self):
        """
        Gets whether nybbles 5 or 7 (or both/none) are occupied by spritedata or not
        """
        nyb5 = (17, 21) # excludes end
        nyb7 = (25, 29)

        found = {5: [], 7: []}

        if self.sprite is None:
            return found

        for field in self.sprite.fields:
            bit = field.bit
            if isinstance(bit, tuple) and not isinstance(bit[0], tuple):
                bit = (bit,)

            # if two ranges (a..b, c..d) overlap, that means that a..b is not
            # completely before c..d (that is, b >= c) nor
            #    a <= i < b AND c <= i < d
            # since a < b and c < d,
            #    a < d AND c < b
            overlap = lambda a, b: a[0] < b[1] and b[0] < a[1]

            if bit is None:
                continue

            for ran in bit:
                if overlap(ran, nyb5):
                    found[5].append(field)

                if overlap(ran, nyb7):
                    found[7].append(field)

        return found

    def checkSpecialEvent(self):
        """
        Find Special Event and then check if it has resize set.
        Returns a list of (slot, sprite) pairs, where slot = 2 means it is a global
        resize.
        """
        slots = []
        for sprite in globals_.Area.sprites:
            if sprite.sprite_num != globals_.SpecialEventSpriteID:
                continue

            type = sprite.spritedata[5] & 0xF
            if type == 5:
                # Global resizer
                slots.append((2, sprite))
            elif type == 6:
                # Selective resizer
                slot = (sprite.spritedata[5] >> 4) & 1
                slots.append((slot, sprite))

        return slots

    def handleResizer(self):
        """
        Either places a new special event or changes the old one.
        """
        if not self.present:
            self.createResizer()
        else:
            for type, sprite in self.present:
                if sprite.sprite_num == globals_.SpecialEventSpriteID:
                    self.editResizer(sprite)
                    break

        return self.accept()

    def editResizer(self, sprite):
        """
        Updates the existing Special Event
        """
        data = list(sprite.spritedata)

        slot = self.buttongroup.checkedId()
        if slot == 2: # global
            data[5] = (self.slider.value() << 4) | 5
        else: # only slot
            data[5] = (slot << 4) | 6

        sprite.spritedata = bytes(data)

    def createResizer(self):
        """
        Places a Special Event and sets the settings so the correct slot.
        """
        slot = self.buttongroup.checkedId()
        size = self.slider.value()
        data = bytearray(8)

        if slot == 2: # Global
            data[5] = (size << 4) | 5
        else: # Selective
            data[5] = (slot << 4) | 6

        mainWindow = globals_.mainWindow
        if mainWindow is None:
            return

        selObj = mainWindow.selObj
        if selObj is None or not isinstance(selObj, InstanceDefinition):
            return

        x = selObj.objx + 16 if selObj.objx is not None else 16
        y = selObj.objy if selObj.objy is not None else 0
        special_event_id = globals_.SpecialEventSpriteID

        if mainWindow.CreateSprite(x, y, special_event_id, data) is not None:
            mainWindow.scene.update()

    def getGlobalScale(self):
        """
        Get the scale for the Global Resizer
        """
        for sprite in globals_.Area.sprites:
            if sprite.sprite_num != globals_.SpecialEventSpriteID:
                continue

            type = sprite.spritedata[5] & 0xF
            if type == 5:
                return (sprite.spritedata[5] >> 4)
            else:
                return 0

    def sliderMoved(self):
        """
        Handle the slider being moved
        """
        self.sliderVal.setText('x' + str(self.scaleLevels[self.slider.value()]))

    def toggleGlbResizerScale(self, button):
        """
        Toggles the global resizer scale
        """
        if not button.isEnabled():
            return

        self.glbScaleWidget.setEnabled(self.buttongroup.id(button) == 2)
