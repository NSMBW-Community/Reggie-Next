from PyQt6 import QtCore, QtWidgets
from typing import cast

from data import globals_
from data.level.dirty import SetDirty
from data.level.nsmbw_level import NSMBWLevel
from ui.theme.reggie_theme import GetIcon, createHorzLine


class ChangePasswordDialog(QtWidgets.QDialog):
    """
    Dialog to set a password for the meta-info
    """
    def __init__(self) -> None:
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle(globals_.trans.string('dialog.meta_info.change_password.title'))
        self.setWindowIcon(GetIcon('lock'))

        self.new_pass = QtWidgets.QLineEdit()
        self.new_pass.setMaxLength(64)
        self.new_pass.textChanged.connect(self.check_password_match)
        self.new_pass.setMinimumWidth(320)

        self.verify_pass = QtWidgets.QLineEdit()
        self.verify_pass.setMaxLength(64)
        self.verify_pass.textChanged.connect(self.check_password_match)
        self.verify_pass.setMinimumWidth(320)

        ok_button = QtWidgets.QDialogButtonBox.StandardButton.Ok
        cancel_button = QtWidgets.QDialogButtonBox.StandardButton.Cancel

        button_box = QtWidgets.QDialogButtonBox()
        self.ok_button = button_box.addButton(ok_button)
        button_box.addButton(cancel_button)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        if self.ok_button is not None:
            self.ok_button.setDisabled(True)

        password_lyt = QtWidgets.QFormLayout()
        password_lyt.addRow(globals_.trans.string('dialog.meta_info.change_password.new_password'), self.new_pass)
        password_lyt.addRow(globals_.trans.string('dialog.meta_info.change_password.verify_password'), self.verify_pass)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(QtWidgets.QLabel(globals_.trans.string('dialog.meta_info.change_password.info')), 0, QtCore.Qt.AlignmentFlag.AlignCenter)
        main_layout.addLayout(password_lyt)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)

    def check_password_match(self) -> None:
        """
        Enables the OK button if the password matches
        """
        if self.ok_button is not None:
            self.ok_button.setDisabled(self.new_pass.text() != self.verify_pass.text() and self.new_pass.text() != '')


class MetaInfoDialog(QtWidgets.QDialog):
    """
    Dialog to set level metadata
    """

    def __init__(self) -> None:
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(globals_.trans.string('dialog.meta_info.title'))
        self.setWindowIcon(GetIcon('information-frame'))

        metadata = cast(NSMBWLevel, globals_.Level).metadata
        title = metadata.get_meta_data('title')
        author = metadata.get_meta_data('author')
        group = metadata.get_meta_data('group')
        website = metadata.get_meta_data('website')
        creator = metadata.get_meta_data('creator')
        password = metadata.get_meta_data('password')

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
            creator = globals_.trans.string('dialog.meta_info.unknown_version')
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

        self.edit_password_button = QtWidgets.QPushButton(globals_.trans.string('dialog.meta_info.add_change_password'))

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

        self.locked_label = QtWidgets.QLabel(globals_.trans.string('dialog.meta_info.password_info'))
        self.line = createHorzLine()

        infoLayout = QtWidgets.QFormLayout()
        infoLayout.addWidget(self.locked_label)
        infoLayout.addRow(globals_.trans.string('dialog.meta_info.field.password'), self.password_field)
        infoLayout.addRow(self.line)
        infoLayout.addRow(globals_.trans.string('dialog.meta_info.field.title'), self.name_field)
        infoLayout.addRow(globals_.trans.string('dialog.meta_info.field.author'), self.author_field)
        infoLayout.addRow(globals_.trans.string('dialog.meta_info.field.group'), self.group_field)
        infoLayout.addRow(globals_.trans.string('dialog.meta_info.field.website'), self.website_field)

        self.password_label = infoLayout.labelForField(self.password_field)

        levelIsLocked = password != ''
        self.locked_label.setVisible(levelIsLocked)
        if self.password_label is not None:
            self.password_label.setVisible(levelIsLocked)
            self.line.setVisible(levelIsLocked)
        self.password_field.setVisible(levelIsLocked)

        info_box = QtWidgets.QGroupBox(globals_.trans.string('dialog.meta_info.version', ('[name]', creator)))
        info_box.setLayout(infoLayout)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(info_box)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)

        self.update_password('')

    def update_password(self, text: str) -> None:
        password = cast(NSMBWLevel, globals_.Level).metadata.get_meta_data('password')
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

    def change_password(self) -> None:
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
            cast(NSMBWLevel, globals_.Level).metadata.set_meta_data('password', password)
            self.password_field.setText(password)
            SetDirty()

            self.name_field.setReadOnly(False)
            self.author_field.setReadOnly(False)
            self.group_field.setReadOnly(False)
            self.website_field.setReadOnly(False)
            self.edit_password_button.setDisabled(False)

    def save_info(self) -> None:
        """
        Saves the info back to the metadata system
        """
        metadata = cast(NSMBWLevel, globals_.Level).metadata
        metadata.set_meta_data('creator', f'Reggie! Next {globals_.ReggieVersionShort}')
        metadata.set_meta_data('title', self.name_field.text())
        metadata.set_meta_data('author', self.author_field.text())
        metadata.set_meta_data('group', self.group_field.text())
        metadata.set_meta_data('website', self.website_field.text())
        SetDirty()
