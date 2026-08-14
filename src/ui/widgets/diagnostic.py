from PyQt6 import QtCore, QtWidgets

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

        self.diag_icon = QtWidgets.QPushButton()
        self.diag_icon.setIcon(GetIcon('autodiagnosticgood'))
        self.diag_icon.setFlat(True)
        self.diag_icon.setGeometry(2, 1, 2, 1)
        # self.diag_icon.setHeight(59)
        # self.diag_icon.clicked.connect(ReggieWindow.HandleDiagnostics)
        self.diag_icon.clicked.connect(self.find_issues)

        self.main_layout = QtWidgets.QGridLayout()
        self.main_layout.addWidget(self.diag_icon, 0, 0)
        self.main_layout.setVerticalSpacing(0)
        self.main_layout.setHorizontalSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        self.start_timer = QtCore.QTimer()
        self.start_timer.setSingleShot(True)
        self.start_timer.timeout.connect(self.start_loop_timer)
        self.start_timer.start(10000)

    def start_loop_timer(self):
        self.loop_timer = QtCore.QTimer()
        self.loop_timer.timeout.connect(self.find_issues)
        self.loop_timer.start(50)

    def find_issues(self):
        result, error_num = self.diag_tool.populate_list()
        print(f'AutoDiag: {result} -> {error_num} error(s) found.')
