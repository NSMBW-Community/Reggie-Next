import os

from PyQt6 import QtWidgets

from data import globals_
from data.common.settings import setSetting, setting
from data.common.translation import Translation
from data.common.translation_metadata import TranslationMetadata
from data.common.utils import get_reggiedata_folder
from ui.widgets.preferences.widgets.preference_tab import PreferenceTabWidget


class GeneralTab(PreferenceTabWidget):
    """
    General Tab
    """
    info: str | None = None

    def __init__(self, info_text: str) -> None:
        """
        Initializes the General Tab
        """
        super().__init__(info_text)
        self.info = info_text

        # Add the Clear Recent Files button
        clear_recent_button = QtWidgets.QPushButton(globals_.trans.string('dialog.preferences.tab.general.clear_recent_files'))
        clear_recent_button.setMaximumWidth(clear_recent_button.minimumSizeHint().width())
        clear_recent_button.clicked.connect(self.clear_recent_files)

        # Setup translation info
        self.translations = self.get_translations

        # Add the Translation Language setting
        self.trans_combo = QtWidgets.QComboBox()
        self.trans_combo.setMaximumWidth(256)
        self.trans_combo.currentIndexChanged.connect(self.update_translation)

        self.translation_info = QtWidgets.QLabel()

        trans_info_box = QtWidgets.QGroupBox(globals_.trans.string('dialog.preferences.tab.general.translation_info.title'))
        trans_lyt = QtWidgets.QFormLayout()
        trans_lyt.addRow(self.translation_info)
        trans_info_box.setLayout(trans_lyt)

        # Add the Zone Entrance Indicator checkbox
        self.zone_entrance_line = QtWidgets.QCheckBox(globals_.trans.string('dialog.preferences.tab.general.display_entrance_lines'))

        # Add the Zone Bounds Indicator checkbox
        self.zone_bound_indicators = QtWidgets.QCheckBox(globals_.trans.string('dialog.preferences.tab.general.display_zone_bounds'))

        # Reset data when hide checkbox
        self.reset_data_hide = QtWidgets.QCheckBox(globals_.trans.string('dialog.preferences.tab.general.reset_hidden_sprite_fields'))

        # Enable padding button
        self.enable_padding = QtWidgets.QCheckBox(globals_.trans.string('dialog.preferences.tab.general.pad_setting.title'))
        self.enable_padding.stateChanged.connect(
            lambda v: self.padding_value.setDisabled(v == 0)
        )

        # Padding size value
        self.padding_value = QtWidgets.QSpinBox()
        self.padding_value.setRange(0, 500000) # Set maximum to 500kb, more than enough for any level

        padding_warning = QtWidgets.QLabel(globals_.trans.string('dialog.preferences.tab.general.pad_setting.note'))

        # Place objects at full size
        self.full_object_size = QtWidgets.QCheckBox(globals_.trans.string('dialog.preferences.tab.general.place_objects_at_full_size'))

        # Toggle auto-diag
        self.auto_diag = QtWidgets.QCheckBox(globals_.trans.string('dialog.preferences.tab.general.auto_diagnostic.enable'))
        self.auto_diag.stateChanged.connect(
            lambda v: self.diag_freq.setDisabled(v == 0)
        )

        # Auto-diag frequency
        self.diag_freq = QtWidgets.QComboBox()
        self.diag_freq.setMaximumWidth(256)
        self.diag_freq.addItems(globals_.trans.string_list('dialog.preferences.tab.general.auto_diagnostic.error_check_frequency.options'))
        self.diag_freq.setToolTip(globals_.trans.string('dialog.preferences.tab.general.auto_diagnostic.error_check_frequency.tooltip'))

        auto_diag_box = QtWidgets.QGroupBox(globals_.trans.string('dialog.preferences.tab.general.auto_diagnostic.title'))
        diag_lyt = QtWidgets.QFormLayout()
        diag_lyt.addRow(self.auto_diag)
        diag_lyt.addRow(globals_.trans.string('dialog.preferences.tab.general.auto_diagnostic.error_check_frequency.text'), self.diag_freq)
        auto_diag_box.setLayout(diag_lyt)

        # Display unknown sprite warnings
        self.show_unk_sprite_msg = QtWidgets.QCheckBox(globals_.trans.string('dialog.preferences.tab.general.show_unknown_sprite_warning'))

        main_layout = QtWidgets.QFormLayout()
        main_layout.addRow(globals_.trans.string('dialog.preferences.tab.general.translation_info.title'), self.trans_combo)
        main_layout.addWidget(trans_info_box)
        main_layout.addWidget(clear_recent_button)
        main_layout.addWidget(self.enable_padding)
        main_layout.addRow(globals_.trans.string('dialog.preferences.tab.general.pad_setting.fixed_level_size'), self.padding_value)
        main_layout.addWidget(padding_warning)
        main_layout.addWidget(self.zone_entrance_line)
        main_layout.addWidget(self.zone_bound_indicators)
        main_layout.addWidget(self.reset_data_hide)
        main_layout.addWidget(self.full_object_size)
        main_layout.addWidget(self.show_unk_sprite_msg)
        main_layout.addWidget(auto_diag_box)
        self.setLayout(main_layout)

        # Set the button data
        self.set_data()

    def set_data(self) -> None:
        """
        Read the preferences and check the respective boxes
        """
        self.trans_combo.addItem('English')
        self.trans_combo.setCurrentIndex(0)

        for i, trans_dir in enumerate(os.listdir(os.path.join(get_reggiedata_folder(), 'translations'))):
            if trans_dir.lower() == 'english':
                continue

            fp = os.path.join(get_reggiedata_folder(), 'translations', trans_dir, 'strings.xml')
            if not os.path.isfile(fp):
                continue

            self.trans_combo.addItem(trans_dir.title())
            if trans_dir == str(setting('Translation')):
                self.trans_combo.setCurrentIndex(i)

        self.update_translation()

        self.zone_entrance_line.setChecked(globals_.DrawEntIndicators)
        self.zone_bound_indicators.setChecked(globals_.BoundsDrawn)
        self.reset_data_hide.setChecked(globals_.ResetDataWhenHiding)

        self.enable_padding.setChecked(globals_.EnablePadding)
        self.padding_value.setEnabled(globals_.EnablePadding)
        self.padding_value.setValue(globals_.PaddingLength)

        self.full_object_size.setChecked(globals_.PlaceObjectsAtFullSize)
        self.show_unk_sprite_msg.setChecked(globals_.ShowUnknownSpriteWarning)

        self.auto_diag.setChecked(globals_.AutoDiagEnabled)
        self.diag_freq.setEnabled(globals_.AutoDiagEnabled)
        self.diag_freq.setCurrentIndex(globals_.AutoDiagFrequency)

    def save(self) -> bool:
        """
        Saves general options
        """
        show_restart_warning = False

        # Get the translation's folder name
        name = self.translations[self.trans_combo.currentIndex()][0]
        if setting('Translation', 'English') not in ('None', name):
            print(setting('Translation', 'English'))
            print(name)
            show_restart_warning = True
        setSetting('Translation', name)

        globals_.DrawEntIndicators = self.zone_entrance_line.isChecked()
        setSetting('ZoneEntIndicators', globals_.DrawEntIndicators)

        globals_.BoundsDrawn = self.zone_bound_indicators.isChecked()
        setSetting('ZoneBoundIndicators', globals_.BoundsDrawn)

        globals_.ResetDataWhenHiding = self.reset_data_hide.isChecked()
        setSetting('ResetDataWhenHiding', globals_.ResetDataWhenHiding)

        globals_.EnablePadding = self.enable_padding.isChecked()
        setSetting('EnablePadding', globals_.EnablePadding)

        globals_.PaddingLength = self.padding_value.value()
        setSetting('PaddingLength', globals_.PaddingLength)

        globals_.PlaceObjectsAtFullSize = self.full_object_size.isChecked()
        setSetting('PlaceObjectsAtFullSize', globals_.PlaceObjectsAtFullSize)

        globals_.AutoDiagEnabled = self.auto_diag.isChecked()
        setSetting('AutoDiagEnabled', globals_.AutoDiagEnabled)

        globals_.AutoDiagFrequency = self.diag_freq.currentIndex()
        setSetting('AutoDiagFrequency', globals_.AutoDiagFrequency)

        globals_.ShowUnknownSpriteWarning = self.show_unk_sprite_msg.isChecked()
        setSetting('ShowUnknownSpriteWarning', globals_.ShowUnknownSpriteWarning)

        # Update diagnostic widget
        globals_.mainWindow.diagnostic.update_widget()

        return show_restart_warning

    def clear_recent_files(self) -> None:
        """
        Handle the Clear Recent Files button being clicked
        """
        ans = QtWidgets.QMessageBox.warning(None, globals_.trans.string('dialog.preferences.tab.general.clear_recent_files'),
                                            globals_.trans.string('dialog.preferences.tab.general.warning_clear_files'),
                                            QtWidgets.QMessageBox.StandardButton.Yes, QtWidgets.QMessageBox.StandardButton.No)
        if ans != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        globals_.mainWindow.RecentMenu.clear_all()

    @property
    def get_translations(self) -> tuple[tuple[str, TranslationMetadata], ...]:
        """
        Searches the Translations folder and returns a list of filepaths.
        Automatically adds 'English' to the list.
        """
        trans_path = os.path.join(get_reggiedata_folder(), 'translations')
        trans_list = [('English', TranslationMetadata.english())]
        for trans_name in os.listdir(trans_path):
            if not os.path.isdir(os.path.join(trans_path, trans_name)):
                continue

            trans = Translation.parse_main(trans_name)

            trans_list.append((trans_name, trans))

        return tuple(trans_list)

    def update_translation(self) -> None:
        """
        Updates the translation info
        """
        for name, transObj in self.translations:
            t = transObj
            if t.name == self.trans_combo.currentText():
                if t.name == 'English':
                    text = globals_.trans.string('dialog.preferences.tab.general.translation_info.info_default', ('[name]', t.name))
                    self.translation_info.setText(text)
                else:
                    text = globals_.trans.string('dialog.preferences.tab.general.translation_info.info', ('[name]', t.name),
                                                     ('[version]', t.version), ('[translator]', t.translator))
                    self.translation_info.setText(text)
