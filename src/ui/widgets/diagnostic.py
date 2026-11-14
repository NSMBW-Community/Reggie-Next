from PyQt6 import QtCore, QtWidgets

from data import globals_
from ui.dialogs.diagnostic_tool import DiagnosticToolDialog
from ui.theme.reggie_theme import GetIcon


class DiagnosticWidget(QtWidgets.QWidget):
    """
    Widget for the auto-diagnostic tool
    """
    def __init__(self) -> None:
        """
        Creates and initializes the widget
        """
        super().__init__()
        self.diag_tool = DiagnosticToolDialog()

        # Button with icon and "X errors found" text
        self.status_button = QtWidgets.QToolButton()
        self.status_button.setAutoRaise(True)
        self.status_button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.status_button.clicked.connect(lambda: DiagnosticToolDialog().exec())

        self.manual_check_button = QtWidgets.QToolButton()
        self.manual_check_button.setAutoRaise(True)
        self.manual_check_button.setIcon(GetIcon('arrow-circle-double-135'))
        self.manual_check_button.setToolTip(globals_.trans.string('widget.auto_diagnostic.manual_check'))
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

    def set_timer(self) -> None:
        """
        Starts a timer
        """
        self.check_timer.stop()
        if not globals_.AutoDiagEnabled or globals_.AutoDiagFrequency == 0:
            return

        # Frequencies (in milliseconds)
        timer_values = [
            5000,
            10000,
            15000
        ]

        if globals_.AutoDiagFrequency != 0:
            self.check_timer.start(timer_values[globals_.AutoDiagFrequency - 1])

    def update_status(self) -> None:
        """
        Checks for errors and updates the widget accordingly
        """
        if not globals_.Area._is_loaded:
            return

        result, error_num = self.diag_tool.populate_list()

        icons = [
            'tick', 'exclamation', 'cross'
        ]

        # Figure out which string to show
        if result != DiagnosticToolDialog.Result.NO_ERROR:
            string = 'many' if error_num > 1 else 'one'
        else:
            string = 'none'

        # Error checking is disabled
        if globals_.AutoDiagFrequency == 0:
            self.status_button.setIcon(GetIcon('wrench-screwdriver'))
            self.status_button.setText(globals_.trans.string('widget.auto_diagnostic.checking_disabled'))
            return

        self.status_button.setIcon(GetIcon(f'wrench-screwdriver-{icons[result]}'))
        self.status_button.setText(globals_.trans.string(f'widget.auto_diagnostic.errors.error_{string}', ('[num]', error_num)))

    def handle_manual_update(self) -> None:
        """
        Handles the manual update button being pressed
        """
        result, error_num = self.diag_tool.populate_list()

        # Figure out which string to show
        if result != DiagnosticToolDialog.Result.NO_ERROR:
            string = 'many' if error_num > 1 else 'one'
        else:
            string = 'none'

        if globals_.AutoDiagFrequency == 0:
            pos = self.manual_check_button.mapToGlobal(self.manual_check_button.rect().center())
            text = globals_.trans.string(f'widget.auto_diagnostic.errors.error_{string}', ('[num]', error_num))
            QtWidgets.QToolTip.showText(pos, text, self.manual_check_button)
        else:
            self.update_status()

    def update_widget(self) -> None:
        """
        Updates the widget after (possibly) being modifed in the Preferences
        """
        # Update diagnostic widget
        self.set_timer()
        if globals_.AutoDiagEnabled:
            # Need to remake the entire bar, or else
            # auto-diag will appear after the zoom stuff
            globals_.mainWindow.setup_status_bar()

            self.update_status()
        else:
            status_bar = globals_.mainWindow.statusBar()
            if status_bar is not None:
                status_bar.removeWidget(self)
