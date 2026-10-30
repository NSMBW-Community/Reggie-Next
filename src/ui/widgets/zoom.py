from PyQt6 import QtCore, QtWidgets

from data import globals_
from ui.theme.reggie_theme import GetIcon

class ZoomWidget(QtWidgets.QWidget):
    """
    Widget that allows easy zoom level control
    """

    def __init__(self):
        """
        Creates and initializes the widget
        """
        super().__init__()
        max_width = 512 - 128
        max_height = 20

        self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.min_label = QtWidgets.QPushButton()
        self.dec_label = QtWidgets.QPushButton()
        self.inc_label = QtWidgets.QPushButton()
        self.max_label = QtWidgets.QPushButton()

        self.slider.setMaximumHeight(max_height)
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(globals_.mainWindow.ZoomLevels) - 1)
        self.slider.setTickInterval(2)
        self.slider.setTickPosition(self.slider.TickPosition.TicksAbove)
        self.slider.setPageStep(1)
        self.slider.setTracking(True)

        self.set_zoom_level(globals_.mainWindow.ZoomLevel)
        self.slider.valueChanged.connect(self.handle_slider_moved)

        self.min_label.setIcon(GetIcon('magnifier-zoom-minimum'))
        self.min_label.setFlat(True)
        self.min_label.clicked.connect(globals_.mainWindow.zoom_min)

        self.dec_label.setIcon(GetIcon('magnifier-zoom-out'))
        self.dec_label.setFlat(True)
        self.dec_label.clicked.connect(globals_.mainWindow.zoom_out)

        self.inc_label.setIcon(GetIcon('magnifier-zoom-in'))
        self.inc_label.setFlat(True)
        self.inc_label.clicked.connect(globals_.mainWindow.zoom_in)

        self.max_label.setIcon(GetIcon('magnifier-zoom-maximum'))
        self.max_label.setFlat(True)
        self.max_label.clicked.connect(globals_.mainWindow.zoom_max)

        self.main_layout = QtWidgets.QGridLayout()
        self.main_layout.addWidget(self.min_label, 0, 0)
        self.main_layout.addWidget(self.dec_label, 0, 1)
        self.main_layout.addWidget(self.slider, 0, 2)
        self.main_layout.addWidget(self.inc_label, 0, 3)
        self.main_layout.addWidget(self.max_label, 0, 4)
        self.main_layout.setVerticalSpacing(0)
        self.main_layout.setHorizontalSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 4, 0)

        self.setLayout(self.main_layout)
        self.setMinimumWidth(max_width)
        self.setMaximumWidth(max_width)
        self.setMaximumHeight(max_height)

    def handle_slider_moved(self):
        """
        Handle the slider being moved
        """
        globals_.mainWindow.set_zoom(globals_.mainWindow.ZoomLevels[self.slider.value()])

    def set_zoom_level(self, new_level):
        """
        Moves the slider to the zoom level given
        """
        new_pos = self.find_level_index(new_level)
        if new_pos is not None:
            self.slider.setSliderPosition(new_pos)

    def find_level_index(self, level):
        """
        Converts the Zoom level (float) to an index for the slider
        """
        for i, main_level in enumerate(globals_.mainWindow.ZoomLevels):
            if float(main_level) == float(level):
                return i
