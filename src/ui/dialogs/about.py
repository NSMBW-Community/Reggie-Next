import os

from PyQt6 import QtGui, QtWidgets

from data import globals_
from data.common.utils import get_reggiedata_folder, get_root_path
from ui.dialogs.changelog import ChangelogDialog


class AboutDialog(QtWidgets.QDialog):
    """
    Displays the README and some other info
    """

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(globals_.trans.string('AboutDlg', 0))

        # Open the readme file
        readme = ''
        try:
            with open(os.path.join(get_root_path(), 'README.md'), 'r', encoding='utf-8') as f:
                readme = f.read()
        except FileNotFoundError:
            readme = globals_.trans.string('AboutDlg', 4)

        logo = QtGui.QPixmap(os.path.join(get_reggiedata_folder(), 'icon.png'))
        logo_label = QtWidgets.QLabel()
        logo_label.setPixmap(logo)
        logo_label.setContentsMargins(16, 4, 32, 4)

        link = 'https://horizon.miraheze.org/wiki/Discord_Servers'

        header = globals_.trans.string('AboutDlg', 1)
        info = globals_.trans.string('AboutDlg', 2)
        contact = globals_.trans.string('AboutDlg', 3, '[link]', link)

        description = (
            '<html><head><style type="text/CSS">'
            'body {font-family: Calibri}'
            '.main {font-size: 12px}'
            '</style></head><body>'
            '<center><h1>'
            f'{header}'
            '</h1><div class="main">'
            f'{info}'
            f'{contact}'
            '</div></center></body></html>'
        )

        about_label = QtWidgets.QLabel()
        about_label.setText(description)
        about_label.setMinimumWidth(512)
        about_label.setOpenExternalLinks(True)
        about_label.setWordWrap(True)

        # README.md viewer
        readme_view = QtWidgets.QPlainTextEdit()
        readme_view.setPlainText(readme)
        readme_view.setReadOnly(True)

        changelog_button = QtWidgets.QPushButton(globals_.trans.string('AboutDlg', 5))
        changelog_button.pressed.connect(lambda: ChangelogDialog().exec())

        close_button = QtWidgets.QPushButton(globals_.trans.string('AboutDlg', 6))

        button_box = QtWidgets.QDialogButtonBox()
        button_box.addButton(changelog_button, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
        button_box.addButton(close_button, QtWidgets.QDialogButtonBox.ButtonRole.RejectRole)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout = QtWidgets.QGridLayout()
        main_layout.addWidget(logo_label, 0, 0, 2, 1)
        main_layout.addWidget(about_label, 0, 1)
        main_layout.addWidget(readme_view, 1, 1)
        main_layout.addWidget(button_box, 2, 0, 1, 2)
        main_layout.setRowStretch(1, 1)
        main_layout.setColumnStretch(1, 1)
        self.setLayout(main_layout)
