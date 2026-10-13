import os

from PyQt6 import QtWidgets

from data import globals_
from data.common.utils import get_root_path


class ChangelogDialog(QtWidgets.QDialog):
    """
    Displays the CHANGELOG file
    """

    def __init__(self) -> None:
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(globals_.trans.string('ChangelogDlg', 0))
        self.setMinimumSize(625, 555)

        # Open the changelog
        changelog = ''
        try:
            with open(os.path.join(get_root_path(), 'CHANGELOG.md'), 'r', encoding='utf-8') as f:
                changelog = f.read()
        except FileNotFoundError:
            changelog = globals_.trans.string('ChangelogDlg', 1)

        changelog_view = QtWidgets.QTextBrowser()
        changelog_view.setMarkdown(changelog)
        changelog_view.setReadOnly(True)
        changelog_view.setOpenExternalLinks(True)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Close)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(changelog_view)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)
