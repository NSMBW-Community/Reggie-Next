from PyQt6 import QtGui, QtWidgets


class HexSpinBox(QtWidgets.QSpinBox):
    class HexValidator(QtGui.QValidator):
        def __init__(self, min: int, max: int) -> None:
            QtGui.QValidator.__init__(self)
            self.valid = set('0123456789ABCDEF')
            self.min = min
            self.max = max

        def validate(self, a0: str, a1: int) -> tuple[QtGui.QValidator.State, str, int]:
            print(type(a0), type(a1))
            if not a0:
                # The empty string is a prefix of a valid input
                return (QtGui.QValidator.State.Intermediate, '', a1)

            try:
                a0 = str(a0).upper()
            except TypeError:
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

    def __init__(self, format: str = '%04X', parent: QtWidgets.QWidget | None = None) -> None:
        self.format = format
        QtWidgets.QSpinBox.__init__(self, parent)
        self.validator = self.HexValidator(self.minimum(), self.maximum())

    def setMinimum(self, min: int) -> None:
        self.validator.min = min
        QtWidgets.QSpinBox.setMinimum(self, min)

    def setMaximum(self, max: int) -> None:
        self.validator.max = max
        QtWidgets.QSpinBox.setMaximum(self, max)

    def setRange(self, min: int, max: int) -> None:
        self.validator.min = min
        self.validator.max = max
        QtWidgets.QSpinBox.setMinimum(self, min)
        QtWidgets.QSpinBox.setMaximum(self, max)

    def validate(self, input: str, pos: int) -> tuple[QtGui.QValidator.State, str, int]:
        return self.validator.validate(input, pos)

    def textFromValue(self, v: int) -> str:
        return self.format % v

    def valueFromText(self, text: str) -> int:
        return int(str(text), 16)
