from PyQt6 import QtCore, QtWidgets


class DualBox(QtWidgets.QWidget):
    """
    A dualbox widget for the sprite data
    """
    toggled = QtCore.pyqtSignal('PyQt_PyObject')

    def __init__(self, text1: str | None = None, text2: str | None = None, initial = 0, direction = 0):
        """
        Inits the dualbox with text to the left/above and text to the right/below
        """
        super().__init__()

        self.qsstemplate = """QPushButton {
            width: %dpx;
            height: %dpx;
            border-radius: 0px;
            border: 1px solid dark%%s;
            background: %%s;
        }"""

        self.value = initial
        self.direction = direction

        self.slider = QtWidgets.QPushButton()
        self.slider.clicked.connect(self.toggle)

        if direction == 0:
            layout = QtWidgets.QHBoxLayout()
            self.qsstemplate %= (40, 20)
        else:
            layout = QtWidgets.QVBoxLayout()
            self.qsstemplate %= (20, 40)

        layout.setContentsMargins(0, 0, 0, 0)

        if text1 is not None:
            label = QtWidgets.QPushButton(text1)
            label.setStyleSheet("""QPushButton {border:0; background:0; margin:0; padding:0}""")
            label.clicked.connect(self.toggle)
            if direction == 0:
                layout.addWidget(label, 0, QtCore.Qt.AlignmentFlag.AlignRight)
            else:
                layout.addWidget(label)

        layout.addWidget(self.slider)

        if text2 is not None:
            label = QtWidgets.QPushButton(text2)
            label.setStyleSheet("""QPushButton {border:0; background:0; margin:0; padding:0}""")
            label.clicked.connect(self.toggle)
            layout.addWidget(label)

        self.setLayout(layout)
        self.updateUI()

    def isSet(self):
        return self.value == 1

    def setValue(self, value):
        """
        Sets the value and updates the UI
        """
        # the only allowed values for 'value' are 0 and 1
        if value != 0 and value != 1:
            raise ValueError

        # don't do anything if we are already set
        if self.value == value:
            return

        self.value = value

        # update the UI
        # TODO: Make this a slider
        # TODO: Make this a nice animation
        self.updateUI()

    def getValue(self):
        return self.value

    def updateUI(self):
        colour = ['red', 'green'][self.value]
        self.qss = self.qsstemplate % (colour, colour)
        self.slider.setStyleSheet(self.qss)

    def toggle(self):
        """
        The slider was toggled, so update UI and emit the signal
        """
        self.setValue(1 - self.value)
        self.toggled.emit(self)
