from PyQt6 import QtWidgets, QtCore

import globals_
from dirty import SetDirty
from ui import GetIcon, createHorzLine

class ChangePasswordDialog(QtWidgets.QDialog):
    """
    Dialog to set a password for the meta-info
    """
    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle(globals_.trans.string('InfoDlg', 9))
        self.setWindowIcon(GetIcon('info'))

        self.new_pass = QtWidgets.QLineEdit()
        self.new_pass.setMaxLength(64)
        self.new_pass.textChanged.connect(self.check_password_match)
        self.new_pass.setMinimumWidth(320)

        self.verify_pass = QtWidgets.QLineEdit()
        self.verify_pass.setMaxLength(64)
        self.verify_pass.textChanged.connect(self.check_password_match)
        self.verify_pass.setMinimumWidth(320)

        self.ok_button = QtWidgets.QPushButton('OK')
        self.cancel_button = QtWidgets.QDialogButtonBox.StandardButton.Cancel

        button_box = QtWidgets.QDialogButtonBox()
        button_box.addButton(self.ok_button, button_box.ButtonRole.AcceptRole)
        button_box.addButton(self.cancel_button)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.ok_button.setDisabled(True)

        info_layout = QtWidgets.QFormLayout()
        info_layout.addRow(globals_.trans.string('InfoDlg', 10), self.new_pass)
        info_layout.addRow(globals_.trans.string('InfoDlg', 11), self.verify_pass)

        info_box = QtWidgets.QGroupBox(globals_.trans.string('InfoDlg', 12))

        info_label = QtWidgets.QVBoxLayout()
        info_label.addWidget(QtWidgets.QLabel(globals_.trans.string('InfoDlg', 13)), 0, QtCore.Qt.AlignmentFlag.AlignCenter)
        info_label.addLayout(info_layout)
        info_box.setLayout(info_label)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(info_box)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)

    def check_password_match(self):
        """
        Enables the OK button if the password matches
        """
        self.ok_button.setDisabled(self.new_pass.text() != self.verify_pass.text() and self.new_pass.text() != '')


class MetaInfoDialog(QtWidgets.QDialog):
    """
    Dialog to set level metadata
    """

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(globals_.trans.string('InfoDlg', 0))
        self.setWindowIcon(GetIcon('info'))

        title = globals_.Area.Metadata.strData('Title')
        author = globals_.Area.Metadata.strData('Author')
        group = globals_.Area.Metadata.strData('Group')
        website = globals_.Area.Metadata.strData('Website')
        creator = globals_.Area.Metadata.strData('Creator')
        password = globals_.Area.Metadata.strData('Password')

        # Set defaults
        if title is None:
            title = '-'
        if author is None:
            author = '-'
        if group is None:
            group = '-'
        if website is None:
            website = '-'
        if creator is None:
            creator = globals_.trans.string('InfoDlg', 15)
        if password is None:
            password = ''

        self.name_field = QtWidgets.QLineEdit()
        self.name_field.setMaxLength(128)
        self.name_field.setMinimumWidth(320)
        self.name_field.setText(title)

        self.author_field = QtWidgets.QLineEdit()
        self.author_field.setMaxLength(128)
        self.author_field.setMinimumWidth(320)
        self.author_field.setText(author)

        self.group_field = QtWidgets.QLineEdit()
        self.group_field.setMaxLength(128)
        self.group_field.setMinimumWidth(320)
        self.group_field.setText(group)

        self.website_field = QtWidgets.QLineEdit()
        self.website_field.setMaxLength(128)
        self.website_field.setMinimumWidth(320)
        self.website_field.setText(website)

        self.password_field = QtWidgets.QLineEdit()
        self.password_field.setMaxLength(128)
        self.password_field.textChanged.connect(self.update_password)
        self.password_field.setMinimumWidth(320)

        self.edit_password_button = QtWidgets.QPushButton(globals_.trans.string('InfoDlg', 1))

        if password != '':
            self.name_field.setReadOnly(False)
            self.author_field.setReadOnly(False)
            self.group_field.setReadOnly(False)
            self.website_field.setReadOnly(False)
            self.edit_password_button.setDisabled(False)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        button_box.addButton(self.edit_password_button, button_box.ButtonRole.ActionRole)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        self.edit_password_button.clicked.connect(self.change_password)
        self.edit_password_button.setDisabled(True)

        self.locked_label = QtWidgets.QLabel(globals_.trans.string('InfoDlg', 2))
        self.line = createHorzLine()

        infoLayout = QtWidgets.QFormLayout()
        infoLayout.addWidget(self.locked_label)
        infoLayout.addRow(globals_.trans.string('InfoDlg', 3), self.password_field)
        infoLayout.addRow(self.line)
        infoLayout.addRow(globals_.trans.string('InfoDlg', 4), self.name_field)
        infoLayout.addRow(globals_.trans.string('InfoDlg', 5), self.author_field)
        infoLayout.addRow(globals_.trans.string('InfoDlg', 6), self.group_field)
        infoLayout.addRow(globals_.trans.string('InfoDlg', 7), self.website_field)

        self.password_label = infoLayout.labelForField(self.password_field)

        levelIsLocked = password != ''
        self.locked_label.setVisible(levelIsLocked)
        if self.password_label is not None:
            self.password_label.setVisible(levelIsLocked)
            self.line.setVisible(levelIsLocked)
        self.password_field.setVisible(levelIsLocked)

        info_box = QtWidgets.QGroupBox(globals_.trans.string('InfoDlg', 8, '[name]', creator))
        info_box.setLayout(infoLayout)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(info_box)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)

        self.update_password('')

    def update_password(self, text):
        password = globals_.Area.Metadata.strData('Password')
        if password is None:
            password = ''

        if text == password:
            self.name_field.setReadOnly(False)
            self.author_field.setReadOnly(False)
            self.group_field.setReadOnly(False)
            self.website_field.setReadOnly(False)
            self.edit_password_button.setDisabled(False)
        else:
            self.name_field.setReadOnly(True)
            self.author_field.setReadOnly(True)
            self.group_field.setReadOnly(True)
            self.website_field.setReadOnly(True)
            self.edit_password_button.setDisabled(True)

    def change_password(self):
        """
        Allows the changing of a given password
        """
        dlg = ChangePasswordDialog()
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.locked_label.setVisible(True)
            self.password_field.setVisible(True)
            self.line.setVisible(True)
            if self.password_label is not None:
                self.password_label.setVisible(True)

            password = str(dlg.verify_pass.text())
            globals_.Area.Metadata.setStrData('Password', password)
            self.password_field.setText(password)
            SetDirty()

            self.name_field.setReadOnly(False)
            self.author_field.setReadOnly(False)
            self.group_field.setReadOnly(False)
            self.website_field.setReadOnly(False)
            self.edit_password_button.setDisabled(False)
