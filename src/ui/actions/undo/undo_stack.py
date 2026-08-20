import globals_


class UndoStack:
    """
    A stack you can push UndoActions on, and stuff.
    """

    def __init__(self):
        self.pastActions = []
        self.futureActions = []

    def addAction(self, act):
        """
        Adds an action to the stack
        """
        self.pastActions.append(act)
        self.futureActions = []

        self.enableOrDisableMenuItems()

    def addOrExtendAction(self, act):
        """
        Adds an action to the stack, or extends the current one if applicable
        """
        if self.pastActions and self.pastActions[-1].isExtentionOf(act):
            self.pastActions[-1].extend(act)
            self.enableOrDisableMenuItems()
        else:
            self.addAction(act)

    def undo(self):
        """
        Undoes the last action
        """
        if not self.pastActions: return

        act = self.pastActions.pop()
        while act.isNull():
            # Keep popping null actions off
            if not self.pastActions:
                return
            act = self.pastActions.pop()

        act.undo()
        self.futureActions.append(act)

        self.enableOrDisableMenuItems()

    def redo(self):
        """
        Redoes the last undone action
        """
        if not self.futureActions: return

        act = self.futureActions.pop()
        while act.isNull():
            # Keep popping null actions off
            act = self.futureActions.pop()

        act.redo()
        self.pastActions.append(act)

        self.enableOrDisableMenuItems()

    def enableOrDisableMenuItems(self):
        """
        Enables or disables the menu items of mainWindow
        """
        main_window = globals_.mainWindow
        if main_window is not None:
            main_window.actions['undo'].setEnabled(bool(self.pastActions))
            main_window.actions['redo'].setEnabled(bool(self.futureActions))
