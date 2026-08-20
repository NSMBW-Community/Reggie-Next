class UndoAction:
    """
    Abstract undo action
    """

    def undo(self):
        """
        Sets the target to its initial state
        """

    def redo(self):
        """
        Sets the target to its final state
        """

    def isExtentionOf(self, other):
        """
        Returns True if this action extends another, else False
        """
        return False

    def extend(self, other):
        """
        Extends this UndoAction with the data from an extention of it.
        isExtentionOf must have returned True first!
        """

    def isNull(self):
        """
        Returns True if this action is effectively a no-op
        """
        return True
