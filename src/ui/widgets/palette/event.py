from PyQt6 import QtWidgets, QtCore
Qt = QtCore.Qt

from data import globals_
from data.level.dirty import SetDirty

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
        isOn = (globals_.Area.default_events & 1 << selIdx) == 1 << selIdx
        if item.checkState(0) == Qt.CheckState.Checked and not isOn:
            # Turn a bit on
            globals_.Area.default_events |= 1 << selIdx
            SetDirty()
        elif item.checkState(0) == Qt.CheckState.Unchecked and isOn:
            # Turn a bit off (mask out 1 bit)
            globals_.Area.default_events &= ~(1 << selIdx)
            SetDirty()

    def edit_event_note(self):
        """
        Handles the notes text changing
        """
        new_text = self.note_editor.text()

        # Set the text to the event chooser
        current_item = self.event_tree.selectedItems()[0]
        current_item.setText(1, new_text)

        self.save_event_notes()
        SetDirty()

    def load_event_data(self):
        """
        Configures the Events tab from the default events
        """
        default_events = globals_.Area.default_events
        checked = Qt.CheckState.Checked
        unchecked = Qt.CheckState.Unchecked

        data = None
        event_notes = {}

        data = globals_.Area.metadata.get_meta_data('event_notes')
        if data is not None:
            # The keys are strings when loaded from the JSON
            # so we need to convert them back into ints
            for k, v in data.items():
                event_notes[int(k)] = v
        else:
            data = globals_.Area.legacy_metadata.binData('EventNotes_A%d' % globals_.Area.areanum)
            if data is not None:
                # Iterate through the data
                idx = 0

                while idx < len(data):
                    event_id, str_len = struct.unpack_from(">2I", data, idx)
                    event_notes[event_id] = data[idx + 8:idx + 8 + str_len].decode('utf-8')

                    idx += 8 + str_len

        for i, item in enumerate(self.event_tree_items):
            item.setCheckState(0, checked if (default_events & (1 << i)) != 0 else unchecked)
            item.setText(1, event_notes.get(i, ""))
            item.setSelected(False)

        self.event_tree_items[0].setSelected(True)
        self.note_editor.setText(event_notes.get(0, ""))

    def save_event_notes(self) -> None:
        """
        Save event notes back to the metadata
        """
        event_notes = {}

        for idx in range(64):
            note = str(self.event_tree_items[idx].text(1))
            if note != '':
                event_notes[idx] = note

        globals_.Area.metadata.set_meta_data('event_notes', event_notes)
