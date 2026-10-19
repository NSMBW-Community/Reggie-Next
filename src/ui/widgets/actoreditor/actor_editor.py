from PyQt6 import QtCore, QtGui, QtWidgets

from data import globals_
from data.level.dirty import SetDirty
from data.level.items.actor import ActorItem
from data.level.actor_definition import ActorDefinition
from data.common.list_property import ListPropertyModel
from data.actor.actorfield.check_box import CheckBoxActorField
from data.actor.actorfield.dual_box import DualBoxActorField
from data.actor.actorfield.external import ExternalActorField
from data.actor.actorfield.list import ListActorField
from data.actor.actorfield.multi_dual_box import MultiDualBoxActorField
from data.actor.actorfield.sprite_tex import SpriteTexActorField
from data.actor.actorfield.value import ValueActorField
from ui.dialogs.actoreditor.resize_choice import ResizeChoiceDialog
from ui.widgets.actoreditor.abstract_actor_editor import (
    AbstractActorEditorWidget,
)
from ui.widgets.actoreditor.propertydecoders.check_box import (
    CheckBoxPropertyDecoder,
)
from ui.widgets.actoreditor.propertydecoders.dual_box import DualBoxPropertyDecoder
from ui.widgets.actoreditor.propertydecoders.external import (
    ExternalPropertyDecoder,
)
from ui.widgets.actoreditor.propertydecoders.list import ListPropertyDecoder
from ui.widgets.actoreditor.propertydecoders.multi_dual_box import (
    MultiDualboxPropertyDecoder,
)
from ui.widgets.actoreditor.propertydecoders.sprite_tex import (
    SpriteTexPropertyDecoder,
)
from ui.widgets.actoreditor.propertydecoders.value import ValuePropertyDecoder
from ui.theme.reggie_theme import GetIcon


class ActorEditorWidget(AbstractActorEditorWidget):
    """
    Widget for editing actor data
    """
    DataUpdate: QtCore.pyqtSignal = QtCore.pyqtSignal('PyQt_PyObject')

    def __init__(self, defaultmode=False):
        super().__init__(defaultmode)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred))

        # create the raw editor
        font = QtGui.QFont()
        font.setPointSize(8)
        self.editbox = QtWidgets.QLabel(globals_.trans.string('ActorDataEditor', 3))
        self.editbox.setFont(font)
        edit = QtWidgets.QLineEdit()
        edit.textEdited.connect(self.HandleRawDataEdited)

        min_valid_width = QtGui.QFontMetrics(QtGui.QFont()).horizontalAdvance("dddd dddd dddd dddd")
        edit.setMinimumWidth(min_valid_width + 2 * 11)  # add padding
        edit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Fixed))
        self.raweditor = edit

        self.resetButton = QtWidgets.QPushButton(globals_.trans.string('ActorDataEditor', 17))
        self.resetButton.clicked.connect(self.HandleResetData)

        editboxlayout = QtWidgets.QHBoxLayout()
        editboxlayout.addWidget(self.resetButton)
        editboxlayout.addWidget(self.editbox)
        editboxlayout.addWidget(edit, QtCore.Qt.AlignmentFlag.AlignRight)

        # 'Editing Actor #' label
        self.actorLabel = QtWidgets.QLabel('-')
        self.actorLabel.setWordWrap(True)

        self.noteButton = QtWidgets.QToolButton()
        self.noteButton.setIcon(GetIcon('sticky-note-text'))
        self.noteButton.setText(globals_.trans.string('ActorDataEditor', 4))
        self.noteButton.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.noteButton.setAutoRaise(True)
        self.noteButton.clicked.connect(self.ShowNoteTooltip)

        self.depButton = QtWidgets.QToolButton()
        self.depButton.setIcon(GetIcon('node-select-child'))
        self.depButton.setText(globals_.trans.string('ActorDataEditor', 4))
        self.depButton.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.depButton.setAutoRaise(True)
        self.depButton.clicked.connect(self.ShowDependencies)

        self.relatedObjFilesButton = QtWidgets.QToolButton()
        self.relatedObjFilesButton.setIcon(GetIcon('documents-stack'))
        self.relatedObjFilesButton.setText(globals_.trans.string('ActorDataEditor', 7))
        self.relatedObjFilesButton.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.relatedObjFilesButton.setAutoRaise(True)
        self.relatedObjFilesButton.clicked.connect(self.ShowRelatedObjFilesTooltip)

        self.advNoteButton = QtWidgets.QToolButton()
        self.advNoteButton.setIcon(GetIcon('sticky-note-text-advanced'))
        self.advNoteButton.setText(globals_.trans.string('ActorDataEditor', 10))
        self.advNoteButton.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.advNoteButton.setAutoRaise(True)
        self.advNoteButton.clicked.connect(self.ShowAdvancedNoteTooltip)

        self.yoshiIcon = QtWidgets.QLabel()

        self.yoshiInfo = QtWidgets.QToolButton()
        self.yoshiInfo.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.yoshiInfo.setText(globals_.trans.string('ActorDataEditor', 12))
        self.yoshiInfo.setAutoRaise(True)
        self.yoshiInfo.clicked.connect(self.ShowYoshiTooltip)

        self.asm = QtWidgets.QLabel()
        self.asm.setPixmap(GetIcon('processor').pixmap(64, 64))

        self.sizeButton = QtWidgets.QToolButton()
        self.sizeButton.setIcon(GetIcon('arrow-out'))
        self.sizeButton.setText(globals_.trans.string('ActorDataEditor', 27))
        self.sizeButton.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.sizeButton.setAutoRaise(True)
        self.sizeButton.clicked.connect(self.HandleSizeButtonClicked)

        toplayout = QtWidgets.QHBoxLayout()
        toplayout.addWidget(self.actorLabel)
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

        self.com_main.setReadOnly(True)
        self.com_more.setText(globals_.trans.string('ActorDataEditor', 13))
        self.com_more.clicked.connect(self.ShowMoreComments)
        self.com_dep.setText(globals_.trans.string('ActorDataEditor', 18))
        self.com_dep.clicked.connect(self.DependencyToggle)
        self.com_dep.setVisible(False)
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
        self.data = bytes(10)
        self.fields = []

        self.notes = None
        self.relatedObjFiles = None
        self.dependencyNotes = None

    def setActor(self, type_: int, reset=False, initial_data: bytes | None = None):
        """
        Change the actor type used by the data editor
        """
        if self.actortype == type_ and not reset:
            if initial_data is not None:
                self.data = initial_data
                self.updateFields(True)

            return

        self.actortype = type_
        actor: ActorDefinition | None = None
        if type_ != 1000 and 0 <= type_ < globals_.NumActors:
            actor = globals_.Actors[type_]

        # remove all the existing widgets in the layout
        self.clearMessages()

        def _clear_layout(layout: QtWidgets.QLayout | None):
            if layout is None:
                return

            while True:
                item = layout.takeAt(0)

                if item is None:
                    break

                if item.widget() is not None:
                    x = item.widget()
                    layout.removeItem(item)
                    layout.removeWidget(x)
                    if x is not None:
                        x.setParent(None)
                elif item.layout() is not None:
                    x = item.layout()
                    _clear_layout(x)
                    layout.removeItem(x)
                    layout.removeItem(item)
                    if x is not None:
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
        self.resetButton.setVisible(actor is None or bool(actor.fields) or not actor.noLayer)

        # show size stuff
        self.sizeButton.setVisible(actor is not None and actor.size and globals_.AllowSizeHacks)

        # Nothing is selected, so no comments should appear
        self.com_box.setVisible(False)

        if actor is None:
            self.actorLabel.setText(globals_.trans.string('ActorDataEditor', 5, '[id]', type_))
            self.noteButton.setVisible(False)
            self.yoshiInfo.setVisible(False)
            self.advNoteButton.setVisible(False)
            self.asm.setVisible(False)
            self.fields = []

            return

        self.actorLabel.setText(globals_.trans.string('ActorDataEditor', 6, '[id]', type_, '[name]', actor.name))

        self.noteButton.setVisible(actor.notes is not None)
        if actor.notes is not None:
            self.com_main.setText(actor.notes)
            self.com_main.setVisible(True)
            self.com_more.setVisible(False)
            self.com_extra.setVisible(False)
            self.com_box.setVisible(True)

        self.notes = actor.notes

        # advanced comment
        self.advNoteButton.setVisible(actor.advNotes is not None)
        self.advNotes = actor.advNotes

        # object files
        self.relatedObjFilesButton.setVisible(actor.relatedObjFiles is not None)
        if actor.relatedObjFiles is not None:
            self.relatedObjFiles = actor.relatedObjFiles

            if actor.notes is None:
                self.com_more.setVisible(False)
                self.com_extra.setVisible(False)
                self.ShowRelatedObjFilesTooltip()

        self.asm.setVisible(actor.asm is True)

        # dependency stuff
        # first clear current dependencies
        _clear_layout(self.com_deplist)

        rownum = 0

        # (actor id, importance level)
        # importance level is 0 for 'required', 1 for 'suggested', 2 for 'resource', 3 for 'suggestedresource'
        missing = [[], [], [], []]
        cur_actors = [s.actor_num for s in globals_.Area.actors]
        for dependency, importance in actor.dependencies:
            if dependency not in cur_actors:
                if importance == 2:
                    if dependency not in globals_.Area.force_loaded_actors:
                        missing[importance].append(dependency)
                else:
                    missing[importance].append(dependency)

        # if there are missing things
        # Required
        for missing_actor in missing[0]:
            name = globals_.trans.string('ActorDataEditor', 20, '[id]', missing_actor)
            action = globals_.trans.string('ActorDataEditor', 26)
            addButton = QtWidgets.QPushButton(action)

            message = self.addMessage(name, level = 0, close = action)
            callback = self.closeMessageCallback(message, self.HandleActorPlaced(missing_actor, addButton))
            self.addCallbackToMessage(message, callback)

            addButton.clicked.connect(callback)

            self.com_deplist.addWidget(QtWidgets.QLabel(name), rownum, 0)
            self.com_deplist.addWidget(addButton, rownum, 1)

            rownum += 1

        # Suggested
        for missing_actor in missing[1]:
            name = globals_.trans.string('ActorDataEditor', 21, '[id]', missing_actor)
            action = globals_.trans.string('ActorDataEditor', 26)

            addButton = QtWidgets.QPushButton(action)
            addButton.clicked.connect(self.HandleActorPlaced(missing_actor, addButton))

            self.com_deplist.addWidget(QtWidgets.QLabel(name), rownum, 0)
            self.com_deplist.addWidget(addButton, rownum, 1)
            rownum += 1

        # Resource
        for missing_actor in missing[2]:
            name = globals_.trans.string('ActorDataEditor', 30, '[id]', missing_actor)
            action = globals_.trans.string('ActorDataEditor', 31)
            addButton = QtWidgets.QPushButton(action)

            message = self.addMessage(name, level = 3, close = action)
            callback = self.closeMessageCallback(message, self.HandleAppendToLoadList(missing_actor, addButton))
            self.addCallbackToMessage(message, callback)

            addButton.clicked.connect(callback)

            self.com_deplist.addWidget(QtWidgets.QLabel(name), rownum, 0)
            self.com_deplist.addWidget(addButton, rownum, 1)

            rownum += 1

        # Suggested Resource
        for missing_actor in missing[3]:
            name = globals_.trans.string('ActorDataEditor', 30, '[id]', missing_actor)
            action = globals_.trans.string('ActorDataEditor', 31)

            addButton = QtWidgets.QPushButton(action)
            addButton.clicked.connect(self.HandleAppendToLoadList(missing_actor, addButton))

            self.com_deplist.addWidget(QtWidgets.QLabel(name), rownum, 0)
            self.com_deplist.addWidget(addButton, rownum, 1)
            rownum += 1

        # dependency notes
        self.depButton.setVisible(actor.dependencynotes is not None)
        self.com_deplist_w.setVisible(False)
        self.com_dep.setVisible(False)

        if actor.dependencynotes is not None:
            self.dependencyNotes = actor.dependencynotes

            if actor.notes is None:
                self.com_more.setVisible(False)
                self.com_extra.setVisible(False)
                self.ShowDependencies()

        # yoshi info
        if actor.noyoshi is True:
            image = 'yoshi-egg-cross'
        elif actor.noyoshi is not None:
            image = 'yoshi-egg'
        else:
            image = None

        if actor.yoshiNotes is not None:
            if image is None:
                image = 'yoshi-egg'

            self.yoshiIcon.setVisible(False)
            self.yoshiInfo.setIcon(GetIcon(image))
            self.yoshiInfo.setVisible(True)
            self.yoshiNotes = actor.yoshiNotes

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

        for field in actor.fields:
            nf = None
            if isinstance(field, CheckBoxActorField):
                nf = CheckBoxPropertyDecoder(field, layout, row, self)

            elif isinstance(field, ListActorField):
                nf = ListPropertyDecoder(field, layout, row, self)

            elif isinstance(field, ValueActorField):
                nf = ValuePropertyDecoder(field, layout, row, self)

            elif isinstance(field, DualBoxActorField):
                nf = DualBoxPropertyDecoder(field, layout, row, self)

            elif isinstance(field, ExternalActorField):
                nf = ExternalPropertyDecoder(field, layout, row, self)

            elif isinstance(field, MultiDualBoxActorField):
                nf = MultiDualboxPropertyDecoder(field, layout, row, self)

            elif isinstance(field, SpriteTexActorField):
                nf = SpriteTexPropertyDecoder(field, layout, row, self)

            if nf is None:
                continue

            nf.updateData.connect(self.HandleFieldUpdate)
            fields.append(nf)
            row += 1

        # Now create fields that exist across ALL actors
        if not actor.noLayer:
            # Add a small bit of spacing
            spacer = QtWidgets.QSpacerItem(0, 8, QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
            layout.addItem(spacer, row, 0)
            row += 1

            if hasattr(actor, 'layer_title'):
                title = actor.layer_title
            else:
                title = globals_.trans.string('ActorDataEditor', 32)

            if hasattr(actor, 'layer_comment'):
                comment = actor.layer_comment
            else:
                comment = globals_.trans.string('ActorDataEditor', 33)
            strList = globals_.trans.stringList('ActorDataEditor', 34)
            if strList is None:
                return
            itemList = [(0, strList[0]), (1, strList[1]), (2, strList[2])]

            # Layer reads entire byte, instead of the first two bits
            bit, _ = ActorDefinition().parseBits('15-16')
            model = ListPropertyModel(itemList, True)

            listField = ListActorField(title, comment, None, None, None, bit, model, None)

            nf = ListPropertyDecoder(listField, layout, row, self)
            nf.updateData.connect(self.HandleFieldUpdate)
            fields.append(nf)
            row += 1

        self.fields = fields

        if initial_data is not None:
            self.data = initial_data

        self.updateFields(True)

    def addMessage(self, text, action = None, level = 0, close: str | None = "x"):
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
        label.setStyleSheet(f"""
            QLabel {{
                color: {colours[2]};
            }}
        """)

        closeButton = QtWidgets.QPushButton(close)
        closeButton.setStyleSheet("""
            QPushButton {{
                background: {};
                color: {};
            }}
        """.format(*colours[:2]))

        L = QtWidgets.QHBoxLayout()
        L.addWidget(label)
        L.addStretch(1)
        L.addWidget(closeButton)

        message = QtWidgets.QWidget()
        message.setStyleSheet("""
            .QWidget {{
                background: {};
                border: 2px solid {};
                border-radius: 3px;
            }}
        """.format(*colours[3:]))
        message.setLayout(L)

        closeButton.clicked.connect(self.closeMessageCallback(message, action))

        self.msg_layout.addWidget(message)

        return message

    def clearMessages(self):
        """
        Clears all messages
        """
        l = self.msg_layout

        for row in range(l.count() - 1, -1, -1):
            w = l.itemAt(row)
            if w is None:
                continue
            widget = w.widget()
            if widget is None:
                continue
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

    def updateFields(self, first=False):
        """
        Updates all the fields to display the appropriate info
        """
        data = self.data

        # data[6] is the actor's zone ID. Modifying it is unnecessary since Reggie sets it automatically,
        # and overwrites whatever you change it to. If anything, it seems to just confuse everybody who
        # sees it, so we're just going to hide the value from the user
        self.raweditor.setText(f'{data[0]:02x}{data[1]:02x} {data[2]:02x}{data[3]:02x} {data[4]:02x}{data[5]:02x} {0x00:02x}{data[7]:02x} {data[8]:02x}{data[9]:02x}')

        self.raweditor.setStyleSheet('')

        self.UpdateFlag = True
        self.AutoFlag = True

        # Go through all the data
        for f in self.fields:
            f.update(data, first)

        self.AutoFlag = False
        self.UpdateFlag = False

        # minimise height
        if globals_.mainWindow is not None and globals_.mainWindow.actorEditorDock.isFloating():
            window = self.window()
            if window is not None:
                window.resize(self.width(), 0)

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
            self.com_more.setText(globals_.trans.string('ActorDataEditor', 13))
            self.com_main.setVisible(True)

        else:
            self.com_extra.setVisible(True)
            self.com_more.setText(globals_.trans.string('ActorDataEditor', 14))
            self.com_main.setVisible(False)

    def ShowDependencies(self):
        """
        Show dependencies
        """
        self.com_main.setText(self.dependencyNotes)
        self.com_main.setVisible(True)
        self.com_extra.setVisible(False)
        self.com_deplist_w.setVisible(False)
        self.com_dep.setText(globals_.trans.string('ActorDataEditor', 18))
        self.com_dep.setVisible(self.com_deplist.count() > 0)
        self.com_box.setVisible(True)

    def DependencyToggle(self):
        """
        The button was clicked
        """
        if not self.com_main.isVisible():
            self.com_dep.setText(globals_.trans.string('ActorDataEditor', 18))
            self.com_main.setVisible(True)
            self.com_deplist_w.setVisible(False)

        else:
            self.com_dep.setText(globals_.trans.string('ActorDataEditor', 19))
            self.com_main.setVisible(False)
            self.com_deplist_w.setVisible(True)

    def HandleFieldUpdate(self, field):
        """
        Triggered when a field's data is updated
        """
        if self.UpdateFlag: return

        data = field.assign(self.data)

        # data[6] is the actor's zone ID. Modifying it is unnecessary since Reggie sets it automatically,
        # and overwrites whatever you change it to. If anything, it seems to just confuse everybody who
        # sees it, so we're just going to hide the value from the user
        self.raweditor.setText(f'{data[0]:02x}{data[1]:02x} {data[2]:02x}{data[3]:02x} {data[4]:02x}{data[5]:02x} {0x00:02x}{data[7]:02x} {data[8]:02x}{data[9]:02x}')
        self.raweditor.setStyleSheet('')

        self.UpdateData(data, exclude_update_field=field, do_update=False, was_automatic=False)

    def HandleResetData(self):
        """
        Handles the reset data button being clicked
        """
        self.UpdateData(bytes(10), was_automatic=False)

        self.raweditor.setText("0000 0000 0000 0000 0000")
        self.raweditor.setStyleSheet('')

    def UpdateData(self, new_data, exclude_update_field = None, do_update = True, was_automatic = True):
        """
        Updates all fields (optionally excluding one field) with the new actor
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

        # Fix window not shrinking after fields are hidden
        if globals_.mainWindow is not None and globals_.mainWindow.actorEditorDock.isFloating():
            window = self.window()
            if window is not None:
                window.resize(self.width(), 0)

    def HandleRawDataEdited(self, text):
        """
        Triggered when the raw data textbox is edited
        """

        raw = text.replace(' ', '')
        valid = False
        data = b""

        if len(raw) == 20:
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

    def HandleActorPlaced(self, id_, button_):
        def placeActor():
            mw = globals_.mainWindow
            if mw is None or mw.selObj is None or not isinstance(mw.selObj, ActorItem):
                return

            x_ = mw.selObj.objx + 16 if mw.selObj.objx is not None else 16
            y_ = mw.selObj.objy if mw.selObj.objy is not None else 0
            SpriteItem.CreateSprite(x_, y_, id_, data=bytes(10))

            # remove this dependency, because it is now fulfilled.
            # get row of button
            idx = self.com_deplist.indexOf(button_)
            row, *_ = self.com_deplist.getItemPosition(idx)
            if row is None:
                return

            # remove this row
            l = self.com_deplist
            for column in range(l.columnCount()):
                w = l.itemAtPosition(row, column)
                if w is not None:
                    widget = w.widget()
                    if widget is not None:
                        l.removeWidget(widget)
                        widget.setParent(None)


        return placeActor

    def HandleAppendToLoadList(self, id_, button_):
        def addToLoadList():
            globals_.Area.force_loaded_actors.add(id_)
            SetDirty()

            # remove this dependency, because it is now fulfilled.
            # get row of button
            idx = self.com_deplist.indexOf(button_)
            row, *_ = self.com_deplist.getItemPosition(idx)
            if row is None:
                return

            # remove this row
            l = self.com_deplist
            for column in range(l.columnCount()):
                w = l.itemAtPosition(row, column)
                if w is not None:
                    widget = w.widget()
                    if widget is not None:
                        l.removeWidget(widget)
                        widget.setParent(None)


        return addToLoadList

    def HandleSizeButtonClicked(self, e):
        """
        Handles the 'resize' button being clicked
        """
        # In the event that the user somehow is able to click this when SizeHacks are disabled,
        # show a generic message saying the feature is unavailable.
        if not globals_.AllowSizeHacks:
            QtWidgets.QMessageBox.warning(None, globals_.trans.string('ResizeChoiceDlg', 11), globals_.trans.string('ResizeChoiceDlg', 12))
            return

        dlg = ResizeChoiceDialog(self.actortype)

        # only contine if the user pressed "OK"
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
