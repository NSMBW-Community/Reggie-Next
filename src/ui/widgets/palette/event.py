from PyQt6 import QtWidgets, QtCore
Qt = QtCore.Qt

from src.data import globals_
from src.data.level.dirty import SetDirty

import struct

class EventTab(QtWidgets.QWidget):
    """
    Represents the Events tab in the palette
    """
    def __init__(self):
        super().__init__(None)
        label = QtWidgets.QLabel(globals_.trans.string('Palette', 20))
        note_field_label = QtWidgets.QLabel(globals_.trans.string('Palette', 21))

        self.note_editor = QtWidgets.QLineEdit()
        self.note_editor.textEdited.connect(self.edit_event_note)

        self.event_tree = QtWidgets.QTreeWidget()
        self.event_tree.setColumnCount(2)
        self.event_tree.setHeaderLabels((globals_.trans.string('Palette', 22), globals_.trans.string('Palette', 23)))
        self.event_tree.itemClicked.connect(self.event_selected)
        self.event_tree_items: list[QtWidgets.QTreeWidgetItem] = []

        flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
        for id in range(64):
            itm = QtWidgets.QTreeWidgetItem()
            itm.setFlags(flags)
            itm.setCheckState(0, Qt.CheckState.Unchecked)
            itm.setText(0, globals_.trans.string('Palette', 24, '[id]', str(id + 1)))
            itm.setText(1, '')

            self.event_tree.addTopLevelItem(itm)
            self.event_tree_items.append(itm)
            if id == 0:
                itm.setSelected(True)

        main_layout = QtWidgets.QGridLayout(self)
        main_layout.addWidget(label, 0, 0, 1, 2)
        main_layout.addWidget(note_field_label, 1, 0)
        main_layout.addWidget(self.note_editor, 1, 1)
        main_layout.addWidget(self.event_tree, 2, 0, 1, 2)

    def event_selected(self, item: QtWidgets.QTreeWidgetItem):
        """
        Handles an item being clicked in the Events tab
        """
        # Write the current note to the event note editor
        noteText = item.text(1)
        self.note_editor.setText(noteText)

        selIdx = self.event_tree_items.index(item)
        isOn = (globals_.Area.defEvents & 1 << selIdx) == 1 << selIdx
        if item.checkState(0) == Qt.CheckState.Checked and not isOn:
            # Turn a bit on
            globals_.Area.defEvents |= 1 << selIdx
            SetDirty()
        elif item.checkState(0) == Qt.CheckState.Unchecked and isOn:
            # Turn a bit off (mask out 1 bit)
            globals_.Area.defEvents &= ~(1 << selIdx)
            SetDirty()

    def edit_event_note(self):
        """
        Handles the notes text changing
        """
        new_text = self.note_editor.text()

        # Set the text to the event chooser
        currentItem = self.event_tree.selectedItems()[0]
        currentItem.setText(1, new_text)

        # Save all the events to the metadata
        data = b""
        for i in range(64):
            event_note = str(self.event_tree_items[i].text(1))
            if not event_note:
                continue

            encoded = event_note.encode('utf-8')

            # Add the event ID, note length and note to the data.
            data += struct.pack(">2I", i, len(encoded))
            data += encoded

        globals_.Area.Metadata.setBinData('EventNotes_A%d' % globals_.Area.areanum, data)
        SetDirty()

    def load_event_data(self):
        """
        Configures the Events tab from the data in globals_.Area.defEvents
        """
        defEvents = globals_.Area.defEvents
        checked = Qt.CheckState.Checked
        unchecked = Qt.CheckState.Unchecked

        data = globals_.Area.Metadata.binData('EventNotes_A%d' % globals_.Area.areanum)
        eventTexts = {}
        if data is not None:
            # Iterate through the data
            idx = 0

            while idx < len(data):
                event_id, str_len = struct.unpack_from(">2I", data, idx)
                eventTexts[event_id] = data[idx + 8:idx + 8 + str_len].decode('utf-8')

                idx += 8 + str_len

        for i, item in enumerate(self.event_tree_items):
            item.setCheckState(0, checked if (defEvents & (1 << i)) != 0 else unchecked)
            item.setText(1, eventTexts.get(i, ""))
            item.setSelected(False)

        self.event_tree_items[0].setSelected(True)
        self.note_editor.setText(eventTexts.get(0, ""))
