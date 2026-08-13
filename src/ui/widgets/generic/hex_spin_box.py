from PyQt6 import QtGui, QtWidgets

class HexSpinBox(QtWidgets.QSpinBox):
    class HexValidator(QtGui.QValidator):
        def __init__(self, min, max):
            QtGui.QValidator.__init__(self)
            self.valid = set('0123456789ABCDEF')
            self.min = min
            self.max = max

        def validate(self, a0, a1):
            try:
                a0 = str(a0).upper()
            except Exception:
                return (self.State.Invalid, a0, a1)
            valid = self.valid

            for char in a0:
                if char not in valid:
                    return (self.State.Invalid, a0, a1)

            try:
                value = int(a0, 16)
            except ValueError:
                # If value == '' it raises ValueError
                return (self.State.Invalid, a0, a1)

            if value < self.min or value > self.max:
                return (self.State.Intermediate, a0, a1)

            return (self.State.Acceptable, a0, a1)

    def __init__(self, format='%04X', *args):
        self.format = format
        QtWidgets.QSpinBox.__init__(self, *args)
        self.validator = self.HexValidator(self.minimum(), self.maximum())

    def setMinimum(self, min):
        self.validator.min = min
        QtWidgets.QSpinBox.setMinimum(self, min)

    def setMaximum(self, max):
        self.validator.max = max
        QtWidgets.QSpinBox.setMaximum(self, max)

    def setRange(self, min, max):
        self.validator.min = min
        self.validator.max = max
        QtWidgets.QSpinBox.setMinimum(self, min)
        QtWidgets.QSpinBox.setMaximum(self, max)

    def validate(self, input, pos):
        return self.validator.validate(input, pos)

    def textFromValue(self, v):
        return self.format % v

    def valueFromText(self, text):
        return int(str(text), 16)
