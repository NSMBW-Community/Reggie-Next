from PyQt6 import QtCore, QtGui, QtWidgets

from src.data.common.utils import clamp


class IntSpinBox(QtWidgets.QAbstractSpinBox):
    """
    A spin box that can handle integers of arbitrary size.
    """
    _value: int | None
    _minimum: int
    _maximum: int
    _start: int
    _increment: int
    # Formatted like: ((raw value, num to display), ...)
    _overrides: list

    valueChanged = QtCore.pyqtSignal('int')

    def __init__(self, parent=None, start=0, increment=1, overrides=None):
        QtWidgets.QAbstractSpinBox.__init__(self, parent)
        self.editingFinished.connect(self.interpretText)

        self._value = None
        self._minimum = 0
        self._maximum = 1 << 32
        self._start = start
        self._increment = increment
        self._overrides = overrides if overrides is not None else []

        self.setValue(self._start)

    def interpretText(self):
        """
        Reimplements interpretText.
        """
        # The text has already been validated - it's either a number or the
        # empty string
        lineEdit = self.lineEdit()
        if not lineEdit:
            return

        text = lineEdit.text()
        if not text:
            text = str(self._start)

        self.setValue(self.valueFromText(text))

    def validate(self, input: str | None, pos: int):
        """
        Checks whether the currently entered text is valid.
        """
        if not input:
            # The empty string is a prefix of a valid input
            return (QtGui.QValidator.State.Intermediate, '', pos)

        try:
            val = int(input, 10)
        except ValueError:
            return (QtGui.QValidator.State.Invalid, input, pos)

        # This implementation really only works well if all prefixes of numbers
        # between the minimum and maximum are themselves numbers between the
        # minimum and maximum...
        if not self._minimum <= val <= self._maximum and not self._start <= val <= ((self._maximum * self._increment) + self._start):
            return (QtGui.QValidator.State.Invalid, input, pos)

        return (QtGui.QValidator.State.Acceptable, input, pos)

    def stepEnabled(self):
        """
        Returns a flag indicating in which directions the value can be stepped.
        """
        flag = QtWidgets.QAbstractSpinBox.StepEnabledFlag.StepNone

        if self._value is not None:
            if self._value < self._maximum:
                flag |= QtWidgets.QAbstractSpinBox.StepEnabledFlag.StepUpEnabled
            if self._minimum < self._value:
                flag |= QtWidgets.QAbstractSpinBox.StepEnabledFlag.StepDownEnabled

        return flag

    def value(self) -> int | None:
        return self._value

    def setMaximum(self, val: int):
        self._maximum = val
    def maximum(self) -> int:
        return self._maximum

    def setMinimum(self, val: int):
        self._minimum = val
    def minimum(self) -> int:
        return self._minimum

    def setRange(self, min_: int, max_: int):
        self.setMinimum(min_)
        self.setMaximum(max_)

    def stepBy(self, steps: int):
        """
        Add 'steps' to the current value.
        """
        self.setValue(
            clamp((self._value or 0) + steps, self._minimum, self._maximum)
        )

    def valueFromText(self, text: str) -> int:
        val = (int(text) - self._start) // self._increment
        return max(val, 0)

    def textFromValue(self, val: int) -> str:
        return str(val)

    def setValue(self, val: int | None):
        """
        Updates the value shown by the line edit and emits a signal when the
        value represented by the text of the line edit has changed.
        """
        if val is None and val != 0:
            val = self._maximum

        lineEdit = self.lineEdit()
        if lineEdit is None:
            return

        if self._value == val:
            if val == 0:
                lineEdit.setText(self.textFromValue(self._start))

                # Fixes a bug when reloading spritedata
                if self._overrides is not None:
                    for rawVal, dispNum in self._overrides:
                        if val == rawVal:
                            textVal = dispNum
                            lineEdit.setText(self.textFromValue(textVal))
            return

        textVal = (val * self._increment) + self._start

        # Check for any value overrides
        if self._overrides is not None:
            for rawVal, dispNum in self._overrides:
                if val == rawVal:
                    textVal = dispNum

        lineEdit.setText(self.textFromValue(textVal))
        self._value = val
        self.valueChanged.emit(val)
