from PyQt6 import QtCore, QtWidgets
from enum import IntEnum

import globals_
from ui import GetIcon

from src.ui.dialogs.diagnostic_tool import DiagnosticToolDialog

# TODO:
# Add some proper functionality for this
# Make it check for issues every 5 (or 10?) seconds
# Have it say the number of issues found, clicking on it opens diag tool
# Make it a togglable option in the preferences
class DiagnosticWidget(QtWidgets.QWidget):
    """
    Widget for the auto-diagnostic tool
    """
    def __init__(self):
        """
        Creates and initializes the widget
        """
        super().__init__()
        self.diag_tool = DiagnosticToolDialog()

        # Button with icon and "X errors found" text
        self.status_button = QtWidgets.QToolButton()
        self.status_button.setAutoRaise(True)
        self.status_button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        if globals_.mainWindow is not None:
            self.status_button.clicked.connect(globals_.mainWindow.HandleDiagnostics)

        self.manual_check_button = QtWidgets.QToolButton()
        self.manual_check_button.setAutoRaise(True)
        self.manual_check_button.setIcon(GetIcon('reload'))
        self.manual_check_button.setToolTip(globals_.trans.string('AutoDiag', 4))
        self.manual_check_button.clicked.connect(self.handle_manual_update)

        self.main_layout = QtWidgets.QGridLayout()
        self.main_layout.addWidget(self.status_button, 0, 0)
        self.main_layout.addWidget(self.manual_check_button, 0, 1)
        self.main_layout.setVerticalSpacing(0)
        self.main_layout.setHorizontalSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 5, 0)
        self.setLayout(self.main_layout)

        self.check_timer = QtCore.QTimer()
        self.check_timer.timeout.connect(self.update_status)

    def set_timer(self):
        """
        Starts a timer
        """
        self.check_timer.stop()
        if not globals_.AutoDiagEnabled or globals_.AutoDiagFrequency == 0:
            return

        # Frequencies (in seconds)
        timer_values = [
            5000,
            10000,
            15000
        ]

        if globals_.AutoDiagFrequency != 0:
            self.check_timer.start(timer_values[globals_.AutoDiagFrequency - 1])

    def update_status(self):
        """
        Checks for errors and updates the widget accordingly
        """
        result, error_num = self.diag_tool.populate_list()

        icons = [
            'good', 'warning', 'bad'
        ]

        # Figure out which string to show
        if result != DiagnosticToolDialog.Result.NO_ERROR:
            string_id = error_num > 1
        else:
            string_id = 2

        # Error checking is disabled
        if globals_.AutoDiagFrequency == 0:
            self.status_button.setIcon(GetIcon('autodiag-none'))
            self.status_button.setText(globals_.trans.string('AutoDiag', 3))
            return

        self.status_button.setIcon(GetIcon(f'autodiag-{icons[result]}'))
        self.status_button.setText(globals_.trans.string('AutoDiag', string_id, '[num]', error_num))

    def handle_manual_update(self):
        """
        Handles the manual update button being pressed
        """
        result, error_num = self.diag_tool.populate_list()

        # Figure out which string to show
        if result != DiagnosticToolDialog.Result.NO_ERROR:
            string_id = error_num > 1
        else:
            string_id = 2

        if globals_.AutoDiagFrequency == 0:
            pos = self.manual_check_button.mapToGlobal(self.manual_check_button.rect().center())
            text = globals_.trans.string('AutoDiag', string_id, '[num]', error_num)
            QtWidgets.QToolTip.showText(pos, text, self.manual_check_button)
        else:
            self.update_status()
