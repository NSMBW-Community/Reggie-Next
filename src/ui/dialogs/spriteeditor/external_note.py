import os
from PyQt6 import QtWidgets
from data import globals_

class ExternalNotesDialog(QtWidgets.QDialog):
    """
    Displays External Database notes
    """

    def __init__(self, text: str) -> None:
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(globals_.trans.string('ExternalDatabaseDlg', 4))

        # Do some automatic replacements
        replace = {
            '[br]': '<br>',
            '[b]': '<b>',
            '[/b]': '</b>',
            '[i]': '<i>',
            '[/i]': '</i>',
            '[a': '<a',
            '"]': '">',  # Workaround
            '[/a]': '</a>',
            '\\n': '\n',
            '//n': '\n',
            '[tm]': '™',
            '[small]': '<small>',
            '[/small]': '</small>',
        }
        for old, value in replace.items():
            text = text.replace(old, value)

        text_view = QtWidgets.QTextEdit()
        text_view.setText(text)
        text_view.setReadOnly(True)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Close)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(text_view)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)
