import os
from typing import Literal
from xml.etree import ElementTree

from PyQt6 import QtCore, QtWidgets

from data import globals_
from data.sprite.external_note import ExternalNote
from ui.dialogs.spriteeditor.external_note import ExternalNotesDialog
from ui.widgets.spriteeditor.external_push_button import ExternalPushButtonWidget
from ui.theme.reggie_theme import GetIcon

class ExternalDatabaseDialog(QtWidgets.QDialog):
    """
    Dialog for external sprite databases
    """

    def __init__(self, name: str, value: int) -> None:
        """
        Initialise the dialog
        """
        super().__init__()

        self.name = name
        self.value = value
        self.search_results = set()

        # Set initial window info (title may be overridden later)
        self.setWindowTitle(globals_.trans.string('ExternalDatabaseDlg', 0))
        self.setWindowIcon(GetIcon('database'))
        #self.setMinimumSize(752, 648)

        self.read_xml_database()

        # Setup the search bar
        search_bar = QtWidgets.QLineEdit()
        search_bar.textEdited.connect(self.search)

        search_layout = QtWidgets.QHBoxLayout()
        search_layout.addWidget(QtWidgets.QLabel(globals_.trans.string('ExternalDatabaseDlg', 1)))
        search_layout.addWidget(search_bar)

        # Setup the table
        self.setup_table()

        # Find the current item and select it
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is None:
                break

            if value == item.data(QtCore.Qt.ItemDataRole.UserRole):
                self.table.setCurrentItem(item)
                self.table.scrollToItem(item)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.table)
        main_layout.addWidget(button_box, 0, QtCore.Qt.AlignmentFlag.AlignBottom)
        self.setLayout(main_layout)

    def read_xml_database(self) -> None:
        """
        Reads the XML and stores all of the item data
        """
        # Find the correct XML
        filename = globals_.gamedef.externalFile(f'{self.name}.xml')
        if not os.path.isfile(filename):
            raise FileNotFoundError

        id_header = str(globals_.trans.string('ExternalDatabaseDlg', 2))
        self.headers: list[str] = [id_header]
        self.entries: dict[int, dict[int, str]] = {}
        self.notes: list[ExternalNote] = []

        tree = ElementTree.parse(filename)
        root = tree.getroot()

        # Get the window title
        if 'title' in root.attrib:
            self.setWindowTitle(root.attrib['title'])

        # Parse nodes
        for node in root:
            # Column header name
            if node.tag.lower() == 'header':
                self.headers.append(node.attrib['name'])
                continue

            # Database entries
            elif node.tag.lower() != 'entry':
                continue

            entry_id = int(node.attrib['id'])
            entry: dict[int, str] = {}

            # Read each child column
            for prop in node:
                if prop.tag.lower() != 'column':
                    continue

                column_id = int(prop.attrib['id'])
                data = ''
                
                # This can optionally be excluded for note fields
                if 'text' in prop.attrib:
                    data = prop.attrib['text']

                # Check if there's text here (indicates an external notes box)
                if prop.text is not None:
                    note = ExternalNote(entry_id, column_id, prop.text)
                    self.notes.append(note)

                entry[column_id] = data

            # Now add the data as an entry
            self.entries[entry_id] = entry

    def get_note(self, entry_id: int, column_id: int) -> ExternalNote | None:
        """
        Returns an ExternalNote with the provided IDs, or None if no match is found
        """
        for note in self.notes:
            if note.entry_id == entry_id and note.column_id == column_id:
                return note

        return None

    def setup_table(self) -> None:
        """
        Prepares the table and its data
        """
        self.table = QtWidgets.QTableWidget(len(self.entries), len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)

        vert_header = self.table.verticalHeader()
        horiz_header = self.table.horizontalHeader()
        if vert_header is None or horiz_header is None:
            return

        # Hide vertical headers
        vert_header.setVisible(False)

        # Only select one item at a time, and select the entire row
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)

        self.table.itemClicked.connect(self.item_select)
        self.table.itemDoubleClicked.connect(self.item_select_confirm)

        # Now fill in all of the table data
        curr_row = 0
        for entry_id, entry in self.entries.items():
            # Fill in the default ID column
            item = QtWidgets.QTableWidgetItem(str(entry_id))
            item.setData(QtCore.Qt.ItemDataRole.UserRole, entry_id)
            item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(curr_row, 0, item)

            # Now add the rest of the data
            for column, text in entry.items():
                item = QtWidgets.QTableWidgetItem(text)
                item.setData(QtCore.Qt.ItemDataRole.UserRole, entry_id)
                item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)

                note = self.get_note(entry_id, column)
                if note is not None:
                    button = ExternalPushButtonWidget(globals_.trans.string('ExternalDatabaseDlg', 3), None, note)
                    button.clicked.connect(lambda: self.note_button_clicked(button))
                    self.table.setCellWidget(curr_row, column + 1, button)
                else:
                    self.table.setItem(curr_row, column + 1, item)

            curr_row += 1

        # Resize the dialog to (somewhat) fit the table
        # Sadly there isn't a good way to do this, it'll end up being too small sometimes...
        size = QtCore.QSize(horiz_header.length(), vert_header.length())
        size += QtCore.QSize(vert_header.size().width(), horiz_header.size().height())
        self.resize(size.width(), self.height())

    def get_value(self) -> int:
        """
        Returns the current value
        """
        return self.value

    def search(self, text: str) -> None:
        """
        Search through the table
        """
        if text == "":
            # Optimisation for when no search is given -> show everything
            for row in range(self.table.rowCount()):
                self.table.setRowHidden(row, False)

            self.search_results = set(range(self.table.rowCount()))
            return

        results = self.table.findItems(text, QtCore.Qt.MatchFlag.MatchContains | QtCore.Qt.MatchFlag.MatchRecursive)
        rows = {item.row() for item in results if item is not None}

        for row in range(self.table.rowCount()):
            self.table.setRowHidden(row, row not in rows)

        self.search_results = rows

    def item_select(self, item: QtWidgets.QTableWidgetItem) -> None:
        """
        Selects the current item
        """
        self.value = item.data(QtCore.Qt.ItemDataRole.UserRole)

    def item_select_confirm(self, item: QtWidgets.QTableWidgetItem) -> None:
        """
        Selects the current item and closes the dialog
        """
        self.value = item.data(QtCore.Qt.ItemDataRole.UserRole)
        self.accept()

    def note_button_clicked(self, button: ExternalPushButtonWidget) -> None:
        """
        Handles the notes button being clicked
        """
        dlg = ExternalNotesDialog(button.note.text)
        dlg.exec()
