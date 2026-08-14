from PyQt6 import QtWidgets

import globals_

class ZoomStatusWidget(QtWidgets.QWidget):
    """
    Shows the current zoom level's percentage
    """
    def __init__(self):
        """
        Creates and initializes the widget
        """
        super().__init__()
        self.label = QtWidgets.QPushButton('100%')
        self.label.setFlat(True)
        if globals_.mainWindow is not None:
            self.label.clicked.connect(globals_.mainWindow.HandleZoomActual)

        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.addWidget(self.label)
        self.main_layout.setContentsMargins(4, 0, 8, 0)
        self.setLayout(self.main_layout)

        self.setMaximumWidth(57)

    def set_zoom_level(self, zoom_level):
        """
        Updates the widget
        """
        if float(int(zoom_level)) == float(zoom_level):
            self.label.setText(str(int(zoom_level)) + '%')
        else:
            self.label.setText(str(float(zoom_level)) + '%')
