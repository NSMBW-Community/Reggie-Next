from PyQt6 import QtWidgets, QtGui, QtCore

from data import globals_
from ui.theme.reggie_theme import GetIcon


class ScreenshotDialog(QtWidgets.QDialog):
    """
    Dialog to take screenshots
    """

    def __init__(self) -> None:
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(globals_.trans.string('ScrShtDlg', 0))
        self.setWindowIcon(GetIcon('camera'))

        self.target_combo = QtWidgets.QComboBox()
        self.target_combo.addItem(globals_.trans.string('ScrShtDlg', 1)) # Current Screen
        self.target_combo.addItem(globals_.trans.string('ScrShtDlg', 2)) # All Zones
        self.target_combo.currentIndexChanged.connect(self.target_changed)

        # Individual zones
        for i in range(len(globals_.Area.zones)):
            self.target_combo.addItem(globals_.trans.string('ScrShtDlg', 3, '[zone]', i + 1))

        self.grid_type = QtWidgets.QComboBox()
        self.grid_type.addItems(globals_.trans.stringList('ScrShtDlg', 9))

        curr_grid = 0
        if globals_.GridType is not None:
            if globals_.GridType == 'grid':
                curr_grid = 1
            else:
                curr_grid = 2

        self.grid_type.setCurrentIndex(curr_grid)

        self.hide_background = QtWidgets.QCheckBox()
        self.save_img = QtWidgets.QRadioButton()
        self.save_clip = QtWidgets.QRadioButton()

        self.save_img.setChecked(True)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        save_type_layout = QtWidgets.QHBoxLayout()
        save_type_layout.addWidget(self.save_img)
        save_type_layout.addWidget(QtWidgets.QLabel('|'))
        save_type_layout.addWidget(self.save_clip)
        save_type_layout.addWidget(QtWidgets.QLabel(globals_.trans.string('ScrShtDlg', 7)))

        self.margin_label = QtWidgets.QLabel(globals_.trans.string('ScrShtDlg', 10))

        self.margin = QtWidgets.QSpinBox()
        self.margin.setRange(0, 16384)
        self.margin.setValue(40)
        self.margin.setToolTip(globals_.trans.string('ScrShtDlg', 11))

        self.target_changed(0)

        main_layout = QtWidgets.QFormLayout()
        main_layout.addRow(globals_.trans.string('ScrShtDlg', 4), self.target_combo)
        main_layout.addRow(globals_.trans.string('ScrShtDlg', 8), self.grid_type)
        main_layout.addRow(globals_.trans.string('ScrShtDlg', 5), self.hide_background)
        main_layout.addRow(globals_.trans.string('ScrShtDlg', 6), save_type_layout)
        main_layout.addRow(self.margin_label, self.margin)
        main_layout.addRow(button_box)
        self.setLayout(main_layout)

    def target_changed(self, index: int) -> None:
        """
        Handles the current target changing
        """
        disabled = index == 0
        self.margin.setDisabled(disabled)
        self.margin_label.setDisabled(disabled)

    def create_screenshot(self) -> None:
        """
        Takes the screenshot
        """
        if globals_.mainWindow is None:
            return

        target = self.target_combo.currentIndex()
        grid_type = self.grid_type.currentIndex()
        hide_background = self.hide_background.isChecked()
        save_to_file = self.save_img.isChecked()

        # Update the canvas grid while we take the screenshot
        grid_type_list = [None, 'grid', 'checker']
        current_grid_type = globals_.GridType
        globals_.GridType = grid_type_list[grid_type]
        globals_.mainWindow.scene.update()

        file_name = ''
        if save_to_file:
            filt = f'{globals_.trans.string('FileDlgs', 4)} (*.png)'

            file_name = QtWidgets.QFileDialog.getSaveFileName(self, globals_.trans.string('FileDlgs', 3), None, filt)[0]
            if file_name == '':
                return

        # Current view
        if target == 0:
            screenshot_rect = QtCore.QRect(QtCore.QPoint(), globals_.mainWindow.view.size())
            renderer = globals_.mainWindow.view
            ss_img = QtGui.QImage(screenshot_rect.size(), QtGui.QImage.Format.Format_ARGB32)
        else:
            # All zones together
            if target == 1:
                screenshot_rect = QtCore.QRectF()

                for z in globals_.Area.zones:
                    screenshot_rect |= z.ZoneRect

            # Specific zone
            else:
                screenshot_rect = globals_.Area.zones[target - 2].ZoneRect

            # Map the zone rects to the scene coordinate system
            screenshot_rect = (QtGui.QTransform() * 1.5).mapRect(screenshot_rect)

            # Add padding on all sides
            pad = self.margin.value()
            screenshot_rect += QtCore.QMarginsF(pad, pad, pad, pad)

            # Make sure the rectangle doesn't go out of bounds
            screenshot_rect &= QtCore.QRectF(0, 0, 1024 * 24, 512 * 24)

            renderer = globals_.mainWindow.scene
            renderer.is_screenshot = True
            ss_img = QtGui.QImage(screenshot_rect.size().toSize(), QtGui.QImage.Format.Format_ARGB32)

        ss_img.fill(QtCore.Qt.GlobalColor.transparent)
        ss_painter = QtGui.QPainter(ss_img)

        # Remove the background
        if hide_background:
            brush = globals_.mainWindow.scene.backgroundBrush()
            style = brush.style()
            brush.setStyle(QtCore.Qt.BrushStyle.NoBrush)
            globals_.mainWindow.scene.setBackgroundBrush(brush)

            # Render
            renderer.render(ss_painter, source=screenshot_rect)

            # Restore the background
            brush.setStyle(style)
            globals_.mainWindow.scene.setBackgroundBrush(brush)
        else:
            renderer.render(ss_painter, source=screenshot_rect)

        ss_painter.end()

        if save_to_file:
            ss_img.save(file_name, 'PNG', 50)
        else:
            if globals_.app is not None:
                clip = globals_.app.clipboard()
                if clip is not None:
                    clip.setImage(ss_img)

        if target != 0:
            globals_.mainWindow.scene.is_screenshot = False

        # Restore grid
        globals_.GridType = current_grid_type
        globals_.mainWindow.scene.update()
