import os
from xml.etree import ElementTree

from PyQt5 import QtWidgets, QtCore, QtGui

import globals_
from levelitems import SpriteItem, ListWidgetItem_SortsByOther
from ui import GetIcon
from dirty import SetDirty
import common

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
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred))

        # create the raw editor
        font = QtGui.QFont()
        font.setPointSize(8)
        self.editbox = QtWidgets.QLabel(globals_.trans.string('SpriteDataEditor', 3))
        self.editbox.setFont(font)
        edit = QtWidgets.QLineEdit()
        edit.textEdited.connect(self.HandleRawDataEdited)

        min_valid_width = QtGui.QFontMetrics(QtGui.QFont()).horizontalAdvance("dddd dddd dddd dddd")
        edit.setMinimumWidth(min_valid_width + 2 * 11)  # add padding
        edit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed))
        self.raweditor = edit

        self.resetButton = QtWidgets.QPushButton(globals_.trans.string('SpriteDataEditor', 17))
        self.resetButton.clicked.connect(self.HandleResetData)

        editboxlayout = QtWidgets.QHBoxLayout()
        editboxlayout.addWidget(self.resetButton)
        editboxlayout.addWidget(self.editbox)
        editboxlayout.addWidget(edit, QtCore.Qt.AlignRight)

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
        self.data = bytes(8)
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

        bit = None  # list: ranges
        required = None  # tuple (range, value)
        layout = None  # QLayout
        row = None  # int: row in the parent's layout
        comment = None  # str: comment text
        comment2 = None  # str: additional comment text
        commentAdv = None  # str: even more comment text
        parent = None  # SpriteEditorWidget: the widget this belongs to
        idtype = None  # str: the idtype of this property

        def retrieve(self, data, bits=None):
            """
            Extracts the value from the specified bit(s). Bit numbering is ltr BE
            and starts at 1.
            """
            if bits is None:
                bits = self.bit

            value = 0

            for ran in bits:
                bit_len = ran[1] - ran[0]

                if bit_len == 7 and ran[0] & 7 == 1:
                    # optimise if it's just one byte
                    value = (value << bit_len) | data[ran[0] >> 3]
                    continue

                # we have to calculate it
                for n in range(ran[0] - 1, ran[1] - 1):
                    value <<= 1
                    value |= (data[n >> 3] >> (7 - (n & 7))) & 1

            return value

        def insertvalue(self, data, value, bits=None):
            """
            Assigns a value to the specified bit(s)
            """
            if bits is None:
                bits = self.bit

            sdata = list(data)

            for ran in reversed(bits):
                # find the size of the range
                l = ran[1] - ran[0]

                # Extract the bits that need to be set in this iteration.
                value, v = value >> l, value & ((1 << l) - 1)

                # just one byte, this is easier
                if l == 7 and ran[0] & 7 == 1:
                    sdata[ran[0] >> 3] = v & 0xFF
                    continue

                # set the value bit by bit
                for n in reversed(range(ran[0], ran[1])):
                    off = 1 << (7 - ((n - 1) & 7))

                    if v & 1 != 0:  # set the bit
                        sdata[(n - 1) >> 3] |= off
                    else:  # mask the bit out
                        sdata[(n - 1) >> 3] &= 0xFF ^ off

                    v >>= 1

            return bytes(sdata)

        def checkReq(self, data, first=False):
            """
            Checks the requirements
            """
            if self.required is None:
                return

            show = True
            for pos, ran in self.required:
                show = show and ran[0] <= self.retrieve(data, pos) < ran[1]

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

        def ShowComment(self):
            """
            Sets the comment text
            """
            self.parent.com_main.setText(self.comment)
            self.parent.com_main.setVisible(True)
            self.parent.com_more.setVisible(False)
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

        def __init__(self, title, bit, mask, comment, required, _, comment2, commentAdv, layout, row, parent):
            """
            Creates the widget
            """
            if not isinstance(bit, list):
                raise ValueError("bit should be a list. " + repr(bit))

            super().__init__()

            self.widget = QtWidgets.QCheckBox()
            self.widget.clicked.connect(self.HandleClick)

            self.bit = bit
            self.required = required
            self.comment = comment
            self.comment2 = comment2
            self.commentAdv = commentAdv
            self.parent = parent
            self.row = row
            self.layout = layout

            self.mask = mask

            label = QtWidgets.QLabel(title + ':')
            # label.setWordWrap(True)

            layout.addWidget(label, row, 0, QtCore.Qt.AlignRight)
            layout.addWidget(self.widget, row, 1)

            col = 3
            if comment is not None:
                button_com = QtWidgets.QToolButton()
                button_com.setIcon(GetIcon('setting-comment'))
                button_com.setStyleSheet("border-radius: 50%")
                button_com.clicked.connect(self.ShowComment)
                button_com.setAutoRaise(True)

                layout.addWidget(button_com, row, col)
                col += 1

            if comment2 is not None:
                button_com2 = QtWidgets.QToolButton()
                button_com2.setIcon(GetIcon('setting-comment2'))
                button_com2.setStyleSheet("border-radius: 50%")
                button_com2.clicked.connect(self.ShowComment2)
                button_com2.setAutoRaise(True)

                layout.addWidget(button_com2, row, col)
                col += 1

            if commentAdv is not None:
                button_adv = QtWidgets.QToolButton()
                button_adv.setIcon(GetIcon('setting-comment-adv'))
                button_adv.setStyleSheet("border-radius: 50%")
                button_adv.clicked.connect(self.ShowAdvancedComment)
                button_adv.setAutoRaise(True)

                layout.addWidget(button_adv, row, col)

        def update(self, data, first=False):
            """
            Updates the value shown by the widget
            """
            # check if requirements are met
            self.checkReq(data, first)

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

        def __init__(self, title, bit, model, comment, required, _, comment2, commentAdv, idtype, layout, row, parent):
            """
            Creates the widget
            """
            super().__init__()

            self.parent = parent
            self.bit = bit
            self.required = required
            self.row = row
            self.layout = layout
            self.comment = comment
            self.comment2 = comment2
            self.commentAdv = commentAdv
            self.idtype = idtype
            self.prev_value = 0

            self.widget = QtWidgets.QComboBox()
            self.widget.setModel(model)
            self.widget.currentIndexChanged.connect(self.HandleIndexChanged)

            self.model = model

            label = QtWidgets.QLabel(title + ':')
            # label.setWordWrap(True)

            layout.addWidget(label, row, 0, QtCore.Qt.AlignRight)

            if idtype is not None:
                next_free_button = QtWidgets.QPushButton("Next Free")
                next_free_button.clicked.connect(self.handle_next_free)

                layout.addWidget(self.widget, row, 1)
                layout.addWidget(next_free_button, row, 2)
            else:
                layout.addWidget(self.widget, row, 1, 1, 2)

            col = 3
            if comment is not None:
                button_com = QtWidgets.QToolButton()
                button_com.setIcon(GetIcon('setting-comment'))
                button_com.setStyleSheet("border-radius: 50%")
                button_com.clicked.connect(self.ShowComment)
                button_com.setAutoRaise(True)

                layout.addWidget(button_com, row, col)
                col += 1

            if comment2 is not None:
                button_com2 = QtWidgets.QToolButton()
                button_com2.setIcon(GetIcon('setting-comment2'))
                button_com2.setStyleSheet("border-radius: 50%")
                button_com2.clicked.connect(self.ShowComment2)
                button_com2.setAutoRaise(True)

                layout.addWidget(button_com2, row, col)
                col += 1

            if commentAdv is not None:
                button_adv = QtWidgets.QToolButton()
                button_adv.setIcon(GetIcon('setting-comment-adv'))
                button_adv.setStyleSheet("border-radius: 50%")
                button_adv.clicked.connect(self.ShowAdvancedComment)
                button_adv.setAutoRaise(True)

                layout.addWidget(button_adv, row, col)

        def update(self, data, first=False):
            """
            Updates the value shown by the widget
            """
            # check if requirements are met
            self.checkReq(data, first)

            value = self.retrieve(data)

            for i, x in enumerate(self.model.entries):
                if x[0] == value:
                    self.widget.setCurrentIndex(i)
                    break
            else:
                self.widget.setCurrentIndex(-1)

            if first:
                self.prev_value = value

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

            value = self.model.entries[index][0]
            old_value = self.prev_value
            self.prev_value = value

            # No idtype is set, the widget is updating because of an automatic
            # change in spritedata or this is the default data editor.
            if self.idtype is None or self.parent.AutoFlag or self.parent.DefaultMode:
                return

            # Increment the count of the new value
            used_ids = globals_.Area.sprite_idtypes[self.idtype]
            used_ids[value] = used_ids.get(value, 0) + 1

            # Decrement (and remove if 0) the count of the old value
            if used_ids[old_value] == 1:
                del used_ids[old_value]
            else:
                used_ids[old_value] -= 1

        def handle_next_free(self):
            """
            Sets the value to the next free id of the id type of this property.
            """
            if self.idtype is None: return

            used_ids = globals_.Area.sprite_idtypes[self.idtype]
            current_value = self.model.entries[self.widget.currentIndex()][0]
            values = [value for value, text in self.model.entries]

            for next_id, value in enumerate(values):
                if value > current_value and value not in used_ids:
                    break
            else:
                return

            self.widget.setCurrentIndex(next_id)

    class ValuePropertyDecoder(PropertyDecoder):
        """
        Class that decodes/encodes sprite data to/from a spinbox
        """

        def __init__(self, title, bit, max_, comment, required, _, comment2, commentAdv, idtype, layout, row, parent):
            """
            Creates the widget
            """
            super().__init__()

            self.widget = QtWidgets.QSpinBox()
            self.widget.setRange(0, max_ - 1)
            self.widget.valueChanged.connect(self.HandleValueChanged)

            self.bit = bit
            self.required = required
            self.parent = parent
            self.comment = comment
            self.comment2 = comment2
            self.commentAdv = commentAdv
            self.idtype = idtype
            self.layout = layout
            self.row = row
            self.prev_value = None

            label = QtWidgets.QLabel(title + ':')
            # label.setWordWrap(True)

            layout.addWidget(label, row, 0, QtCore.Qt.AlignRight)

            if idtype is not None:
                next_free_button = QtWidgets.QPushButton("Next Free")
                next_free_button.clicked.connect(self.handle_next_free)

                layout.addWidget(self.widget, row, 1)
                layout.addWidget(next_free_button, row, 2)
            else:
                layout.addWidget(self.widget, row, 1, 1, 2)

            col = 3
            if comment is not None:
                button_com = QtWidgets.QToolButton()
                button_com.setIcon(GetIcon('setting-comment'))
                button_com.setStyleSheet("border-radius: 50%")
                button_com.clicked.connect(self.ShowComment)
                button_com.setAutoRaise(True)

                layout.addWidget(button_com, row, col)
                col += 1

            if comment2 is not None:
                button_com2 = QtWidgets.QToolButton()
                button_com2.setIcon(GetIcon('setting-comment2'))
                button_com2.setStyleSheet("border-radius: 50%")
                button_com2.clicked.connect(self.ShowComment2)
                button_com2.setAutoRaise(True)

                layout.addWidget(button_com2, row, col)
                col += 1

            if commentAdv is not None:
                button_adv = QtWidgets.QToolButton()
                button_adv.setIcon(GetIcon('setting-comment-adv'))
                button_adv.setStyleSheet("border-radius: 50%")
                button_adv.clicked.connect(self.ShowAdvancedComment)
                button_adv.setAutoRaise(True)

                layout.addWidget(button_adv, row, col)

        def update(self, data, first=False):
            """
            Updates the value shown by the widget
            """
            # check if requirements are met
            self.checkReq(data, first)

            value = self.retrieve(data)
            self.widget.setValue(value)

            if first:
                self.prev_value = value

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

            old_value = self.prev_value
            self.prev_value = value

            # No idtype is set, the widget is updating because of an automatic
            # change in spritedata or this is the default data editor.
            if self.idtype is None or self.parent.AutoFlag or self.parent.DefaultMode:
                return

            # Increment the count of the new value
            used_ids = globals_.Area.sprite_idtypes[self.idtype]
            used_ids[value] = used_ids.get(value, 0) + 1

            # Decrement (and remove if 0) the count of the old value
            if used_ids[old_value] == 1:
                del used_ids[old_value]
            else:
                used_ids[old_value] -= 1

        def handle_next_free(self):
            """
            Sets the value to the next free id of the id type of this property.
            """
            if self.idtype is None: return

            used_ids = globals_.Area.sprite_idtypes[self.idtype]
            next_id = common.find_first_available_id(used_ids, self.widget.maximum(), self.widget.value() + 1)

            self.widget.setValue(next_id)

    # UNUSED
    class BitfieldPropertyDecoder(PropertyDecoder):
        """
        Class that decodes/encodes sprite data to/from a bitfield
        """

        def __init__(self, title, startbit, bitnum, comment, required, _, comment2, commentAdv, layout, row, parent):
            """
            Creates the widget
            """
            super().__init__()

            self.bit = [(startbit, startbit + bitnum)]
            self.required = required
            self.parent = parent
            self.comment = comment
            self.comment2 = comment2
            self.commentAdv = commentAdv
            self.layout = layout
            self.row = row

            self.bitnum = bitnum
            self.widgets = []

            CheckboxLayout = QtWidgets.QGridLayout()
            # CheckboxLayout.setContentsMargins(0, 0, 0, 0)

            for i in range(bitnum):
                c = QtWidgets.QCheckBox()
                c.toggled.connect(self.HandleValueChanged)
                self.widgets.append(c)

                CheckboxLayout.addWidget(c, 0, i)
                CheckboxLayout.addWidget(QtWidgets.QLabel(str(i + 1)), 1, i, QtCore.Qt.AlignHCenter)

            label = QtWidgets.QLabel(title + ':')
            # label.setWordWrap(True)

            checkbox_widget = QtWidgets.QWidget()
            checkbox_widget.setLayout(CheckboxLayout)

            layout.addWidget(label, row, 0, QtCore.Qt.AlignRight)
            layout.addWidget(checkbox_widget, row, 1, 1, 2)

            col = 3
            if comment is not None:
                button_com = QtWidgets.QToolButton()
                button_com.setIcon(GetIcon('setting-comment'))
                button_com.setStyleSheet("border-radius: 50%")
                button_com.clicked.connect(self.ShowComment)
                button_com.setAutoRaise(True)

                layout.addWidget(button_com, row, col)
                col += 1

            if comment2 is not None:
                button_com2 = QtWidgets.QToolButton()
                button_com2.setIcon(GetIcon('setting-comment2'))
                button_com2.setStyleSheet("border-radius: 50%")
                button_com2.clicked.connect(self.ShowComment2)
                button_com2.setAutoRaise(True)

                layout.addWidget(button_com2, row, col)
                col += 1

            if commentAdv is not None:
                button_adv = QtWidgets.QToolButton()
                button_adv.setIcon(GetIcon('setting-comment-adv'))
                button_adv.setStyleSheet("border-radius: 50%")
                button_adv.clicked.connect(self.ShowAdvancedComment)
                button_adv.setAutoRaise(True)

                layout.addWidget(button_adv, row, col)

        def update(self, data, first=False):
            """
            Updates the value shown by the widget
            """
            # check if requirements are met
            self.checkReq(data, first)

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

    # UNUSED
    class MultiboxPropertyDecoder(PropertyDecoder):
        """
        Class that decodes/encodes sprite data to/from a multibox
        """

        def __init__(self, title, bit, comment, required, advanced, comment2, commentAdv, layout, row, parent):
            """
            Creates the widget
            """
            super().__init__()

            bitnum = bit[1] - bit[0]
            startbit = bit[0]

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

                button_com.setIcon(GetIcon('setting-comment'))
                button_com.setStyleSheet("border-radius: 50%")

                button_com.clicked.connect(self.ShowComment)
                button_com.setAutoRaise(True)

            else:
                button_com = None

            if comment2 is not None:
                button_com2 = QtWidgets.QToolButton()
                button_com2.setIcon(GetIcon('setting-comment2'))
                button_com2.setStyleSheet("border-radius: 50%")
                button_com2.clicked.connect(self.ShowComment2)
                button_com2.setAutoRaise(True)

            else:
                button_com2 = None

            if commentAdv is not None:
                button_adv = QtWidgets.QToolButton()

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
            layout.addWidget(w, row, 1, 1, 2)

            self.layout = layout
            self.row = row

        def update(self, data, first=False):
            """
            Updates the value shown by the widget
            """
            # check if requirements are met
            self.checkReq(data, first)

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

        def __init__(self, title1, title2, bit, comment, required, _, comment2, commentAdv, layout, row, parent):
            """
            Creates the widget
            """
            super().__init__()

            self.bit = bit
            self.required = required
            self.parent = parent
            self.comment = comment
            self.comment2 = comment2
            self.commentAdv = commentAdv
            self.row = row
            self.layout = layout

            self.buttons = [QtWidgets.QRadioButton(), QtWidgets.QRadioButton()]

            for button in self.buttons:
                button.clicked.connect(self.HandleClick)

            label1 = QtWidgets.QLabel(title1)
            # label1.setWordWrap(True)

            label2 = QtWidgets.QLabel(title2)
            # label2.setWordWrap(True)

            L = QtWidgets.QHBoxLayout()
            L.addStretch(1)
            L.addWidget(label1)
            L.addWidget(self.buttons[0])
            L.addWidget(QtWidgets.QLabel("|"))
            L.addWidget(self.buttons[1])
            L.addWidget(label2)
            L.addStretch(1)
            L.setContentsMargins(0, 0, 0, 0)

            widget = QtWidgets.QWidget()
            widget.setLayout(L)

            # span three columns
            layout.addWidget(widget, row, 0, 1, 3)

            col = 3
            if comment is not None:
                button_com = QtWidgets.QToolButton()
                button_com.setIcon(GetIcon('setting-comment'))
                button_com.setStyleSheet("border-radius: 50%")
                button_com.clicked.connect(self.ShowComment)
                button_com.setAutoRaise(True)

                layout.addWidget(button_com, row, col)
                col += 1

            if comment2 is not None:
                button_com2 = QtWidgets.QToolButton()
                button_com2.setIcon(GetIcon('setting-comment2'))
                button_com2.setStyleSheet("border-radius: 50%")
                button_com2.clicked.connect(self.ShowComment2)
                button_com2.setAutoRaise(True)

                layout.addWidget(button_com2, row, col)
                col += 1

            if commentAdv is not None:
                button_adv = QtWidgets.QToolButton()
                button_adv.setIcon(GetIcon('setting-comment-adv'))
                button_adv.setStyleSheet("border-radius: 50%")
                button_adv.clicked.connect(self.ShowAdvancedComment)
                button_adv.setAutoRaise(True)

                layout.addWidget(button_adv, row, col)


        def update(self, data, first=False):
            """
            Updates the value shown by the widget
            """
            # check if requirements are met
            self.checkReq(data, first)

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

        def __init__(self, title, bit, comment, required, _, comment2, commentAdv, type_, layout, row, parent):
            """
            Creates the widget
            """
            super().__init__()

            assert len(bit) == 1

            self.bit = bit
            self.row = row
            self.layout = layout
            self.parent = parent
            self.comment = comment
            self.comment2 = comment2
            self.required = required
            self.commentAdv = commentAdv

            self.type = type_
            self.dispvalue = 0

            bits = bit[0][1] - bit[0][0]

            # button that contains the current value
            self.button = QtWidgets.QPushButton()
            self.button.clicked.connect(self.HandleClicked)

            # spinbox that contains the current value
            self.box = QtWidgets.QSpinBox()
            self.box.setRange(0, (2 ** bits) - 1)
            self.box.setValue(self.dispvalue)
            self.box.valueChanged.connect(self.HandleValueChanged)

            label = QtWidgets.QLabel(title + ":")
            # label.setWordWrap(True)

            layout.addWidget(label, row, 0, QtCore.Qt.AlignRight)
            layout.addWidget(self.button, row, 1)
            layout.addWidget(self.box, row, 2)

            col = 3
            if comment is not None:
                button_com = QtWidgets.QToolButton()
                button_com.setIcon(GetIcon('setting-comment'))
                button_com.setStyleSheet("border-radius: 50%")
                button_com.clicked.connect(self.ShowComment)
                button_com.setAutoRaise(True)

                layout.addWidget(button_com, row, col)
                col += 1

            if comment2 is not None:
                button_com2 = QtWidgets.QToolButton()
                button_com2.setIcon(GetIcon('setting-comment2'))
                button_com2.setStyleSheet("border-radius: 50%")
                button_com2.clicked.connect(self.ShowComment2)
                button_com2.setAutoRaise(True)

                layout.addWidget(button_com2, row, col)
                col += 1

            if commentAdv is not None:
                button_adv = QtWidgets.QToolButton()
                button_adv.setIcon(GetIcon('setting-comment-adv'))
                button_adv.setStyleSheet("border-radius: 50%")
                button_adv.clicked.connect(self.ShowAdvancedComment)
                button_adv.setAutoRaise(True)

                layout.addWidget(button_adv, row, col)

        def update(self, data, first=False):
            """
            Updates the info
            """
            # check if requirements are met
            self.checkReq(data, first)

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
            value = int(value)

            # find correct xml
            filename = globals_.gamedef.externalFile(self.type + '.xml')
            if not os.path.isfile(filename):
                raise ValueError("The external xml file cannot be found for type: " + self.type)

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
                if option_.tag.lower() == 'option' and int(option_.attrib['value'], 0) == value:
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

            assert len(bit) == 1

            self.bit = bit
            self.required = required
            self.advanced = advanced
            self.parent = parent
            self.layout = layout
            self.row = row
            self.comment = comment
            self.comment2 = comment2
            self.commentAdv = commentAdv
            self.bitnum = self.bit[0][1] - self.bit[0][0]
            self.startbit = self.bit[0][0]

            self.widgets = []
            DualboxLayout = QtWidgets.QGridLayout()
            DualboxLayout.setContentsMargins(0, 0, 0, 0)

            for i in range(self.bitnum):
                buttons = [QtWidgets.QRadioButton(), QtWidgets.QRadioButton()]
                buttons[0].clicked.connect(self.HandleClicked)
                buttons[0].setAutoExclusive(False)
                buttons[1].clicked.connect(self.HandleClicked)
                buttons[1].setAutoExclusive(False)

                buttons[0].setChecked(True)

                button_group = QtWidgets.QButtonGroup()
                button_group.addButton(buttons[0], 1)
                button_group.addButton(buttons[1], 2)

                self.widgets.append(button_group)

                DualboxLayout.addWidget(buttons[0], 0, i)
                DualboxLayout.addWidget(buttons[1], 1, i)

            label1 = QtWidgets.QLabel(title1)
            # label1.setWordWrap(True)
            label2 = QtWidgets.QLabel(title2)
            # label2.setWordWrap(True)

            labels = QtWidgets.QGridLayout()
            labels.addWidget(label1, 0, 0, QtCore.Qt.AlignRight)
            labels.addWidget(label2, 1, 0, QtCore.Qt.AlignRight)

            labels_widget = QtWidgets.QWidget()
            labels_widget.setLayout(labels)

            dualbox_widget = QtWidgets.QWidget()
            dualbox_widget.setLayout(DualboxLayout)

            layout.addWidget(labels_widget, row, 0, QtCore.Qt.AlignRight)
            layout.addWidget(dualbox_widget, row, 1, 1, 2)

            col = 3
            if comment is not None:
                button_com = QtWidgets.QToolButton()
                button_com.setIcon(GetIcon('setting-comment'))
                button_com.setStyleSheet("border-radius: 50%")
                button_com.clicked.connect(self.ShowComment)
                button_com.setAutoRaise(True)

                layout.addWidget(button_com, row, col)
                col += 1

            if comment2 is not None:
                button_com2 = QtWidgets.QToolButton()
                button_com2.setIcon(GetIcon('setting-comment2'))
                button_com2.setStyleSheet("border-radius: 50%")
                button_com2.clicked.connect(self.ShowComment2)
                button_com2.setAutoRaise(True)

                layout.addWidget(button_com2, row, col)
                col += 1

            if commentAdv is not None:
                button_adv = QtWidgets.QToolButton()
                button_adv.setIcon(GetIcon('setting-comment-adv'))
                button_adv.setStyleSheet("border-radius: 50%")
                button_adv.clicked.connect(self.ShowAdvancedComment)
                button_adv.setAutoRaise(True)

                layout.addWidget(button_adv, row, col)

        def HandleClicked(self, _):
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

            value = self.retrieve(data)

            # run at most self.bitnum times
            for i in range(self.bitnum - 1, -1, -1):
                self.widgets[i].button(2).setChecked(value & 1)
                value >>= 1

        def assign(self, data):
            """
            Assigns the checkbox states to the data
            """
            value = 0

            # construct bitmask
            for i in range(self.bitnum):
                value = (value << 1) | (self.widgets[i].checkedId() - 1)

            return self.insertvalue(data, value)


    def setSprite(self, type_, reset=False, initial_data=None):
        """
        Change the sprite type used by the data editor
        """
        if self.spritetype == type_ and not reset:
            if initial_data is not None:
                self.data = initial_data
                self.update(True)

            return

        self.spritetype = type_
        if type_ != 1000 and 0 <= type_ < globals_.NumSprites:
            sprite = globals_.Sprites[type_]
        else:
            sprite = None

        # remove all the existing widgets in the layout
        self.clearMessages()

        def _clear_layout(layout):
            while True:
                item = layout.takeAt(0)

                if item is None:
                    break

                if item.widget() is not None:
                    x = item.widget()
                    layout.removeItem(item)
                    layout.removeWidget(x)
                    x.setParent(None)
                elif item.layout() is not None:
                    x = item.layout()
                    _clear_layout(x)
                    layout.removeItem(x)
                    layout.removeItem(item)
                    x.setParent(None)
                else:
                    x = item.spacerItem()
                    layout.removeItem(x)

                del x, item

        layout = self.editorlayout
        _clear_layout(layout)

        # show the raw editor
        self.raweditor.setVisible(True)
        self.editbox.setVisible(True)
        self.resetButton.setVisible(not globals_.HideResetSpritedata and (sprite is None or bool(sprite.fields)))

        # show size stuff
        self.sizeButton.setVisible(sprite is not None and sprite.size)

        # Nothing is selected, so no comments should appear
        self.com_box.setVisible(False)

        if sprite is None:
            self.spriteLabel.setText(globals_.trans.string('SpriteDataEditor', 5, '[id]', type_))
            self.noteButton.setVisible(False)
            self.yoshiInfo.setVisible(False)
            self.advNoteButton.setVisible(False)
            self.asm.setVisible(False)
            self.fields = []

            return

        self.spriteLabel.setText(globals_.trans.string('SpriteDataEditor', 6, '[id]', type_, '[name]', sprite.name))

        if sprite.notes is not None:
            self.noteButton.setVisible(True)
            self.com_main.setText(sprite.notes)
            self.com_main.setVisible(True)
            self.com_more.setVisible(False)
            self.com_extra.setVisible(False)
            self.com_box.setVisible(True)

        self.notes = sprite.notes

        # advanced comment
        self.advNoteButton.setVisible(sprite.advNotes is not None)
        self.advNotes = sprite.advNotes

        self.relatedObjFilesButton.setVisible(sprite.relatedObjFiles is not None)
        self.relatedObjFiles = sprite.relatedObjFiles

        self.asm.setVisible(sprite.asm is True)

        # dependency stuff
        # first clear current dependencies
        _clear_layout(self.com_deplist)

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
                nf = SpriteEditorWidget.ListPropertyDecoder(f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8], f[9], layout, row, self)

            elif f[0] == 2:
                nf = SpriteEditorWidget.ValuePropertyDecoder(f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8], f[9], layout, row, self)

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

        if initial_data is not None:
            self.data = initial_data

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

        for row in range(l.count() - 1, -1, -1):
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
        data = self.data

        self.raweditor.setText('%02x%02x %02x%02x %02x%02x %02x%02x' % (
            data[0], data[1], data[2], data[3],
            data[4], data[5], data[6], data[7],
        ))

        self.raweditor.setStyleSheet('')

        self.UpdateFlag = True
        self.AutoFlag = True

        # Go through all the data
        for f in self.fields:
            f.update(data, first)

        self.AutoFlag = False
        self.UpdateFlag = False

        # minimise height
        if globals_.mainWindow.spriteEditorDock.isFloating():
            self.window().resize(self.width(), 0)

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
            self.com_dep.setText(globals_.trans.string('SpriteDataEditor', 18))
            self.com_main.setVisible(True)
            self.com_deplist_w.setVisible(False)

        else:
            self.com_dep.setText(globals_.trans.string('SpriteDataEditor', 19))
            self.com_main.setVisible(False)
            self.com_deplist_w.setVisible(True)

    def HandleFieldUpdate(self, field):
        """
        Triggered when a field's data is updated
        """
        if self.UpdateFlag: return

        data = field.assign(self.data)

        self.raweditor.setText('%02x%02x %02x%02x %02x%02x %02x%02x' % (
            data[0], data[1], data[2], data[3],
            data[4], data[5], data[6], data[7],
        ))
        self.raweditor.setStyleSheet('')

        self.UpdateData(data, exclude_update_field=field, do_update=False, was_automatic=False)

    def HandleResetData(self):
        """
        Handles the reset data button being clicked
        """
        self.UpdateData(bytes(8), was_automatic=False)

        self.raweditor.setText("0000 0000 0000 0000")
        self.raweditor.setStyleSheet('')

    def UpdateData(self, new_data, exclude_update_field = None, do_update = True, was_automatic = True):
        """
        Updates all fields (optionally excluding one field) with the new sprite
        data. If do_update is not set, the UpdateFlag is not changed. If was_automatic
        is set, a flag is set to indicate the change was caused by the user.
        """
        self.data = new_data

        if do_update:
            self.UpdateFlag = True

        if was_automatic:
            self.AutoFlag = True

        for f in self.fields:
            if f != exclude_update_field:
                f.update(new_data)

        if was_automatic:
            self.AutoFlag = True

        if do_update:
            self.UpdateFlag = False

        self.DataUpdate.emit(new_data)

    def HandleRawDataEdited(self, text):
        """
        Triggered when the raw data textbox is edited
        """

        raw = text.replace(' ', '')
        valid = False

        if len(raw) == 16:
            try:
                data = bytes.fromhex(text)
                valid = True

            except ValueError:
                pass

        if not valid:
            self.raweditor.setStyleSheet('QLineEdit { background-color: #ffd2d2; }')
            return

        # if it's valid, let it go
        self.raweditor.setStyleSheet('')
        self.UpdateData(data, was_automatic=False)

    def HandleSpritePlaced(self, id_, button_):
        def placeSprite():
            mw = globals_.mainWindow

            x_ = mw.selObj.objx + 16
            y_ = mw.selObj.objy
            globals_.mainWindow.CreateSprite(x_, y_, id_, data=bytes(8))

            # remove this dependency, because it is now fulfilled.
            # get row of button
            idx = self.com_deplist.indexOf(button_)
            row, *_ = self.com_deplist.getItemPosition(idx)

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

        if not secondary:
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

        if 0 <= spriteid < globals_.NumSprites:
            self.sprite = globals_.Sprites[spriteid]
        else:
            self.sprite = None

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

        if not self.present:
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

        if self.present:
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

        if self.sprite is None:
            return found

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

            if not isinstance(bit[0], tuple):
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

        if not thing:
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
        special_event_id = 246

        if globals_.mainWindow.CreateSprite(x, y, special_event_id, data) is not None:
            globals_.mainWindow.scene.update()
