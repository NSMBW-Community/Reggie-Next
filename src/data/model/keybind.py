from PyQt6 import QtCore, QtGui


class Keybind:
    def __init__(
        self, id: str, name: str | None, key_sequence: QtCore.QKeyCombination | QtGui.QKeySequence.StandardKey | str | None
    ):
        self.id = id
        self.name = name
        self.key_sequence = key_sequence
