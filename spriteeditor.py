import os
from xml.etree import ElementTree

from PyQt5 import QtWidgets, QtCore, QtGui

import globals_
from levelitems import SpriteItem, ListWidgetItem_SortsByOther
from sliderswitch import QSliderSwitch
from ui import GetIcon
from dirty import SetDirty

class DualBox(QtWidgets.QWidget):
    """
    A dualbox widget for the sprite data
    """
    toggled = QtCore.pyqtSignal('PyQt_PyObject')

    def __init__(self, text1 = None, text2 = None, initial = 0, direction = 0):
        """
        Inits the dualbox with text to the left/above and text to the right/below
        """
        super().__init__()

        self.qsstemplate = """QPushButton {
            width: %dpx;
            height: %dpx;
            border-radius: 0px;
            border: 1px solid dark%%s;
            background: %%s;
        }"""

        self.value = initial
        self.direction = direction

        self.slider = QtWidgets.QPushButton()
        self.slider.clicked.connect(self.toggle)

        if direction == 0:
            layout = QtWidgets.QHBoxLayout()
            self.qsstemplate %= (40, 20)
        else:
            layout = QtWidgets.QVBoxLayout()
            self.qsstemplate %= (20, 40)

        layout.setContentsMargins(0, 0, 0, 0)

        if text1 is not None:
            label = QtWidgets.QPushButton(text1)
            label.setStyleSheet("""QPushButton {border:0; background:0; margin:0; padding:0}""")
            label.clicked.connect(self.toggle)
            if direction == 0:
                layout.addWidget(label, 0, QtCore.Qt.AlignRight)
            else:
                layout.addWidget(label)

        layout.addWidget(self.slider)

        if text2 is not None:
            label = QtWidgets.QPushButton(text2)
            label.setStyleSheet("""QPushButton {border:0; background:0; margin:0; padding:0}""")
            label.clicked.connect(self.toggle)
            layout.addWidget(label)

        self.setLayout(layout)
        self.updateUI()

    def isSet(self):
        return self.value == 1

    def setValue(self, value):
        """
        Sets the value and updates the UI
        """
        # the only allowed values for 'value' are 0 and 1
        if value != 0 and value != 1:
            raise ValueError

        # don't do anything if we are already set
        if self.value == value:
            return

        self.value = value

        # update the UI
        # TODO: Make this a slider
        # TODO: Make this a nice animation
        self.updateUI()

    def getValue(self):
        return self.value

    def updateUI(self):
        colour = ['red', 'green'][self.value]
        self.qss = self.qsstemplate % (colour, colour)
        self.slider.setStyleSheet(self.qss)

    def toggle(self):
        """
        The slider was toggled, so update UI and emit the signal
        """
        self.setValue(1 - self.value)
        self.toggled.emit(self)


class SpriteEditorWidget(QtWidgets.QWidget):
    """
    Widget for editing sprite data
    """
    DataUpdate = QtCore.pyqtSignal('PyQt_PyObject')

    def __init__(self, defaultmode=False):
        """
        Constructor
        """
        super().__init__()
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))
        self.setMaximumWidth(500)

        # create the raw editor
        font = QtGui.QFont()
        font.setPointSize(8)
        self.editbox = QtWidgets.QLabel(globals_.trans.string('SpriteDataEditor', 3))
        self.editbox.setFont(font)
        edit = QtWidgets.QLineEdit()
        edit.textEdited.connect(self.HandleRawDataEdited)
        edit.setMinimumWidth(133 + 10) # width of 'dddd dddd dddd dddd' (widest valid string) + padding
        self.raweditor = edit

        self.resetButton = QtWidgets.QPushButton(globals_.trans.string('SpriteDataEditor', 17))
        self.resetButton.clicked.connect(self.HandleResetData)

        self.showRawData = QtWidgets.QPushButton(globals_.trans.string('SpriteDataEditor', 24))
        self.showRawData.clicked.connect(self.HandleShowRawData)

        editboxlayout = QtWidgets.QHBoxLayout()
        editboxlayout.addWidget(self.resetButton)
        editboxlayout.addStretch(1)
        editboxlayout.addWidget(self.showRawData)
        editboxlayout.addWidget(self.editbox)
        editboxlayout.addWidget(edit)

        # 'Editing Sprite #' label
        self.spriteLabel = QtWidgets.QLabel('-')
        self.spriteLabel.setWordWrap(True)

        self.noteButton = QtWidgets.QToolButton()
        self.noteButton.setIcon(GetIcon('note'))
        self.noteButton.setText(globals_.trans.string('SpriteDataEditor', 4))
        self.noteButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.noteButton.setAutoRaise(True)
        self.noteButton.clicked.connect(self.ShowNoteTooltip)

        self.depButton = QtWidgets.QToolButton()
        self.depButton.setIcon(GetIcon('dependency-notes'))
        self.depButton.setText(globals_.trans.string('SpriteDataEditor', 4))
        self.depButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.depButton.setAutoRaise(True)
        self.depButton.clicked.connect(self.ShowDependencies)

        self.relatedObjFilesButton = QtWidgets.QToolButton()
        self.relatedObjFilesButton.setIcon(GetIcon('data'))
        self.relatedObjFilesButton.setText(globals_.trans.string('SpriteDataEditor', 7))
        self.relatedObjFilesButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.relatedObjFilesButton.setAutoRaise(True)
        self.relatedObjFilesButton.clicked.connect(self.ShowRelatedObjFilesTooltip)

        self.advNoteButton = QtWidgets.QToolButton()
        self.advNoteButton.setIcon(GetIcon('note-advanced'))
        self.advNoteButton.setText(globals_.trans.string('SpriteDataEditor', 10))
        self.advNoteButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.advNoteButton.setAutoRaise(True)
        self.advNoteButton.clicked.connect(self.ShowAdvancedNoteTooltip)

        self.yoshiIcon = QtWidgets.QLabel()

        self.yoshiInfo = QtWidgets.QToolButton()
        self.yoshiInfo.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.yoshiInfo.setText(globals_.trans.string('SpriteDataEditor', 12))
        self.yoshiInfo.setAutoRaise(True)
        self.yoshiInfo.clicked.connect(self.ShowYoshiTooltip)

        self.asm = QtWidgets.QLabel()
        self.asm.setPixmap(GetIcon("asm").pixmap(64, 64))

        self.sizeButton = QtWidgets.QToolButton()
        self.sizeButton.setIcon(GetIcon('reggie')) # TODO: find a proper icon
        self.sizeButton.setText("Resize") # TODO: Add this to the translation
        self.sizeButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.sizeButton.setAutoRaise(True)
        self.sizeButton.clicked.connect(self.HandleSizeButtonClicked)

        toplayout = QtWidgets.QHBoxLayout()
        toplayout.addWidget(self.spriteLabel)
        toplayout.addStretch(1)
        toplayout.addWidget(self.asm)
        toplayout.addWidget(self.yoshiIcon)
        toplayout.addWidget(self.yoshiInfo)
        toplayout.addWidget(self.sizeButton)
        toplayout.addWidget(self.relatedObjFilesButton)
        toplayout.addWidget(self.depButton)
        toplayout.addWidget(self.noteButton)
        toplayout.addWidget(self.advNoteButton)

        subLayout = QtWidgets.QVBoxLayout()
        subLayout.setContentsMargins(0, 0, 0, 0)

        # messages - now used for dependency warnings, but it might be useful for
        # other stuff too
        self.msg_layout = QtWidgets.QVBoxLayout()

        # comments
        self.com_box = QtWidgets.QGroupBox()
        self.com_box.setMaximumHeight(120)

        self.com_main = QtWidgets.QTextEdit()
        self.com_main.setReadOnly(True)

        self.com_more = QtWidgets.QPushButton()
        self.com_more.setText(globals_.trans.string('SpriteDataEditor', 13))
        self.com_more.clicked.connect(self.ShowMoreComments)

        self.com_dep = QtWidgets.QPushButton()
        self.com_dep.setText(globals_.trans.string('SpriteDataEditor', 18))
        self.com_dep.clicked.connect(self.DependencyToggle)
        self.com_dep.setVisible(False)

        self.com_extra = QtWidgets.QTextEdit()
        self.com_extra.setReadOnly(True)
        self.com_extra.setVisible(False)

        self.com_deplist = QtWidgets.QGridLayout()

        self.com_deplist_w = QtWidgets.QWidget()
        self.com_deplist_w.setVisible(False)
        self.com_deplist_w.setLayout(self.com_deplist)

        L = QtWidgets.QVBoxLayout()
        L.addWidget(self.com_main)
        L.addWidget(self.com_more)
        L.addWidget(self.com_dep)
        L.addWidget(self.com_extra)
        L.addWidget(self.com_deplist_w)

        self.com_box.setLayout(L)

        # create a layout
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(toplayout)
        mainLayout.addLayout(subLayout)

        layout = QtWidgets.QGridLayout()
        self.editorlayout = layout

        subLayout.addLayout(self.msg_layout)
        subLayout.addLayout(layout)
        subLayout.addWidget(self.com_box)
        subLayout.addLayout(editboxlayout)

        self.setLayout(mainLayout)

        self.spritetype = -1
        self.data = b'\0\0\0\0\0\0\0\0'
        self.fields = []
        self.UpdateFlag = False
        self.DefaultMode = defaultmode

        self.notes = None
        self.relatedObjFiles = None
        self.dependencyNotes = None

    class PropertyDecoder(QtCore.QObject):
        """
        Base class for all the sprite data decoder/encoders
        """
        updateData = QtCore.pyqtSignal('PyQt_PyObject')

        def retrieve(self, data, bits=None):
            """
            Extracts the value from the specified bit(s). Bit numbering is ltr BE
            and starts at 1.
            """
            if bits is None:
                bit = self.bit

            else:
                bit = bits

            if isinstance(bit, list):
                # multiple ranges. do this recursively.
                value = 0

                for ran in bit:
                    # find the size of the range
                    if isinstance(ran, tuple):
                        l = ran[1] - ran[0]

                    else:
                        l = 1

                    # shift the value so we don't overwrite
                    value <<= l

                    # and OR in the value for the range
                    value |= self.retrieve(data, ran)

                # done
                return value

            elif isinstance(bit, tuple):
                if bit[1] == bit[0] + 7 and bit[0] & 1 == 1:
                    # optimise if it's just one byte
                    return data[bit[0] >> 3]

                else:
                    # we have to calculate it sadly
                    # just do it by looping, shouldn't be that bad
                    value = 0
                    for n in range(bit[0], bit[1]):
                        n -= 1
                        value = (value << 1) | ((data[n >> 3] >> (7 - (n & 7))) & 1)

                    return value

            else:
                # we just want one bit
                bit -= 1

                if (bit >> 3) >= len(data):
                    return 0

                return (data[bit >> 3] >> (7 - (bit & 7))) & 1

        def insertvalue(self, data, value, bits=None):
            """
            Assigns a value to the specified bit(s)
            """
            if bits is None:
                bit = self.bit

            else:
                bit = bits

            sdata = list(data)

            if isinstance(bit, list):
                # multiple ranges
                for ran in reversed(bit):
                    # find the size of the range
                    if isinstance(ran, tuple):
                        l = ran[1] - ran[0]

                    else:
                        l = 1

                    # mask the value over this length
                    mask = (1 << l) - 1
                    v = value & mask

                    # remove these bits from the value
                    value >>= l

                    # recursively set the value
                    data = list(self.insertvalue(data, v, ran))

                return bytes(data)

            elif isinstance(bit, tuple):
                if bit[1] == bit[0] + 7 and bit[0] & 1 == 1:
                    # just one byte, this is easier
                    sdata[(bit[0] - 1) >> 3] = value & 0xFF

                else:
                    # complicated stuff
                    for n in reversed(range(bit[0], bit[1])):
                        off = 1 << (7 - ((n - 1) & 7))

                        if value & 1:
                            # set the bit
                            sdata[(n - 1) >> 3] |= off

                        else:
                            # mask the bit out
                            sdata[(n - 1) >> 3] &= 0xFF ^ off

                        value >>= 1

            else:
                # only overwrite one bit
                byte = (bit - 1) >> 3
                if byte >= len(data):
                    return 0

                off = 1 << (7 - ((bit - 1) & 7))

                if value & 1:
                    # set the bit
                    sdata[byte] |= off

                else:
                    # mask the bit out
                    sdata[byte] &= 0xFF ^ off

            return bytes(sdata)

        def checkReq(self, data, first=False):
            """
            Checks the requirements
            """
            if self.required is None:
                return

            show = True
            for requirement in self.required:
                val = self.retrieve(data, requirement[0])
                ran = requirement[1]

                if isinstance(ran, tuple):
                    show = show and ran[0] <= val < ran[1]

                else:
                    show = show and ran == val

            visibleNow = self.layout.itemAtPosition(self.row, 0).widget().isVisible()

            if show == visibleNow and not first:
                return

            # show/hide all widgets in this row
            for i in range(self.layout.columnCount()):
                w = self.layout.itemAtPosition(self.row, i)
                if w is not None:
                    w.widget().clearFocus()
                    w.widget().setVisible(show)

            # maybe reset hidden stuff
            if globals_.ResetDataWhenHiding and not show:
                self.insertvalue(data, 0)

        def checkAdv(self):
            """
            Checks if we should show this setting
            """

            if not self.advanced or globals_.AdvancedModeEnabled:
                return

            # hide all widgets in this row
            for i in range(self.layout.columnCount()):
                if self.layout.itemAtPosition(self.row, i) is not None:
                    self.layout.itemAtPosition(self.row, i).widget().setVisible(False)

        def ShowComment(self):
            """
            Sets the comment text
            """
            self.parent.com_main.setText(self.comment)
            self.parent.com_main.setVisible(True)

            if self.comment2 is None or not globals_.AltSettingIcons:
                self.parent.com_more.setVisible(False)

            else:
                self.parent.com_more.setVisible(True)
                self.parent.com_extra.setText(self.comment2)

            self.parent.com_extra.setVisible(False)
            self.parent.com_box.setVisible(True)

        def ShowComment2(self):
            """
            Sets the comment2 text
            """
            self.parent.com_main.setText(self.comment2)
            self.parent.com_main.setVisible(True)
            self.parent.com_more.setVisible(False)
            self.parent.com_extra.setVisible(False)
            self.parent.com_box.setVisible(True)

        def ShowAdvancedComment(self):
            """
            Sets the advanced comment
            """
            self.parent.com_main.setText(self.commentAdv)
            self.parent.com_main.setVisible(True)
            self.parent.com_more.setVisible(False)
            self.parent.com_extra.setVisible(False)
            self.parent.com_box.setVisible(True)

    class CheckboxPropertyDecoder(PropertyDecoder):
        """
        Class that decodes/encodes sprite data to/from a checkbox
        """

        def __init__(self, title, bit, mask, comment, required, advanced, comment2, commentAdv, layout, row, parent):
            """
            Creates the widget
            """
            super().__init__()

            self.widget = QtWidgets.QCheckBox()
            label = QtWidgets.QLabel(title + ':')
            label.setWordWrap(True)
            label.setAlignment(QtCore.Qt.AlignRight)

            self.comment = comment
            self.comment2 = comment2
            self.commentAdv = commentAdv

            if comment is not None:
                button_com = QtWidgets.QToolButton()

                if not globals_.AltSettingIcons:
                    button_com.setIcon(GetIcon('setting-comment'))
                    button_com.setStyleSheet("border-radius: 50%")

                button_com.clicked.connect(self.ShowComment)
                button_com.setAutoRaise(True)

            else:
                button_com = None

            if comment2 is not None and not globals_.AltSettingIcons:
                button_com2 = QtWidgets.QToolButton()
                button_com2.setIcon(GetIcon('setting-comment2'))
                button_com2.setStyleSheet("border-radius: 50%")
                button_com2.clicked.connect(self.ShowComment2)
                button_com2.setAutoRaise(True)

            else:
                button_com2 = None

            if commentAdv is not None and globals_.AdvancedModeEnabled:
                button_adv = QtWidgets.QToolButton()

                if not globals_.AltSettingIcons:
                    button_adv.setIcon(GetIcon('setting-comment-adv'))
                    button_adv.setStyleSheet("border-radius: 50%")

                button_adv.clicked.connect(self.ShowAdvancedComment)
                button_adv.setAutoRaise(True)

            else:
                button_adv = None

            if button_com is not None or button_com2 is not None or button_adv is not None:
                L = QtWidgets.QHBoxLayout()
                L.setContentsMargins(0, 0, 0, 0)
                L.addWidget(self.widget)

                if button_com is not None:
                    L.addWidget(button_com)

                if button_com2 is not None:
                    L.addWidget(button_com2)

                if button_adv is not None:
                    L.addWidget(button_adv)

                L.addStretch(1)

                widget = QtWidgets.QWidget()
                widget.setLayout(L)

            else:
                widget = self.widget

            self.widget.clicked.connect(self.HandleClick)

            if isinstance(bit, tuple):
                length = bit[1] - bit[0] + 1

            else:
                length = 1

            xormask = (1 << length) - 1

            self.bit = bit
            self.mask = mask
            self.xormask = xormask
            self.required = required
            self.advanced = advanced
            self.parent = parent

            self.row = row
            self.layout = layout

            layout.addWidget(label, row, 0)
            layout.addWidget(widget, row, 1)

        def update(self, data, first=False):
            """
            Updates the value shown by the widget
            """
            # check if requirements are met
            self.checkReq(data, first)
            self.checkAdv()

            value = ((self.retrieve(data) & self.mask) == self.mask)
            self.widget.setChecked(value)

        def assign(self, data):
            """
            Assigns the selected value to the data
            """
            value = self.retrieve(data)

            if self.widget.isChecked():
                value |= self.mask
            elif value & self.mask == self.mask:
                value = 0

            return self.insertvalue(data, value)

        def HandleClick(self, clicked=False):
            """
            Handles clicks on the checkbox
            """
            self.updateData.emit(self)

    class ListPropertyDecoder(PropertyDecoder):
        """
        Class that decodes/encodes sprite data to/from a combobox
        """

        def __init__(self, title, bit, model, comment, required, advanced, comment2, commentAdv, layout, row, parent):
            """
            Creates the widget
            """
            super().__init__()

            self.model = model
            self.widget = QtWidgets.QComboBox()
            self.widget.setModel(model)
            self.parent = parent

            self.widget.currentIndexChanged.connect(self.HandleIndexChanged)
            self.bit = bit
            self.required = required
            self.advanced = advanced

            self.row = row
            self.layout = layout

            self.comment = comment
            self.comment2 = comment2
            self.commentAdv = commentAdv

            if comment is not None:
                button_com = QtWidgets.QToolButton()

                if not globals_.AltSettingIcons:
                    button_com.setIcon(GetIcon('setting-comment'))
                    button_com.setStyleSheet("border-radius: 50%")

                button_com.clicked.connect(self.ShowComment)
                button_com.setAutoRaise(True)

            else:
                button_com = None

            if comment2 is not None and not globals_.AltSettingIcons:
                button_com2 = QtWidgets.QToolButton()
                button_com2.setIcon(GetIcon('setting-comment2'))
                button_com2.setStyleSheet("border-radius: 50%")
                button_com2.clicked.connect(self.ShowComment2)
                button_com2.setAutoRaise(True)

            else:
                button_com2 = None

            if commentAdv is not None and globals_.AdvancedModeEnabled:
                button_adv = QtWidgets.QToolButton()

                if not globals_.AltSettingIcons:
                    button_adv.setIcon(GetIcon('setting-comment-adv'))
                    button_adv.setStyleSheet("border-radius: 50%")

                button_adv.clicked.connect(self.ShowAdvancedComment)
                button_adv.setAutoRaise(True)

            else:
                button_adv = None

            if button_com is not None or button_com2 is not None or button_adv is not None:
                L = QtWidgets.QHBoxLayout()
                L.addStretch(1)

                if button_com is not None:
                    L.addWidget(button_com)

                if button_com2 is not None:
                    L.addWidget(button_com2)

                if button_adv is not None:
                    L.addWidget(button_adv)

                label = QtWidgets.QLabel(title + ':')
                label.setWordWrap(True)

                L.addWidget(label)
                L.setContentsMargins(0, 0, 0, 0)

                widget = QtWidgets.QWidget()
                widget.setLayout(L)

            else:
                widget = QtWidgets.QLabel(title + ':')
                widget.setWordWrap(True)

            layout.addWidget(widget, row, 0, QtCore.Qt.AlignRight)
            layout.addWidget(self.widget, row, 1)

        def update(self, data, first=False):
            """
            Updates the value shown by the widget
            """
            # check if requirements are met
            self.checkReq(data, first)
            self.checkAdv()

            value = self.retrieve(data)
            if not self.model.existingLookup[value]:
                self.widget.setCurrentIndex(-1)
                return

            for i, x in enumerate(self.model.entries):
                if x[0] == value:
                    self.widget.setCurrentIndex(i)
                    break

        def assign(self, data):
            """
            Assigns the selected value to the data
            """
            return self.insertvalue(data, self.model.entries[self.widget.currentIndex()][0])

        def HandleIndexChanged(self, index):
            """
            Handle the current index changing in the combobox
            """
            if index < 0:
                return

            self.updateData.emit(self)

    class ValuePropertyDecoder(PropertyDecoder):
        """
        Class that decodes/encodes sprite data to/from a spinbox
        """

        def __init__(self, title, bit, max, comment, required, advanced, comment2, commentAdv, layout, row, parent):
            """
            Creates the widget
            """
            super().__init__()

            self.widget = QtWidgets.QSpinBox()
            self.widget.setRange(0, max - 1)
            self.parent = parent

            self.comment = comment
            self.comment2 = comment2
            self.commentAdv = commentAdv

            if comment is not None:
                button_com = QtWidgets.QToolButton()

                if not globals_.AltSettingIcons:
                    button_com.setIcon(GetIcon('setting-comment'))
                    button_com.setStyleSheet("border-radius: 50%")

                button_com.clicked.connect(self.ShowComment)
                button_com.setAutoRaise(True)

            else:
                button_com = None

            if comment2 is not None and not globals_.AltSettingIcons:
                button_com2 = QtWidgets.QToolButton()
                button_com2.setIcon(GetIcon('setting-comment2'))
                button_com2.setStyleSheet("border-radius: 50%")
                button_com2.clicked.connect(self.ShowComment2)
                button_com2.setAutoRaise(True)

            else:
                button_com2 = None

            if commentAdv is not None and globals_.AdvancedModeEnabled:
                button_adv = QtWidgets.QToolButton()

                if not globals_.AltSettingIcons:
                    button_adv.setIcon(GetIcon('setting-comment-adv'))
                    button_adv.setStyleSheet("border-radius: 50%")

                button_adv.clicked.connect(self.ShowAdvancedComment)
                button_adv.setAutoRaise(True)

            else:
                button_adv = None

            if button_com is not None or button_com2 is not None or button_adv is not None:
                L = QtWidgets.QHBoxLayout()
                L.addStretch(1)

                if button_com is not None:
                    L.addWidget(button_com)

                if button_com2 is not None:
                    L.addWidget(button_com2)

                if button_adv is not None:
                    L.addWidget(button_adv)

                label = QtWidgets.QLabel(title + ':')
                label.setWordWrap(True)

                L.addWidget(label)
                L.setContentsMargins(0, 0, 0, 0)

                widget = QtWidgets.QWidget()
                widget.setLayout(L)

            else:
                widget = QtWidgets.QLabel(title + ':')
                widget.setWordWrap(True)

            self.widget.valueChanged.connect(self.HandleValueChanged)
            self.bit = bit
            self.required = required
            self.advanced = advanced

            layout.addWidget(widget, row, 0, QtCore.Qt.AlignRight)
            layout.addWidget(self.widget, row, 1)

            self.layout = layout
            self.row = row

        def update(self, data, first=False):
            """
            Updates the value shown by the widget
            """
            # check if requirements are met
            self.checkReq(data, first)
            self.checkAdv()

            value = self.retrieve(data)
            self.widget.setValue(value)

        def assign(self, data):
            """
            Assigns the selected value to the data
            """
            return self.insertvalue(data, self.widget.value())

        def HandleValueChanged(self, value):
            """
            Handle the value changing in the spinbox
            """
            self.updateData.emit(self)

    class BitfieldPropertyDecoder(PropertyDecoder):
        """
        Class that decodes/encodes sprite data to/from a bitfield
        """

        def __init__(self, title, startbit, bitnum, comment, required, advanced, comment2, commentAdv, layout, row, parent):
            """
            Creates the widget
            """
            super().__init__()

            self.startbit = startbit
            self.bitnum = bitnum
            self.required = required
            self.advanced = advanced
            self.parent = parent

            self.widgets = []
            CheckboxLayout = QtWidgets.QGridLayout()
            CheckboxLayout.setContentsMargins(0, 0, 0, 0)

            self.comment = comment
            self.comment2 = comment2
            self.commentAdv = commentAdv

            if comment is not None:
                button_com = QtWidgets.QToolButton()

                if not globals_.AltSettingIcons:
                    button_com.setIcon(GetIcon('setting-comment'))
                    button_com.setStyleSheet("border-radius: 50%")

                button_com.clicked.connect(self.ShowComment)
                button_com.setAutoRaise(True)

            else:
                button_com = None

            if comment2 is not None and not globals_.AltSettingIcons:
                button_com2 = QtWidgets.QToolButton()
                button_com2.setIcon(GetIcon('setting-comment2'))
                button_com2.setStyleSheet("border-radius: 50%")
                button_com2.clicked.connect(self.ShowComment2)
                button_com2.setAutoRaise(True)

            else:
                button_com2 = None

            if commentAdv is not None and globals_.AdvancedModeEnabled:
                button_adv = QtWidgets.QToolButton()

                if not globals_.AltSettingIcons:
                    button_adv.setIcon(GetIcon('setting-comment-adv'))
                    button_adv.setStyleSheet("border-radius: 50%")

                button_adv.clicked.connect(self.ShowAdvancedComment)
                button_adv.setAutoRaise(True)

            else:
                button_adv = None

            if button_com is not None or button_com2 is not None or button_adv is not None:
                L = QtWidgets.QHBoxLayout()
                L.addStretch(1)

                if button_com is not None:
                    L.addWidget(button_com)

                if button_com2 is not None:
                    L.addWidget(button_com2)

                if button_adv is not None:
                    L.addWidget(button_adv)

                label = QtWidgets.QLabel(title + ':')
                label.setWordWrap(True)

                L.addWidget(label)
                L.setContentsMargins(0, 0, 0, 0)

                widget = QtWidgets.QWidget()
                widget.setLayout(L)

            else:
                widget = QtWidgets.QLabel(title + ':')
                widget.setWordWrap(True)

            for i in range(bitnum):
                c = QtWidgets.QCheckBox()
                self.widgets.append(c)
                CheckboxLayout.addWidget(c, 0, i)

                c.toggled.connect(self.HandleValueChanged)

                L = QtWidgets.QLabel(str(i + 1))
                CheckboxLayout.addWidget(L, 1, i)
                CheckboxLayout.setAlignment(L, QtCore.Qt.AlignHCenter)

            w = QtWidgets.QWidget()
            w.setLayout(CheckboxLayout)

            layout.addWidget(widget, row, 0, QtCore.Qt.AlignRight)
            layout.addWidget(w, row, 1)

            self.layout = layout
            self.row = row

        def update(self, data, first=False):
            """
            Updates the value shown by the widget
            """
            # check if requirements are met
            self.checkReq(data, first)
            self.checkAdv()

            value = self.retrieve(data)
            i = self.bitnum

            # run at most self.bitnum times
            while value != 0 and i != 0:
                self.widgets[i].setChecked(value & 1)
                value >>= 1
                i -= 1

        def assign(self, data):
            """
            Assigns the checkbox states to the data
            """
            value = 0

            # construct bitmask
            for i in self.bitnum:
                value = (value | self.widgets[i].isChecked()) << 1

            return self.insertvalue(data, value)

        def HandleValueChanged(self, value):
            """
            Handle any checkbox being changed
            """
            self.updateData.emit(self)

    class MultiboxPropertyDecoder(PropertyDecoder):
        """
        Class that decodes/encodes sprite data to/from a multibox
        """

        def __init__(self, title, bit, comment, required, advanced, comment2, commentAdv, layout, row, parent):
            """
            Creates the widget
            """
            super().__init__()

            if isinstance(bit, tuple):
                bitnum = bit[1] - bit[0]
                startbit = bit[0]

            else:
                bitnum = 1
                startbit = bit

            self.bit = bit
            self.startbit = startbit
            self.bitnum = bitnum
            self.required = required
            self.advanced = advanced
            self.parent = parent

            self.widgets = []
            CheckboxLayout = QtWidgets.QGridLayout()
            CheckboxLayout.setContentsMargins(0, 0, 0, 0)

            for i in range(bitnum):
                c = QtWidgets.QCheckBox(str(bitnum - i))
                c.toggled.connect(self.HandleValueChanged)

                self.widgets.append(c)
                CheckboxLayout.addWidget(c, 0, i)

            w = QtWidgets.QWidget()
            w.setLayout(CheckboxLayout)

            self.comment = comment
            self.comment2 = comment2
            self.commentAdv = commentAdv

            if comment is not None:
                button_com = QtWidgets.QToolButton()

                if not globals_.AltSettingIcons:
                    button_com.setIcon(GetIcon('setting-comment'))
                    button_com.setStyleSheet("border-radius: 50%")

                button_com.clicked.connect(self.ShowComment)
                button_com.setAutoRaise(True)

            else:
                button_com = None

            if comment2 is not None and not globals_.AltSettingIcons:
                button_com2 = QtWidgets.QToolButton()
                button_com2.setIcon(GetIcon('setting-comment2'))
                button_com2.setStyleSheet("border-radius: 50%")
                button_com2.clicked.connect(self.ShowComment2)
                button_com2.setAutoRaise(True)

            else:
                button_com2 = None

            if commentAdv is not None and globals_.AdvancedModeEnabled:
                button_adv = QtWidgets.QToolButton()

                if not globals_.AltSettingIcons:
                    button_adv.setIcon(GetIcon('setting-comment-adv'))
                    button_adv.setStyleSheet("border-radius: 50%")

                button_adv.clicked.connect(self.ShowAdvancedComment)
                button_adv.setAutoRaise(True)

            else:
                button_adv = None

            if button_com is not None or button_com2 is not None or button_adv is not None:
                L = QtWidgets.QHBoxLayout()
                L.addStretch(1)

                if button_com is not None:
                    L.addWidget(button_com)

                if button_com2 is not None:
                    L.addWidget(button_com2)

                if button_adv is not None:
                    L.addWidget(button_adv)

                label = QtWidgets.QLabel(title + ':')
                label.setWordWrap(True)

                L.addWidget(label)
                L.setContentsMargins(0, 0, 0, 0)

                widget = QtWidgets.QWidget()
                widget.setLayout(L)

            else:
                widget = QtWidgets.QLabel(title + ':')
                widget.setWordWrap(True)

            layout.addWidget(widget, row, 0, QtCore.Qt.AlignRight)
            layout.addWidget(w, row, 1)

            self.layout = layout
            self.row = row

        def update(self, data, first=False):
            """
            Updates the value shown by the widget
            """
            # check if requirements are met
            self.checkReq(data, first)
            self.checkAdv()

            value = self.retrieve(data)
            i = self.bitnum - 1

            # run at most self.bitnum times
            while value != 0 and i != 0:
                self.widgets[i].setChecked(value & 1)
                value >>= 1
                i -= 1

        def assign(self, data):
            """
            Assigns the checkbox states to the data
            """
            value = 0

            # construct bitmask
            for i in range(self.bitnum):
                value = (value << 1) | self.widgets[i].isChecked()

            return self.insertvalue(data, value)

        def HandleValueChanged(self, value):
            """
            Handle any checkbox being changed
            """
            self.updateData.emit(self)

    class DualboxPropertyDecoder(PropertyDecoder):
        """
        Class that decodes/encodes sprite data to/from a dualbox
        """

        def __init__(self, title1, title2, bit, comment, required, advanced, comment2, commentAdv, layout, row, parent):
            """
            Creates the widget
            """
            super().__init__()

            self.bit = bit
            self.required = required
            self.advanced = advanced
            self.parent = parent

            self.row = row
            self.layout = layout

            self.buttons = []

            button = QtWidgets.QRadioButton()
            #button.setStyleSheet("height: 18px; width: 18px")
            self.buttons.append(button)

            button = QtWidgets.QRadioButton()
            #button.setStyleSheet("height: 18px; width: 18px")
            self.buttons.append(button)

            for button in self.buttons:
                button.clicked.connect(self.HandleClick)

            label1 = QtWidgets.QLabel(title1)
            label1.setWordWrap(True)
            label2 = QtWidgets.QLabel(title2)
            label2.setWordWrap(True)

            self.comment = comment
            self.comment2 = comment2
            self.commentAdv = commentAdv

            if comment is not None:
                button_com = QtWidgets.QToolButton()

                if not globals_.AltSettingIcons:
                    button_com.setIcon(GetIcon('setting-comment'))
                    button_com.setStyleSheet("QToolButton { border-radius: 50%; }")

                button_com.clicked.connect(self.ShowComment)
                button_com.setAutoRaise(True)

            else:
                button_com = None

            if comment2 is not None and not globals_.AltSettingIcons:
                button_com2 = QtWidgets.QToolButton()
                button_com2.setIcon(GetIcon('setting-comment2'))
                button_com2.setStyleSheet("border-radius: 50%")
                button_com2.clicked.connect(self.ShowComment2)
                button_com2.setAutoRaise(True)

            else:
                button_com2 = None

            if commentAdv is not None and globals_.AdvancedModeEnabled:
                button_adv = QtWidgets.QToolButton()

                if not globals_.AltSettingIcons:
                    button_adv.setIcon(GetIcon('setting-comment-adv'))
                    button_adv.setStyleSheet("border-radius: 50%")

                button_adv.clicked.connect(self.ShowAdvancedComment)
                button_adv.setAutoRaise(True)

            else:
                button_adv = None

            if button_com is not None or button_com2 is not None or button_adv is not None:
                L = QtWidgets.QHBoxLayout()

                if button_com is not None:
                    L.addWidget(button_com)

                if button_com2 is not None:
                    L.addWidget(button_com2)

                if button_adv is not None:
                    L.addWidget(button_adv)

                L.setContentsMargins(0, 0, 0, 0)

                widget = QtWidgets.QWidget()
                widget.setLayout(L)

            else:
                widget = None

            L = QtWidgets.QHBoxLayout()
            L.addStretch(1)
            L.addWidget(label1)
            L.addWidget(self.buttons[0])
            L.addWidget(QtWidgets.QLabel("|"))

            if widget is not None:
                L.addWidget(widget)
                L.addWidget(QtWidgets.QLabel("|"))

            L.addWidget(self.buttons[1])
            L.addWidget(label2)
            L.addStretch(1)

            L.setContentsMargins(0, 0, 0, 0)

            # span 2 columns
            w = QtWidgets.QWidget()
            w.setLayout(L)
            layout.addWidget(w, row, 0, 1, 2)

        def update(self, data, first=False):
            """
            Updates the value shown by the widget
            """
            # check if requirements are met
            self.checkReq(data, first)
            self.checkAdv()

            value = self.retrieve(data) & 1

            self.buttons[value].setChecked(True)
            self.buttons[not value].setChecked(False)

        def assign(self, data):
            """
            Assigns the selected value to the data
            """
            value = self.buttons[1].isChecked()

            return self.insertvalue(data, value)

        def HandleClick(self, clicked=False):
            """
            Handles clicks on the checkbox
            """
            self.updateData.emit(self)

    class ExternalPropertyDecoder(PropertyDecoder):
        # (6, title, bit, comment, required, advanced, comment2, advancedcomment, type)

        def __init__(self, title, bit, comment, required, advanced, comment2, advancedcomment, type, layout, row, parent):
            """
            Creates the widget
            """
            super().__init__()

            self.bit = bit
            self.row = row
            self.layout = layout
            self.parent = parent
            self.comment = comment
            self.advanced = advanced
            self.comment2 = comment2
            self.required = required
            self.commentAdv = advancedcomment
            self.type = type
            self.dispvalue = 0

            if comment is not None:
                button_com = QtWidgets.QToolButton()

                if not globals_.AltSettingIcons:
                    button_com.setIcon(GetIcon('setting-comment'))
                    button_com.setStyleSheet("border-radius: 50%")

                button_com.clicked.connect(self.ShowComment)
                button_com.setAutoRaise(True)

            else:
                button_com = None

            if comment2 is not None and not globals_.AltSettingIcons:
                button_com2 = QtWidgets.QToolButton()
                button_com2.setIcon(GetIcon('setting-comment2'))
                button_com2.setStyleSheet("border-radius: 50%")
                button_com2.clicked.connect(self.ShowComment2)
                button_com2.setAutoRaise(True)

            else:
                button_com2 = None

            if advancedcomment is not None and globals_.AdvancedModeEnabled:
                button_adv = QtWidgets.QToolButton()

                if not globals_.AltSettingIcons:
                    button_adv.setIcon(GetIcon('setting-comment-adv'))
                    button_adv.setStyleSheet("border-radius: 50%")

                button_adv.clicked.connect(self.ShowAdvancedComment)
                button_adv.setAutoRaise(True)

            else:
                button_adv = None

            if button_com is not None or button_com2 is not None or button_adv is not None:
                L = QtWidgets.QHBoxLayout()
                L.addStretch(1)

                if button_com is not None:
                    L.addWidget(button_com)

                if button_com2 is not None:
                    L.addWidget(button_com2)

                if button_adv is not None:
                    L.addWidget(button_adv)

                label = QtWidgets.QLabel(title + ':')
                label.setWordWrap(True)

                L.addWidget(label)
                L.setContentsMargins(0, 0, 0, 0)

                widget = QtWidgets.QWidget()
                widget.setLayout(L)

            else:
                widget = QtWidgets.QLabel(title + ':')
                widget.setWordWrap(True)

            bits = bit[1] - bit[0]

            # button that contains the current value
            self.button = QtWidgets.QPushButton()

            # spinbox that contains the current value
            self.box = QtWidgets.QSpinBox()
            self.box.setRange(0, (2 ** bits) - 1)
            self.box.setValue(self.dispvalue)

            L2 = QtWidgets.QHBoxLayout()
            L2.addWidget(self.button)
            L2.addWidget(self.box)
            L2.setContentsMargins(0, 0, 0, 0)

            rightwidget = QtWidgets.QWidget()
            rightwidget.setLayout(L2)

            self.button.clicked.connect(self.HandleClicked)
            self.box.valueChanged.connect(self.HandleValueChanged)

            layout.addWidget(widget, row, 0, QtCore.Qt.AlignRight)
            layout.addWidget(rightwidget, row, 1)

        def update(self, data, first=False):
            """
            Updates the info
            """
            # check if requirements are met
            self.checkReq(data, first)
            self.checkAdv()

            self.dispvalue = self.retrieve(data)
            self.button.setText(self.getShortForValue(self.dispvalue))
            self.box.setValue(self.dispvalue)

        def assign(self, data):
            """
            Assigns the currently selected value to data
            """
            return self.insertvalue(data, self.dispvalue)

        def HandleClicked(self, e):
            """
            Handles the button being clicked.
            """
            dlg = ExternalSpriteOptionDialog(self.type, self.dispvalue)

            # only contine if the user pressed "OK"
            if dlg.exec_() != QtWidgets.QDialog.Accepted:
                return

            # read set value from dlg and update self.dispwidget
            self.dispvalue = dlg.getValue()
            self.button.setText(self.getShortForValue(self.dispvalue))
            self.box.setValue(self.dispvalue)

            # update all other fields
            self.updateData.emit(self)

        def HandleValueChanged(self, value):
            """
            Handles the spin value being changed
            """
            self.dispvalue = value
            self.button.setText(self.getShortForValue(self.dispvalue))

            # update all other fields
            self.updateData.emit(self)

        def getShortForValue(self, value):
            """
            Gets the short form from the xml for a value
            """

            # find correct xml
            filename = globals_.gamedef.externalFile(self.type + '.xml')
            if not os.path.isfile(filename):
                raise Exception # file does not exist

            # parse the xml
            tree = ElementTree.parse(filename)
            root = tree.getroot()

            try:
                fmt = root.attrib['short']
            except:
                return str(value)

            option = None
            for option_ in root:
                # skip if this is not an <option> or it's not for the correct value
                if option_.tag.lower() == 'option' and int(option_.attrib['value'], 0) == int(value):
                    option = option_
                    break

            if option is None:
                return str(value)

            # Do replacements
            for prop in option:
                name = "[%s]" % prop.attrib['name']
                fmt = fmt.replace(name, prop.attrib['value'])

            del tree, root

            # Do some automatic replacements
            replace = {
                '[b]': '<b>',
                '[/b]': '</b>',
                '[i]': '<i>',
                '[/i]': '</i>',
            }

            for old in replace:
                fmt = fmt.replace(old, replace[old])

            # only display the first 27 characters and ...
            # so len(fmt) is at most 30.
            if len(fmt) > 30:
                fmt = fmt[:27] + '...'

            # Return it
            return fmt

    class MultiDualboxPropertyDecoder(PropertyDecoder):
        """
        Class that decodes/encodes sprite data to/from a row of dualboxes
        """

        def __init__(self, title1, title2, bit, comment, required, advanced, comment2, commentAdv, layout, row, parent):
            """
            Creates the widget
            """
            super().__init__()

            self.bit = bit
            self.required = required
            self.advanced = advanced
            self.parent = parent
            self.layout = layout
            self.row = row
            self.comment = comment
            self.comment2 = comment2
            self.commentAdv = commentAdv

            if isinstance(bit, tuple):
                self.bitnum = bit[1] - bit[0]
                self.startbit = bit[0]

            else:
                self.bitnum = 1
                self.startbit = bit

            self.widgets = []
            DualboxLayout = QtWidgets.QGridLayout()
            DualboxLayout.setContentsMargins(0, 0, 0, 0)

            for i in range(self.bitnum):
                dualbox = QSliderSwitch(QSliderSwitch.Vertical, "#F00000")
                dualbox.clicked.connect(self.HandleValueChanged)

                self.widgets.append(dualbox)
                DualboxLayout.addWidget(dualbox, 0, i)

            w = QtWidgets.QWidget()
            w.setLayout(DualboxLayout)

            if comment is not None:
                button_com = QtWidgets.QToolButton()

                if not globals_.AltSettingIcons:
                    button_com.setIcon(GetIcon('setting-comment'))
                    button_com.setStyleSheet("QToolButton { border-radius: 50%; }")

                button_com.clicked.connect(self.ShowComment)
                button_com.setAutoRaise(True)

            else:
                button_com = None

            if comment2 is not None and not globals_.AltSettingIcons:
                button_com2 = QtWidgets.QToolButton()
                button_com2.setIcon(GetIcon('setting-comment2'))
                button_com2.setStyleSheet("QToolButton { border-radius: 50%; }")
                button_com2.clicked.connect(self.ShowComment2)
                button_com2.setAutoRaise(True)

            else:
                button_com2 = None

            if commentAdv is not None and globals_.AdvancedModeEnabled:
                button_adv = QtWidgets.QToolButton()

                if not globals_.AltSettingIcons:
                    button_adv.setIcon(GetIcon('setting-comment-adv'))
                    button_adv.setStyleSheet("QToolButton { border-radius: 50%; }")

                button_adv.clicked.connect(self.ShowAdvancedComment)
                button_adv.setAutoRaise(True)

            else:
                button_adv = None

            L = QtWidgets.QHBoxLayout()
            L.setContentsMargins(0, 0, 0, 0)
            L.addStretch(1)

            if button_com is not None:
                L.addWidget(button_com)

            if button_com2 is not None:
                L.addWidget(button_com2)

            if button_adv is not None:
                L.addWidget(button_adv)


            L2 = QtWidgets.QVBoxLayout()

            label1 = QtWidgets.QLabel(title1)
            label1.setWordWrap(True)
            label2 = QtWidgets.QLabel(title2)
            label2.setWordWrap(True)

            L2.addWidget(label1, 0, QtCore.Qt.AlignRight)
            L2.addWidget(label2, 0, QtCore.Qt.AlignRight)

            L.addLayout(L2)
            widget = QtWidgets.QWidget()
            widget.setLayout(L)

            layout.addWidget(widget, row, 0, QtCore.Qt.AlignRight)
            layout.addWidget(w, row, 1)

        def HandleValueChanged(self, _):
            """
            Handles clicks on the radiobutton
            """
            self.updateData.emit(self)

        def update(self, data, first=False):
            """
            Updates the value shown by the widget
            """
            # check if requirements are met
            self.checkReq(data, first)
            self.checkAdv()

            value = self.retrieve(data)
            i = self.bitnum - 1

            # run at most self.bitnum times
            while value != 0 and i >= 0:
                self.widgets[i].setValue(value & 1)
                value >>= 1
                i -= 1

        def assign(self, data):
            """
            Assigns the checkbox states to the data
            """
            value = 0

            # construct bitmask
            for i in range(self.bitnum):
                value = (value << 1) | self.widgets[i].getValue()

            return self.insertvalue(data, value)


    def setSprite(self, type, reset=False):
        """
        Change the sprite type used by the data editor
        """
        if (self.spritetype == type) and not reset:
            return

        self.spritetype = type
        if type != 1000:
            sprite = globals_.Sprites[type]

        else:
            sprite = None

        # remove all the existing widgets in the layout
        self.clearMessages()

        layout = self.editorlayout
        for row in range(2, layout.rowCount()):
            for column in range(0, layout.columnCount()):
                w = layout.itemAtPosition(row, column)
                if w is not None:
                    widget = w.widget()
                    layout.removeWidget(widget)
                    widget.setParent(None)

        # show the raw editor if advanced mode is enabled
        self.showRawData.setVisible(not globals_.AdvancedModeEnabled)
        self.raweditor.setVisible(globals_.AdvancedModeEnabled)
        self.editbox.setVisible(globals_.AdvancedModeEnabled)
        self.resetButton.setVisible(not globals_.HideResetSpritedata and (globals_.AdvancedModeEnabled or len(sprite.fields) > 0))

        # show size stuff
        self.sizeButton.setVisible(sprite.size)

        # Nothing is selected, so no comments should appear
        self.com_box.setVisible(False)

        if sprite is None:
            self.spriteLabel.setText(globals_.trans.string('SpriteDataEditor', 5, '[id]', type))
            self.noteButton.setVisible(False)
            self.yoshiInfo.setVisible(False)
            self.advNoteButton.setVisible(False)
            self.asm.setVisible(False)

            if len(self.fields) > 0:
                self.fields = []

            return

        self.spriteLabel.setText(globals_.trans.string('SpriteDataEditor', 6, '[id]', type, '[name]', sprite.name))

        if sprite.notes is not None:
            self.noteButton.setVisible(True)
            self.com_main.setText(sprite.notes)
            self.com_main.setVisible(True)
            self.com_more.setVisible(False)
            self.com_extra.setVisible(False)
            self.com_box.setVisible(True)

        self.notes = sprite.notes

        # advanced comment
        self.advNoteButton.setVisible(globals_.AdvancedModeEnabled and sprite.advNotes is not None)
        self.advNotes = sprite.advNotes

        self.relatedObjFilesButton.setVisible(sprite.relatedObjFiles is not None)
        self.relatedObjFiles = sprite.relatedObjFiles

        self.asm.setVisible(sprite.asm is True)

        # dependency stuff
        # first clear current dependencies
        l = self.com_deplist
        for row in range(l.rowCount()):
            for column in range(l.columnCount()):
                w = l.itemAtPosition(row, column)
                if w is not None:
                    widget = w.widget()
                    l.removeWidget(widget)
                    widget.setParent(None)

        rownum = 0

        # (sprite id, importance level)
        # importance level is 0 for 'required', 1 for 'suggested'
        missing = [[], []]
        cur_sprites = [s.type for s in globals_.Area.sprites]
        for dependency, importance in sprite.dependencies:
            if dependency not in cur_sprites:
                missing[importance].append(dependency)

        # if there are missing things
        for missingSprite in missing[0]:
            name = globals_.trans.string('SpriteDataEditor', 20, '[id]', missingSprite)
            action = 'Add Sprite' # TODO: Make this translatable
            addButton = QtWidgets.QPushButton(action)

            message = self.addMessage(name, level = 0, close = action)
            callback = self.closeMessageCallback(message, self.HandleSpritePlaced(missingSprite, addButton))
            self.addCallbackToMessage(message, callback)

            addButton.clicked.connect(callback)

            self.com_deplist.addWidget(QtWidgets.QLabel(name), rownum, 0)
            self.com_deplist.addWidget(addButton, rownum, 1)

            rownum += 1

        for missingSprite in missing[1]:
            name = globals_.trans.string('SpriteDataEditor', 21, '[id]', missingSprite)
            action = 'Add Sprite' # TODO: Make this translatable

            addButton = QtWidgets.QPushButton(action)
            addButton.clicked.connect(self.HandleSpritePlaced(missingSprite, addButton))

            self.com_deplist.addWidget(QtWidgets.QLabel(name), rownum, 0)
            self.com_deplist.addWidget(addButton, rownum, 1)
            rownum += 1

        # dependency notes
        self.depButton.setVisible(sprite.dependencynotes is not None)
        self.com_deplist_w.setVisible(False)
        self.com_dep.setVisible(False)

        if sprite.dependencynotes is not None:
            self.dependencyNotes = sprite.dependencynotes

        # yoshi info
        if sprite.noyoshi is True:
            image = "ys-no"
        elif sprite.noyoshi is not None:
            image = "ys-works"
        else:
            image = None

        if sprite.yoshiNotes is not None:
            if image is None:
                image = "ys-works"

            self.yoshiIcon.setVisible(False)
            self.yoshiInfo.setIcon(GetIcon(image))
            self.yoshiInfo.setVisible(True)
            self.yoshiNotes = sprite.yoshiNotes

        else:
            if image is None:
                self.yoshiIcon.setVisible(False)
            else:
                self.yoshiIcon.setPixmap(GetIcon(image).pixmap(64, 64))
                self.yoshiIcon.setVisible(True)

            self.yoshiInfo.setVisible(False)

        # create all the new fields
        fields = []
        row = 2

        for f in sprite.fields:
            if f[0] == 0:
                nf = SpriteEditorWidget.CheckboxPropertyDecoder(f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8], layout, row, self)

            elif f[0] == 1:
                nf = SpriteEditorWidget.ListPropertyDecoder(f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8], layout, row, self)

            elif f[0] == 2:
                nf = SpriteEditorWidget.ValuePropertyDecoder(f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8], layout, row, self)

            elif f[0] == 3:
                nf = SpriteEditorWidget.BitfieldPropertyDecoder(f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8], layout, row, self)

            elif f[0] == 4:
                nf = SpriteEditorWidget.MultiboxPropertyDecoder(f[1], f[2], f[3], f[4], f[5], f[6], f[7], layout, row, self)

            elif f[0] == 5:
                nf = SpriteEditorWidget.DualboxPropertyDecoder(f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8], layout, row, self)

            elif f[0] == 6:
                nf = SpriteEditorWidget.ExternalPropertyDecoder(f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8], layout, row, self)

            elif f[0] == 7:
                nf = SpriteEditorWidget.MultiDualboxPropertyDecoder(f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8], layout, row, self)

            nf.updateData.connect(self.HandleFieldUpdate)
            fields.append(nf)
            row += 1

        self.fields = fields
        self.update(True)

    def addMessage(self, text, action = None, level = 0, close = "x"):
        """
        Adds a message to the message layout which can be removed
        """
        # buttonbg, buttontext, widgettext, widgetbg, widgetborder
        if level == 0:
            # red
            colours = ('black', 'white', 'white', '#CF3038', 'darkred')
        elif level == 1:
            # orange
            colours = ('#FFA500', 'black', 'black', '#FFA500', '#FF8C00')
        elif level == 2:
            # neutral
            colours = ('none', 'black', 'black', 'none', 'black')
        elif level == 3:
            # green
            colours = ('green', 'white', 'white', 'green', 'darkgreen')
        else:
            # neutral
            colours = ('none', 'black', 'black', 'none', 'black')

        label = QtWidgets.QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet("""
            QLabel {
                color: %s;
            }
        """ % colours[2])

        close = QtWidgets.QPushButton(close)
        close.setStyleSheet("""
            QPushButton {
                background: %s;
                color: %s;
            }
        """ % colours[:2])

        L = QtWidgets.QHBoxLayout()
        L.addWidget(label)
        L.addStretch(1)
        L.addWidget(close)

        message = QtWidgets.QWidget()
        message.setStyleSheet("""
            .QWidget {
                background: %s;
                border: 2px solid %s;
                border-radius: 3px;
            }
        """ % colours[3:])
        message.setLayout(L)

        close.clicked.connect(self.closeMessageCallback(message, action))

        self.msg_layout.addWidget(message)

        return message

    def clearMessages(self):
        """
        Clears all messages
        """
        l = self.msg_layout

        for row in range(l.count()):
            w = l.itemAt(row)
            if w is not None:
                widget = w.widget()
                l.removeWidget(widget)
                widget.setParent(None)

    def closeMessageCallback(self, message_, action_):
        """
        Gets callback for the close button of messages
        """
        layout_ = self.msg_layout

        def callback(e):
            if action_ is not None:
                action_()

            # remove message from layout
            layout_.removeWidget(message_)
            message_.setParent(None)

        return callback

    def addCallbackToMessage(self, message, callback):
        """
        Adds a callback to the clicked attribute of the button of a message
        """
        l = self.msg_layout

        for row in range(l.count()):
            w = l.itemAt(row)
            if w is not None and w.widget() == message:
                layout = message.layout()
                close = layout.itemAt(layout.count() - 1).widget()
                close.clicked.connect(callback)
                break

    def update(self, first=False):
        """
        Updates all the fields to display the appropriate info
        """
        self.UpdateFlag = True

        data = self.data

        self.raweditor.setText('%02x%02x %02x%02x %02x%02x %02x%02x' % (
            data[0], data[1], data[2], data[3],
            data[4], data[5], data[6], data[7],
        ))

        self.raweditor.setStyleSheet('')

        # Go through all the data
        for f in self.fields:
            f.update(data, first)

        self.UpdateFlag = False

        # minimise width
        if globals_.mainWindow.spriteEditorDock.isFloating():
            self.window().resize(0, self.height())

    def ShowNoteTooltip(self):
        """
        Show notes
        """
        self.com_dep.setVisible(False)
        self.com_main.setText(self.notes)
        self.com_main.setVisible(True)
        self.com_more.setVisible(False)
        self.com_extra.setVisible(False)
        self.com_box.setVisible(True)

    def ShowRelatedObjFilesTooltip(self):
        """
        Show related obj files
        """
        self.com_dep.setVisible(False)
        self.com_main.setText(self.relatedObjFiles)
        self.com_more.setVisible(False)
        self.com_box.setVisible(True)

    def ShowYoshiTooltip(self):
        """
        Show the Yoshi info
        """
        self.com_dep.setVisible(False)
        self.com_main.setText(self.yoshiNotes)
        self.com_more.setVisible(False)
        self.com_box.setVisible(True)

    def ShowAdvancedNoteTooltip(self):
        """
        Show the advanced notes
        """
        self.com_dep.setVisible(False)
        self.com_main.setText(self.advNotes)
        self.com_more.setVisible(False)
        self.com_box.setVisible(True)

    def ShowMoreComments(self):
        """
        Show or hide the extra comment
        """
        self.com_dep.setVisible(False)

        if self.com_extra.isVisible():
            self.com_extra.setVisible(False)
            self.com_more.setText(globals_.trans.string('SpriteDataEditor', 13))
            self.com_main.setVisible(True)
            self.com_dep

        else:
            self.com_extra.setVisible(True)
            self.com_more.setText(globals_.trans.string('SpriteDataEditor', 14))
            self.com_main.setVisible(False)

    def ShowDependencies(self):
        """
        Show dependencies
        """
        self.com_main.setText(self.dependencyNotes)
        self.com_main.setVisible(True)
        self.com_extra.setVisible(False)
        self.com_deplist_w.setVisible(False)
        self.com_dep.setText(globals_.trans.string('SpriteDataEditor', 18))
        self.com_dep.setVisible(self.com_deplist.count() > 0)

    def DependencyToggle(self):
        """
        The button was clicked
        """
        if not self.com_main.isVisible():
            self.com_box.setMaximumHeight(120)
            w = self.com_box.width()
            self.com_box.resize(w, 120)

            self.com_dep.setText(globals_.trans.string('SpriteDataEditor', 18))
            self.com_deplist_w.setVisible(False)
            self.com_main.setVisible(True)

        else:
            self.com_box.setMaximumHeight(200)
            w = self.com_box.width()
            self.com_box.resize(w, 200)

            self.com_dep.setText(globals_.trans.string('SpriteDataEditor', 19))
            self.com_main.setVisible(False)
            self.com_deplist_w.setVisible(True)

    def HandleFieldUpdate(self, field):
        """
        Triggered when a field's data is updated
        """
        if self.UpdateFlag: return

        data = field.assign(self.data)
        self.data = data

        self.raweditor.setText('%02x%02x %02x%02x %02x%02x %02x%02x' % (
            data[0], data[1], data[2], data[3],
            data[4], data[5], data[6], data[7],
        ))

        self.raweditor.setStyleSheet('')

        for f in self.fields:
            if f != field: f.update(data)

        self.DataUpdate.emit(data)

    def HandleResetData(self):
        """
        Handles the reset data button being clicked
        """
        self.data = b'\0\0\0\0\0\0\0\0'
        data = self.data

        self.UpdateFlag = True

        for f in self.fields:
            f.update(data)

        self.UpdateFlag = False

        self.DataUpdate.emit(data)

        data = ['0' * 4] * 4
        self.raweditor.setText(' '.join(data))
        self.raweditor.setStyleSheet('QLineEdit { background-color: #ffffff; }')

    def HandleRawDataEdited(self, text):
        """
        Triggered when the raw data textbox is edited
        """

        raw = text.replace(' ', '')
        valid = False

        if len(raw) == 16:
            try:
                data = bytes([int(raw[r:r + 2], 16) for r in range(0, len(raw), 2)])
                valid = True

            except Exception:
                pass

        # if it's valid, let it go
        if valid:
            self.raweditor.setStyleSheet('')
            self.data = data

            self.UpdateFlag = True
            for f in self.fields: f.update(data)
            self.UpdateFlag = False

            self.DataUpdate.emit(data)
            self.raweditor.setStyleSheet('')

        else:
            self.raweditor.setStyleSheet('QLineEdit { background-color: #ffd2d2; }')

    def HandleShowRawData(self, e):
        """
        Shows raw data
        """
        self.showRawData.setVisible(False)
        self.raweditor.setVisible(True)
        self.editbox.setVisible(True)

    def HandleSpritePlaced(self, id_, button_):
        def placeSprite():
            mw = globals_.mainWindow

            x_ = mw.selObj.objx + 16
            y_ = mw.selObj.objy
            data_ = mw.defaultDataEditor.data

            spr = SpriteItem(id_, x_, y_, data_)
            spr.positionChanged = mw.HandleSprPosChange

            mw.scene.addItem(spr)
            globals_.Area.sprites.append(spr)

            spr.listitem = ListWidgetItem_SortsByOther(spr)
            mw.spriteList.addItem(spr.listitem)

            SetDirty()
            spr.UpdateListItem()

            # remove this dependency, because it is now fulfilled.
            # get row of button
            idx = self.com_deplist.indexOf(button_)
            row, _, _, _ = self.com_deplist.getItemPosition(idx)

            # remove this row
            l = self.com_deplist
            for column in range(l.columnCount()):
                w = l.itemAtPosition(row, column)
                if w is not None:
                    widget = w.widget()
                    l.removeWidget(widget)
                    widget.setParent(None)


        return placeSprite

    def HandleSizeButtonClicked(self, e):
        """
        Handles the 'resize' button being clicked
        """
        dlg = ResizeChoiceDialog(self.spritetype)

        # only contine if the user pressed "OK"
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return


class ExternalSpriteOptionDialog(QtWidgets.QDialog):
    """
    Dialog for the external sprite option.
    """

    def __init__(self, type, current):
        """
        Initialise the dialog
        """
        QtWidgets.QDialog.__init__(self)

        # create edit thing based on type
        # each of these functions should assign the editing thing to self.widget
        self.type = type

        items, order = self.loadItemsFromXML()
        self.fillWidgetFromItems(items, order)

        self.value = current

        # make the layout of ExternalSpriteOptionWidgets
        self.widget = QtWidgets.QWidget()
        self.buttons = []
        self.visibleEntries = []

        L = QtWidgets.QVBoxLayout()
        self.buttongroup = QtWidgets.QButtonGroup()

        # create a widget for every entry
        self.widgets = []
        for i, widget in enumerate(self.entries):
            button = QtWidgets.QRadioButton()
            button.setChecked(i == self.value)
            self.buttongroup.addButton(button, i)

            self.widgets.append(
                ExternalSpriteOptionRow(button, widget[0], widget[1])
            )

        self.widget.setLayout(L)

        # search thing
        searchbar = QtWidgets.QLineEdit()
        searchbar.textEdited.connect(self.search)

        L = QtWidgets.QHBoxLayout()
        L.addWidget(QtWidgets.QLabel("Search:"))
        L.addWidget(searchbar)

        search = QtWidgets.QWidget()
        search.setLayout(L)

        # create layout
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        scrollWidget = QtWidgets.QScrollArea()
        scrollWidget.setWidget(self.widget)
        scrollWidget.setWidgetResizable(True)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(search)
        mainLayout.addWidget(scrollWidget)
        mainLayout.addWidget(buttonBox, 0, QtCore.Qt.AlignBottom)

        self.setLayout(mainLayout)

        self.updateVisibleRows(list(range(len(self.entries))))

        # Keep col widths constant
        #layout = self.widget.layout()
        #colCount = layout.columnCount()
        #rowCount = layout.rowCount()

        #for column in range(colCount):
        #    for row in range(rowCount):
        #        try:
        #            width = layout.itemAtPosition(row, column).widget().width()
        #            layout.itemAtPosition(row, column).widget().setFixedWidth(width)
        #        except:
        #            pass

    def loadItemsFromXML(self):
        """
        Returns the items from the correct XML
        """
        # find correct xml
        filename = globals_.gamedef.externalFile(self.type + '.xml')
        if not os.path.isfile(filename):
            raise Exception # file does not exist

        # parse the xml
        options = {}
        primary = []
        secondary = []

        tree = ElementTree.parse(filename)
        root = tree.getroot()

        try:
            primary += list(map(
                lambda x: None if x.strip().lower() == "[id]" else x.strip(),
                root.attrib['primary'].split(',')
            ))
        except:
            pass

        try:
            secondary += list(map(
                lambda x: x.strip(),
                root.attrib['secondary'].split(',')
            ))
        except:
            pass

        for option in root:
            # skip if this is not an <option>
            if option.tag.lower() != 'option':
                continue

            # read properties and put it in this dict
            properties = {}
            for prop in option:
                if prop.tag.lower() != 'property':
                    continue

                name = prop.attrib['name']
                value = prop.attrib['value']

                properties[name] = value

            # parse the value [can be hexadecimal, binary or octal]
            value = int(option.attrib['value'], 0)

            # save it
            options[value] = properties

        # delete the xml stuff
        del tree, root

        return (options, (primary, secondary))

    def fillWidgetFromItems(self, options, order):
        """
        Adds items to the layout
        """
        # list of widgets sorted by value
        self.entries = []

        for option in options:
            items = options[option]
            subwidgets = ([], [])

            for prop in order[0]:
                if prop == None:
                    value = option
                else:
                    value = items[prop]

                subwidgets[0].append(value)

            # secondary items are optional
            for prop in order[1]:
                if prop in items:
                    subwidgets[1].append(items[prop])

            self.entries.append(subwidgets)

    def setCurrentValue(self, value):
        """
        Sets the current value to 'value'
        """
        self.buttongroup.button(value).setChecked(True)

    def getValue(self):
        """
        Gets the current value
        """
        return self.buttongroup.checkedId()

    def search(self, text):
        """
        Only show the elements fulfilling the search for text
        """
        # TODO: maybe let another thread handle this...
        # Don't do anything if you search for fewer than 2 characters
        if len(text) < 2:
            return

        matches = lambda haystack, needle: haystack.lower().find(needle.lower()) >= 0

        matching = []
        for i, entry in enumerate(self.entries):
            for property in entry[0]: # primary
                if matches(str(property), text):
                    matching.append(i)
                    break
            else:
                for property in entry[1]: # secondary
                    if matches(str(property), text):
                        matching.append(i)
                        break

        self.updateVisibleRows(matching)

    def updateVisibleRows(self, new):
        """
        Makes sure we only show the correct rows
        """

        layout = self.widget.layout()

        # clear layout
        self.clearLayout(layout)

        # add back the correct ones
        for id in new:
            row = self.widgets[id]

            # add row to the layout
            layout.addWidget(row)

        # add stretch so the items align to the top
        layout.addStretch()

        self.visibleEntries = new

    def clearLayout(self, layout):
        """
        Removes all rows of the layout
        """
        while True:
            item = layout.takeAt(0)
            if item is None:
                break

            wid = item.widget()
            del item

            if wid is None:
                continue

            # don't delete the widget, since we might need to show it again later
            wid.setParent(None)


class ExternalSpriteOptionRow(QtWidgets.QWidget):
    def __init__(self, button, primary, secondary):
        QtWidgets.QWidget.__init__(self)

        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.addWidget(button, 0, 0, 1, 1)
        self.setLayout(self.gridLayout)

        for i, text in enumerate(primary):
            label = QtWidgets.QLabel(str(text))
            self.gridLayout.addWidget(label, 0, i + 1, 1, 1)

        self.secondary = []

        if len(secondary) == 0:
            return

        placedText = False
        for i, text in enumerate(secondary):
            if str(text) == "":
                continue

            placedText = True
            label = QtWidgets.QLabel(str(text))
            label.setWordWrap(True)

            self.secondary.append(label)

        if placedText:
            more = QtWidgets.QPushButton("v")
            more.clicked.connect(self.handleButtonClick)

            self.gridLayout.addWidget(more, 0, len(primary) + 1, 1, 1)

    def handleButtonClick(self, e):
        """
        Handles button click
        """

        layout = self.gridLayout
        cols = layout.columnCount()
        button = layout.itemAtPosition(0, cols - 1).widget()

        width = (cols - 1) // len(self.secondary)

        if button.text() == "v":
            button.setText("^")

            for i, label in enumerate(self.secondary):
                layout.addWidget(label, 1, i + 1, 1, width)
        else:
            button.setText("v")

            for label in self.secondary:
                label.setParent(None)


class ResizeChoiceDialog(QtWidgets.QDialog):
    """
    Dialog for the resize option.
    """
    # TODO: Think critically about the design/behaviour/goal of this dialog
    # TODO: Add size selector to the sprite editor
    # TODO: Make this translatable

    def __init__(self, spriteid):
        """
        Initialise the dialog
        """
        QtWidgets.QDialog.__init__(self)

        self.sprite = globals_.Sprites[spriteid]

        text = "Let's resize your sprite. In order to do this, choose one of " \
               "the two slots, based on the below information. Note that some " \
               "choices can overlap with other settings, leading to undesired " \
               "effects."

        text2 = "Click the button below to create a Special Event sprite with " \
                "the selected slot."

        text3 = "Please note that there already is a resizer sprite that affects " \
                "this sprite. All changes made here will apply to the entire zone/area " \
                "so be careful."

        text4 = "More than 1 resizer is a <b>very</b> bad idea. Please don't do " \
                "this and remove the extra resizers."

        ## Slots
        used = self.getNyb5And7Availability()
        self.present = self.getSpecialEventAvailability()

        rows = max(len(used[5]), len(used[7]), 1)

        self.buttongroup = QtWidgets.QButtonGroup()
        self.radio1 = QtWidgets.QRadioButton()
        self.buttongroup.addButton(self.radio1, 0)
        self.radio2 = QtWidgets.QRadioButton()
        self.buttongroup.addButton(self.radio2, 1)
        self.radio3 = QtWidgets.QRadioButton()
        self.buttongroup.addButton(self.radio3, -1)

        header = QtWidgets.QLabel("Slots")
        footer = QtWidgets.QLabel(text2)

        if len(self.present) == 0:
            label = "Create"
        elif len(self.present) == 1:
            label = "Edit"
        else:
            label = "Nothing."

        createButton = QtWidgets.QPushButton(label)
        createButton.clicked.connect(self.doAThing)

        a_label = QtWidgets.QLabel("A")
        b_label = QtWidgets.QLabel("B")
        g_label = QtWidgets.QLabel("Global")

        slotsLayout = QtWidgets.QGridLayout()
        slotsLayout.setContentsMargins(0, 0, 0, 0)
        slotsLayout.addWidget(header,      0, 0, 1, 3, QtCore.Qt.AlignHCenter)
        slotsLayout.addWidget(a_label,     1, 0, 1, 1, QtCore.Qt.AlignHCenter)
        slotsLayout.addWidget(self.radio1, 2, 0, 1, 1, QtCore.Qt.AlignHCenter)
        slotsLayout.addWidget(b_label,     1, 1, 1, 1, QtCore.Qt.AlignHCenter)
        slotsLayout.addWidget(self.radio2, 2, 1, 1, 1, QtCore.Qt.AlignHCenter)
        slotsLayout.addWidget(g_label,     1, 2, 1, 1, QtCore.Qt.AlignHCenter)
        slotsLayout.addWidget(self.radio3, 2, 2, 1, 1, QtCore.Qt.AlignHCenter)

        if len(used[5]) == 0:
            slotsLayout.addWidget(QtWidgets.QLabel("None"), 3, 0, 1, 1, QtCore.Qt.AlignHCenter)
        else:
            for offset, conflict in enumerate(used[5]):
                slotsLayout.addWidget(QtWidgets.QLabel(conflict[1]), 3 + offset, 0, 1, 1, QtCore.Qt.AlignHCenter)

        if len(used[7]) == 0:
            slotsLayout.addWidget(QtWidgets.QLabel("None"), 3, 1, 1, 1, QtCore.Qt.AlignHCenter)
        else:
            for offset, conflict in enumerate(used[7]):
                slotsLayout.addWidget(QtWidgets.QLabel(conflict[1]), 3 + offset, 1, 1, 1, QtCore.Qt.AlignHCenter)

        slotsLayout.addWidget(footer,       4 + rows, 0, 1, 3)
        slotsLayout.addWidget(createButton, 5 + rows, 0, 1, 3, QtCore.Qt.AlignHCenter)

        # Proposing the best option
        # Maybe change this to set the option that is already applied?
        if len(used[5]) <= len(used[7]):
            self.radio1.setChecked(True)
        else:
            self.radio2.setChecked(True)

        # create layout
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(QtWidgets.QLabel(text))

        if len(self.present) > 0:
            mainLayout.addWidget(QtWidgets.QLabel(text3))
            mainLayout.addWidget(QtWidgets.QLabel(str(self.present)))

        mainLayout.addLayout(slotsLayout)
        mainLayout.addWidget(buttonBox, 0, QtCore.Qt.AlignBottom)

        self.setLayout(mainLayout)

    def getNyb5And7Availability(self):
        """
        Gets whether nybble 5 or 7 or both or none is free.
        """
        nyb5 = (17, 21) # excludes end
        nyb7 = (25, 29)

        found = {5: [], 7: []}
        for field in self.sprite.fields:

            type = field[0]
            if type == 3: # multibox
                start = field[2]
                num = field[3]
                bit = (start, start + num)
            elif type in (5, 7): # (multi)dualbox
                bit = field[3]
            else:
                bit = field[2]

            if not isinstance(bit, tuple):
                bit = ((bit, bit + 1),)
            elif not isinstance(bit[0], tuple):
                bit = (bit,)

            # if two ranges (a..b, c..d) overlap, that means that a..b is not
            # completely before c..d (that is, b >= c) nor
            #    a <= i < b AND c <= i < d
            # since a < b and c < d,
            #    a < d AND c < b
            overlap = lambda a, b: a[0] < b[1] and b[0] < a[1]

            for ran in bit:
                if overlap(ran, nyb5):
                    found[5].append(field)

                if overlap(ran, nyb7):
                    found[7].append(field)

        return found

    def getSpecialEventAvailability(self):
        """
        Find Special Event [246] and then check if it has resize set.
        Returns a list of (slot, sprite) pairs, where slot = 2 means it is a global
        resize.
        """
        slots = []
        for sprite in globals_.Area.sprites:
            if sprite.type != 246:
                continue

            type = sprite.spritedata[5] & 0xF

            if type == 5:
                # Resizer
                slots.append((2, sprite))
            elif type == 6:
                # Selective resizer
                slot = (sprite.spritedata[5] >> 4) & 1
                slots.append((slot, sprite))

        return slots

    def doAThing(self):
        """
        Either places a new special event or changes the old one.
        """
        slot = self.buttongroup.checkedId()

        thing = []
        for type, sprite in self.present:
            if slot == -1 and type == 2:
                thing.append(sprite)

            elif not (slot == -1 or type == 2):
                thing.append(sprite)

        if len(thing) == 0:
            self.placeSpecialResizeEvent()
        elif len(thing) == 1:
            self.editSpecialResizeEvent(thing[0][1])
        else:
            # TODO: figure out what to do here
            ...

        return self.accept()

    def editSpecialResizeEvent(self, sprite):
        data = list(sprite.spritedata)

        slot = self.buttongroup.checkedId()
        if slot == -1:
            # global
            data[5] = (data[5] & 0xF0) | 5
        else:
            # only slot
            data[5] = (slot << 4) | 6

        sprite.spritedata = bytes(data)

    def placeSpecialResizeEvent(self):
        """
        Places a Special Event [246] and sets the settings so the correct slot.
        """
        # global globals_.mainWindow, globals_.Area

        slot = self.buttongroup.checkedId()
        data = bytearray(8)
        if slot == -1:
            data[5] = 5
        else:
            data[5] = (slot << 4) | 6

        x = globals_.mainWindow.selObj.objx + 16
        y = globals_.mainWindow.selObj.objy

        sprite = SpriteItem(246, x, y, data)
        sprite.positionChanged = globals_.mainWindow.HandleSprPosChange

        globals_.mainWindow.scene.addItem(sprite)
        globals_.Area.sprites.append(sprite)

        sprite.listitem = ListWidgetItem_SortsByOther(sprite)
        globals_.mainWindow.spriteList.addItem(sprite.listitem)

        SetDirty()
        sprite.UpdateListItem()

