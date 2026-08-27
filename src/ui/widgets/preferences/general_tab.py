from PyQt6 import QtCore, QtWidgets
import os

import globals_
from src.data.common.settings import setting
from src.data.common.reggie_translation import ReggieTranslation

from src.ui.widgets.preferences.widgets.preference_tab import PreferenceTabWidget

class GeneralTab(PreferenceTabWidget):
    """
    General Tab
    """
    info: str | None = None

    def __init__(self, info_text):
        """
        Initializes the General Tab
        """
        super().__init__(info_text)
        self.info = info_text

        # Add the Clear Recent Files button
        clear_recent_button = QtWidgets.QPushButton(globals_.trans.string('PrefsDlg', 16))
        clear_recent_button.setMaximumWidth(clear_recent_button.minimumSizeHint().width())
        clear_recent_button.clicked.connect(self.clear_recent_files)

        # Setup translation info
        self.translations = self.get_translations

        # Add the Translation Language setting
        self.trans_combo = QtWidgets.QComboBox()
        self.trans_combo.setMaximumWidth(256)
        self.trans_combo.currentIndexChanged.connect(self.update_translation)

        self.translation_info = QtWidgets.QLabel()

        trans_info_box = QtWidgets.QGroupBox(globals_.trans.string('PrefsDlg', 42))
        trans_lyt = QtWidgets.QFormLayout()
        trans_lyt.addRow(self.translation_info)
        trans_info_box.setLayout(trans_lyt)

        # Add the Zone Entrance Indicator checkbox
        self.zone_entrance_line = QtWidgets.QCheckBox(globals_.trans.string('PrefsDlg', 31))

        # Add the Zone Bounds Indicator checkbox
        self.zone_bound_indicators = QtWidgets.QCheckBox(globals_.trans.string('PrefsDlg', 38))

        # Reset data when hide checkbox
        self.reset_data_hide = QtWidgets.QCheckBox(globals_.trans.string('PrefsDlg', 33))

        # Enable padding button
        self.enable_padding = QtWidgets.QCheckBox(globals_.trans.string('PrefsDlg', 35))
        self.enable_padding.stateChanged.connect(
            lambda v: self.padding_value.setDisabled(v == 0)
        )

        # Padding size value
        self.padding_value = QtWidgets.QSpinBox()
        self.padding_value.setRange(0, 500000) # Set maximum to 500kb, more than enough for any level

        # Place objects at full size
        self.full_object_size = QtWidgets.QCheckBox(globals_.trans.string('PrefsDlg', 37))

        # Insert new path node
        self.insert_path_node = QtWidgets.QCheckBox(globals_.trans.string('PrefsDlg', 39))

        # Display full filepath
        self.full_file_path = QtWidgets.QCheckBox(globals_.trans.string('PrefsDlg', 49))

        # Cursor modes
        self.cursor_mode = QtWidgets.QComboBox()
        self.cursor_mode.setMaximumWidth(256)
        self.cursor_mode.addItems(globals_.trans.stringList('PrefsDlg', 55))
        self.cursor_mode.setToolTip(globals_.trans.string('PrefsDlg', 54))

        # Toggle auto-diag
        self.auto_diag = QtWidgets.QCheckBox(globals_.trans.string('PrefsDlg', 71))
        self.auto_diag.stateChanged.connect(
            lambda v: self.diag_freq.setDisabled(v == 0)
        )

        # Auto-diag frequency
        self.diag_freq = QtWidgets.QComboBox()
        self.diag_freq.setMaximumWidth(256)
        self.diag_freq.addItems(globals_.trans.stringList('PrefsDlg', 73))
        self.diag_freq.setToolTip(globals_.trans.string('PrefsDlg', 74))

        auto_diag_box = QtWidgets.QGroupBox(globals_.trans.string('PrefsDlg', 70))
        diag_lyt = QtWidgets.QFormLayout()
        diag_lyt.addRow(self.auto_diag)
        diag_lyt.addRow(globals_.trans.string('PrefsDlg', 72), self.diag_freq)
        auto_diag_box.setLayout(diag_lyt)

        main_layout = QtWidgets.QFormLayout()
        main_layout.addRow(globals_.trans.string('PrefsDlg', 14), self.trans_combo)
        main_layout.addWidget(trans_info_box)
        main_layout.addRow(globals_.trans.string('PrefsDlg', 15), clear_recent_button)
        main_layout.addWidget(self.enable_padding)
        main_layout.addRow(globals_.trans.string('PrefsDlg', 36), self.padding_value)
        main_layout.addWidget(self.zone_entrance_line)
        main_layout.addWidget(self.zone_bound_indicators)
        main_layout.addWidget(self.reset_data_hide)
        main_layout.addWidget(self.full_object_size)
        main_layout.addWidget(self.insert_path_node)
        main_layout.addWidget(self.full_file_path)
        main_layout.addRow(globals_.trans.string('PrefsDlg', 53), self.cursor_mode)
        main_layout.addWidget(auto_diag_box)
        self.setLayout(main_layout)

        # Set the button data
        self.set_data()

    def set_data(self):
        """
        Read the preferences and check the respective boxes
        """
        self.trans_combo.addItem('English')
        self.trans_combo.setItemData(0, None, QtCore.Qt.ItemDataRole.UserRole)
        self.trans_combo.setCurrentIndex(0)

        for i, trans_dir in enumerate(os.listdir(os.path.join('reggiedata', 'translations'))):
            if trans_dir.lower() == 'english':
                continue

            fp = os.path.join('reggiedata', 'translations', trans_dir, 'main.xml')
            if not os.path.isfile(fp):
                continue

            trans_obj = ReggieTranslation(trans_dir)
            self.trans_combo.addItem(trans_obj.name)
            self.trans_combo.setItemData(i+1, trans_dir, QtCore.Qt.ItemDataRole.UserRole)
            if trans_dir == str(setting('Translation')):
                self.trans_combo.setCurrentIndex(i+1)

        self.update_translation()

        self.zone_entrance_line.setChecked(globals_.DrawEntIndicators)
        self.zone_bound_indicators.setChecked(globals_.BoundsDrawn)
        self.reset_data_hide.setChecked(globals_.ResetDataWhenHiding)

        self.enable_padding.setChecked(globals_.EnablePadding)
        self.padding_value.setEnabled(globals_.EnablePadding)
        self.padding_value.setValue(globals_.PaddingLength)

        self.full_object_size.setChecked(globals_.PlaceObjectsAtFullSize)
        self.insert_path_node.setChecked(globals_.InsertPathNode)
        self.full_file_path.setChecked(globals_.UseFullFilepath)
        self.cursor_mode.setCurrentIndex(globals_.CursorMode)

        self.auto_diag.setChecked(globals_.AutoDiagEnabled)
        self.diag_freq.setEnabled(globals_.AutoDiagEnabled)
        self.diag_freq.setCurrentIndex(globals_.AutoDiagFrequency)

    def clear_recent_files(self):
        """
        Handle the Clear Recent Files button being clicked
        """
        ans = QtWidgets.QMessageBox.question(None, globals_.trans.string('PrefsDlg', 17), globals_.trans.string('PrefsDlg', 18),
                                                QtWidgets.QMessageBox.StandardButton.Yes, QtWidgets.QMessageBox.StandardButton.No)
        if ans != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        if globals_.mainWindow is not None:
            globals_.mainWindow.RecentMenu.clear_all()

    @property
    def get_translations(self):
        """
        Searches the Translations folder and returns a list of filepaths.
        Automatically adds 'English' to the list.
        """
        trans_path = os.path.join('reggiedata', 'translations')
        trans_list = [('English', ReggieTranslation(None))]
        for trans_name in os.listdir(trans_path):
            if not os.path.isdir(os.path.join(trans_path, trans_name)):
                continue

            try:
                trans = ReggieTranslation(trans_name)
            except Exception:
                continue

            trans_list.append((trans_name, trans))

        return tuple(trans_list)

    def update_translation(self):
        """
        Updates the translation info
        """
        for name, transObj in self.translations:
            t = transObj
            if t.name == self.trans_combo.currentText():
                if t.name == 'English':
                    text = globals_.trans.string('PrefsDlg', 43, '[name]', t.name)
                    self.translation_info.setText(text)
                else:
                    text = globals_.trans.string('PrefsDlg', 44, '[name]', t.name, '[version]', t.version, '[translator]', t.translator)
                    self.translation_info.setText(text)
