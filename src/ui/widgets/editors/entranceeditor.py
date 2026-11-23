from collections.abc import Callable
from typing import cast

from PyQt6 import QtCore, QtGui, QtWidgets

from data import globals_
from data.common.list_property import ListPropertyModel
from data.common.translation import Translation
from data.level.dirty import SetDirty
from data.level.items.sprite import SpriteItem
from data.level.items.entrance import EntranceItem
from data.level.sprite_definition import SpriteDefinition
from data.sprite.spritefield.check_box import CheckBoxSpriteField
from data.sprite.spritefield.dual_box import DualBoxSpriteField
from data.sprite.spritefield.external import ExternalSpriteField
from data.sprite.spritefield.list import ListSpriteField
from data.sprite.spritefield.multi_dual_box import MultiDualBoxSpriteField
from data.sprite.spritefield.value_list import ValueListSpriteField
from data.sprite.spritefield.value import ValueSpriteField
from ui.dialogs.spriteeditor.resize_choice import ResizeChoiceDialog
from ui.theme.reggie_theme import GetIcon
from ui.widgets.item_editor_dock import ItemEditorDockWidget
from ui.widgets.spriteeditor.abstract_sprite_editor import (
    AbstractSpriteEditorWidget,
)
from ui.widgets.spriteeditor.propertydecoders.check_box import (
    CheckBoxPropertyDecoder,
)
from ui.widgets.spriteeditor.propertydecoders.dual_box import DualBoxPropertyDecoder
from ui.widgets.spriteeditor.propertydecoders.external import (
    ExternalPropertyDecoder,
)
from ui.widgets.spriteeditor.propertydecoders.list import ListPropertyDecoder
from ui.widgets.spriteeditor.propertydecoders.multi_dual_box import (
    MultiDualboxPropertyDecoder,
)
from ui.widgets.spriteeditor.propertydecoders.property_decoder import (
    PropertyDecoder,
)
from ui.widgets.spriteeditor.propertydecoders.value_list import (
    ValueListPropertyDecoder,
)
from ui.widgets.spriteeditor.propertydecoders.value import ValuePropertyDecoder


class EntranceEditorWidget(AbstractSpriteEditorWidget):
    """
    Widget for editing sprite data
    """
    data_update: QtCore.pyqtSignal = QtCore.pyqtSignal('PyQt_PyObject')

    def __init__(self, defaultmode: bool = False) -> None:
        super().__init__(defaultmode)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred))
        self.data_update.connect(self.data_updated)

        # Create the raw editor
        font = QtGui.QFont()
        font.setPointSize(8)
        self.editbox = QtWidgets.QLabel(globals_.trans.string('dialog.sprite_data_editor.modify_raw_data'))
        self.editbox.setFont(font)
        edit = QtWidgets.QLineEdit()
        edit.textEdited.connect(self.HandleRawDataEdited)

        min_valid_width = QtGui.QFontMetrics(QtGui.QFont()).horizontalAdvance("dddd dddd dddd dddd dddd dddd dddd dddd dddd")
        edit.setMinimumWidth(min_valid_width + 2 * 11)
        edit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Fixed))
        self.raweditor = edit

        self.reset_button = QtWidgets.QPushButton(globals_.trans.string('dialog.sprite_data_editor.reset_all'))
        self.reset_button.clicked.connect(self.HandleResetData)

        raw_data_layout = QtWidgets.QHBoxLayout()
        raw_data_layout.addWidget(self.reset_button)
        raw_data_layout.addWidget(self.editbox)
        raw_data_layout.addWidget(edit, QtCore.Qt.AlignmentFlag.AlignRight)

        self.title_label = QtWidgets.QLabel('-')
        self.title_label.setWordWrap(True)

        toplayout = QtWidgets.QHBoxLayout()
        toplayout.addWidget(self.title_label)
        toplayout.addStretch(1)

        subLayout = QtWidgets.QVBoxLayout()
        subLayout.setContentsMargins(0, 0, 0, 0)

        self.com_main.setReadOnly(True)

        self.com_deplist = QtWidgets.QGridLayout()

        self.com_deplist_w = QtWidgets.QWidget()
        self.com_deplist_w.setVisible(False)
        self.com_deplist_w.setLayout(self.com_deplist)

        L = QtWidgets.QVBoxLayout()
        L.addWidget(self.com_main)
        self.com_box.setLayout(L)

        # Create a layout
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(toplayout)
        mainLayout.addLayout(subLayout)

        layout = QtWidgets.QGridLayout()
        self.editorlayout = layout

        subLayout.addLayout(layout)
        subLayout.addWidget(self.com_box)
        subLayout.addLayout(raw_data_layout)

        self.setLayout(mainLayout)

        self.entrance_type = -1
        self.data = bytes(16)
        self.fields = []

        self.notes = None
        self.relatedObjFiles = None
        self.dependencyNotes = None

    def set_entrance(self, ent: EntranceItem, reset: bool = False) -> None:
        """
        Change the sprite type used by the data editor
        """
        _type = ent.ent_type
        if self.entrance_type == _type and not reset:
            return

        self.entrance_type = _type
        entrance: SpriteDefinition | None = None
        if 0 <= _type < globals_.NumEntrances:
            
            entrance = globals_.Entrances[_type]

        # Remove all the existing widgets in the layout
        def _clear_layout(layout: QtWidgets.QLayout | None) -> None:
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
        self.reset_button.setVisible(entrance is None or bool(entrance.fields) or not entrance.noLayer)

        # Nothing is selected, so no comments should appear
        self.com_box.setVisible(False)

        if entrance is None:
            self.title_label.setText(globals_.trans.string('dialog.entrance_data_editor.unknown_info', ('[id]', _type)))
            self.fields = []
            return

        self.title_label.setText(globals_.trans.string('dialog.entrance_data_editor.info', ('[id]', _type), ('[name]', entrance.name)))
        if entrance.notes is not None:
            self.com_main.setText(entrance.notes)
            self.com_main.setVisible(True)
            self.com_box.setVisible(True)

        self.notes = entrance.notes

        # Create fields
        fields = []
        row = 0

        for field in entrance.fields:
            nf = None
            if isinstance(field, CheckBoxSpriteField):
                nf = CheckBoxPropertyDecoder(field, layout, row, self)

            elif isinstance(field, ListSpriteField):
                nf = ListPropertyDecoder(field, layout, row, self)

            elif isinstance(field, ValueSpriteField):
                nf = ValuePropertyDecoder(field, layout, row, self)

            elif isinstance(field, DualBoxSpriteField):
                nf = DualBoxPropertyDecoder(field, layout, row, self)

            elif isinstance(field, ExternalSpriteField):
                nf = ExternalPropertyDecoder(field, layout, row, self)

            elif isinstance(field, MultiDualBoxSpriteField):
                nf = MultiDualboxPropertyDecoder(field, layout, row, self)

            elif isinstance(field, ValueListSpriteField):
                nf = ValueListPropertyDecoder(field, layout, row, self)

            if nf is None:
                continue

            nf.updateData.connect(self.HandleFieldUpdate)
            fields.append(nf)
            row += 1

        # Now create fields that exist across ALL sprites
        if not entrance.noLayer:
            # Add a small bit of spacing
            spacer = QtWidgets.QSpacerItem(0, 8, QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
            layout.addItem(spacer, row, 0)
            row += 1

            if hasattr(entrance, 'layer_title'):
                title = entrance.layer_title
            else:
                title = globals_.trans.string('dialog.sprite_data_editor.property_decoder.layer_default.label')

            if hasattr(entrance, 'layer_comment'):
                comment = entrance.layer_comment
            else:
                comment = globals_.trans.string('dialog.sprite_data_editor.property_decoder.layer_default.comment')

            str_list = globals_.trans.string_list('common.layer1', 'common.layer2', 'common.layer0')
            if str_list is None:
                return

            item_list = [(0, str_list[0]), (1, str_list[1]), (2, str_list[2])]

            # Layer reads entire byte
            bit, _ = SpriteDefinition(129).parseBits('21-22')
            model = ListPropertyModel(item_list, True)

            listField = ListSpriteField(title, comment, None, None, None, bit, model, None)

            nf = ListPropertyDecoder(listField, layout, row, self)
            nf.updateData.connect(self.HandleFieldUpdate)
            fields.append(nf)
            row += 1

        self.fields = fields

        self.updateFields(True)

    def update_raw_data(self, reset: bool = False) -> None:
        """
        Updates the raw data
        """
        data = self.data

        texts: list[str] = []
        for i in range(0, len(data), 2):
            texts.append(f'{data[i]:02x}{data[i + 1]:02x}' if not reset else '0000')

        self.raweditor.setText(' '.join(texts))
        self.raweditor.setStyleSheet('')

    def updateFields(self, first: bool = False) -> None:
        """
        Updates all the fields to display the appropriate info
        """
        data = self.data
        self.update_raw_data()

        self.UpdateFlag = True
        self.AutoFlag = True

        # Go through all the data
        for f in self.fields:
            f.update(data, first)

        self.AutoFlag = False
        self.UpdateFlag = False

        # Minimise height
        if globals_.mainWindow.spriteEditorDock.isFloating():
            window = self.window()
            if window is not None:
                window.resize(self.width(), 0)

    def HandleFieldUpdate(self, field: PropertyDecoder) -> None:
        """
        Triggered when a field's data is updated
        """
        if self.UpdateFlag:
            return

        data = field.assign(self.data)
        self.update_raw_data()

        self.UpdateData(data, exclude_update_field=field, do_update=False, was_automatic=False)

    def HandleResetData(self) -> None:
        """
        Handles the reset data button being clicked
        """
        self.UpdateData(bytes(10), was_automatic=False)
        self.update_raw_data(True)

    def UpdateData(self, new_data: bytes, exclude_update_field: PropertyDecoder | None = None, do_update: bool = True, was_automatic: bool = True) -> None:
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

        self.data_update.emit(new_data)

        # Fix window not shrinking after fields are hidden
        if globals_.mainWindow.spriteEditorDock.isFloating():
            window = self.window()
            if window is not None:
                window.resize(self.width(), 0)

    def HandleRawDataEdited(self, text: str) -> None:
        """
        Triggered when the raw data textbox is edited
        """
        raw = text.replace(' ', '')
        valid = False
        data = b""

        if len(raw) == 32:
            try:
                data = bytes.fromhex(text)
                valid = True
            except ValueError:
                pass

        if not valid:
            self.raweditor.setStyleSheet('QLineEdit { background-color: #ffd2d2; }')
            return

        # If it's valid, let it go
        self.raweditor.setStyleSheet('')
        self.UpdateData(data, was_automatic=False)

    def data_updated(self, data: bytes) -> None:
        """
        Handle the current sprite's data being updated
        """
        dock = cast(ItemEditorDockWidget, self.parent())
        if dock.is_active():
            for obj in globals_.mainWindow.scene.selectedItems():
                if isinstance(obj, SpriteItem):
                    obj.spritedata = data
                    obj.UpdateListItem()
                    SetDirty()

                    obj.UpdateDynamicSizing()
                    globals_.mainWindow.palette_dock.sprite_tab.sprite_list.updateSprite(obj)
