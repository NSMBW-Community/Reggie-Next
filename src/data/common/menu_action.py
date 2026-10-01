from PyQt6 import QtCore, QtGui


class MenuAction:
    """Represents a menu action."""

    def __init__(
        self, shortname: str, function, icon: QtGui.QIcon, label: str | None, status_text: str | None,
        key_sequence: QtGui.QKeySequence | QtGui.QKeySequence.StandardKey | str | None, checkable = False
    ):
        self.shortname = shortname
        self.function = function
        self.icon = icon
        self.label = label
        self.status_text = status_text
        self.key_sequence = key_sequence
        self.is_checkable = checkable

    def create_action(self, parent: QtCore.QObject) -> QtGui.QAction:
        """
        Creates an action from the class info
        """
        if self.icon is not None:
            act = QtGui.QAction(self.icon, self.label, parent)
        else:
            act = QtGui.QAction(self.label, parent)

        if self.key_sequence is not None:
            act.setShortcut(self.key_sequence)
        if self.status_text is not None:
            act.setStatusTip(self.status_text)
        if self.is_checkable:
            act.setCheckable(True)
        if self.function is not None:
            act.triggered.connect(self.function)

        return act
