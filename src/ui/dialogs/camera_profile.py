from PyQt6 import QtWidgets, QtCore

import globals_
from ui import GetIcon, createHorzLine, CustomSortableListWidgetItem
from zones import CameraModeZoomSettingsLayout

class CameraProfilesDialog(QtWidgets.QDialog):
    """
    Dialog for editing camera profiles
    """

    def __init__(self):
        """
        Creates and initialises the dialog
        """
        super().__init__()
        self.setWindowTitle(globals_.trans.string('CamProfsDlg', 0))
        self.setWindowIcon(GetIcon('camprofile'))
        self.setMinimumHeight(450)

        self.list = QtWidgets.QListWidget()
        self.list.itemSelectionChanged.connect(self.handle_selection_changed)
        self.list.setSortingEnabled(True)

        self.add_button = QtWidgets.QPushButton(globals_.trans.string('CamProfsDlg', 1))
        self.add_button.clicked.connect(self.handle_add)

        self.remove_button = QtWidgets.QPushButton(globals_.trans.string('CamProfsDlg', 2))
        self.remove_button.clicked.connect(self.handle_remove)
        self.remove_button.setEnabled(False)

        list_layout = QtWidgets.QGridLayout()
        list_layout.addWidget(self.add_button, 0, 0)
        list_layout.addWidget(self.remove_button, 0, 1)
        list_layout.addWidget(self.list, 1, 0, 1, 2)

        self.event_id = QtWidgets.QSpinBox()
        self.event_id.setRange(0, 255)
        self.event_id.setToolTip(globals_.trans.string('CamProfsDlg', 6))
        self.event_id.valueChanged.connect(self.handle_event_id_changed)

        self.camera_settings = CameraModeZoomSettingsLayout(False)
        self.camera_settings.setValues(0, 0)
        self.camera_settings.edited.connect(self.handle_camera_settings_changed)

        profile_layout = QtWidgets.QFormLayout()
        profile_layout.addRow(globals_.trans.string('CamProfsDlg', 5), self.event_id)
        profile_layout.addRow(createHorzLine())
        profile_layout.addRow(self.camera_settings)

        self.profile_box = QtWidgets.QGroupBox(globals_.trans.string('CamProfsDlg', 3))
        self.profile_box.setLayout(profile_layout)
        self.profile_box.setEnabled(False)
        self.profile_box.setToolTip(globals_.trans.string('CamProfsDlg', 4))

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout = QtWidgets.QGridLayout()
        main_layout.addLayout(list_layout, 0, 0)
        main_layout.addWidget(self.profile_box, 0, 1)
        main_layout.addWidget(button_box, 1, 0, 1, 2)
        self.setLayout(main_layout)

        # Populate the profile list
        for profile in globals_.Area.camprofiles:
            item = CustomSortableListWidgetItem()
            item.setData(QtCore.Qt.ItemDataRole.UserRole, profile)

            item.sort_key = profile[0]
            self.update_item_title(item)
            self.list.addItem(item)

        self.list.sortItems()

        # If we have items, go ahead and select the first one
        if self.list.count() != 0:
            self.list.setCurrentRow(0)

    def handle_add(self):
        """
        Handles adding a profile
        """
        new_id = 1
        for row in range(self.list.count()):
            item = self.list.item(row)
            if item is not None:
                values = item.data(QtCore.Qt.ItemDataRole.UserRole)
                new_id = max(new_id, values[0] + 1)

        item = CustomSortableListWidgetItem()
        item.setData(QtCore.Qt.ItemDataRole.UserRole, [new_id, 0, 0])
        self.update_item_title(item)
        self.list.addItem(item)

    def handle_remove(self):
        """
        Handles removing a profile
        """
        self.list.takeItem(self.list.currentRow())

    def handle_selection_changed(self):
        """
        Handles updating the profile fields
        """
        selItems = self.list.selectedItems()

        self.remove_button.setEnabled(bool(selItems))
        self.profile_box.setEnabled(bool(selItems))

        if selItems:
            selItem = selItems[0]
            values = selItem.data(QtCore.Qt.ItemDataRole.UserRole)

            self.event_id.setValue(values[0])
            self.camera_settings.setValues(values[1], values[2])

    def handle_event_id_changed(self, event_id):
        """
        Handles the Triggering Event ID being changed
        """
        selItem = self.list.selectedItems()[0]
        values = selItem.data(QtCore.Qt.ItemDataRole.UserRole)
        values[0] = event_id
        selItem.setData(QtCore.Qt.ItemDataRole.UserRole, values)

        if isinstance(selItem, CustomSortableListWidgetItem):
            selItem.sort_key = event_id
        self.update_item_title(selItem)

    def handle_camera_settings_changed(self):
        """
        Handles updating the camera settings
        """
        selItem = self.list.selectedItems()[0]
        values = selItem.data(QtCore.Qt.ItemDataRole.UserRole)
        values[1] = self.camera_settings.modeButtonGroup.checkedId()
        values[2] = self.camera_settings.screenSizes.currentIndex()
        selItem.setData(QtCore.Qt.ItemDataRole.UserRole, values)

    def update_item_title(self, item):
        """
        Updates the profile name in the list
        """
        item.setText(globals_.trans.string('CamProfsDlg', 7, '[id]', item.data(QtCore.Qt.ItemDataRole.UserRole)[0]))
