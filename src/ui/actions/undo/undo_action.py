class UndoAction:
    """
    Abstract undo action
    """

    def undo(self) -> None:
        """
        Sets the target to its initial state
        """

    def redo(self) -> None:
        """
        Sets the target to its final state
        """

    def isExtentionOf(self, other: 'UndoAction') -> bool:
        """
        Returns True if this action extends another, else False
        """
        return False

    def extend(self, other: 'UndoAction') -> None:
        """
        Extends this UndoAction with the data from an extention of it.
        isExtentionOf must have returned True first!
        """

    def isNull(self) -> bool:
        """
        Returns True if this action is effectively a no-op
        """
        return True
