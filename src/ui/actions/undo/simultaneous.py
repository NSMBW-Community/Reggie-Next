from src.ui.actions.undo.undo_action import UndoAction


class SimultaneousUndoAction(UndoAction):
    """
    An undo action that consists of multiple undo actions at once
    """

    def __init__(self, children):
        """
        Initializes the undo action
        """
        self.children = set(children)

    def undo(self):
        """
        Calls undo() on all children
        """
        for c in self.children:
            c.undo()

    def redo(self):
        """
        Calls redo() on all children
        """
        for c in self.children:
            c.redo()

    def isExtentionOf(self, other):
        """
        Returns True if this SinultaneousUndoAction and another one have equivalent children
        """
        if not hasattr(other, 'children'): return False
        searchIn = set(self.children)
        searchAgainst = set(other.children)
        for searchInObj in searchIn:
            found = False
            for searchAgainstObj in searchAgainst:
                if searchAgainstObj.isExtentionOf(searchInObj):
                    found = True
                    searchAgainst.remove(searchAgainstObj)
                    break  # only breaks out of inner loop
            if not found:
                return False
        return True

    def extend(self, other):
        """
        Extend this SimultaneousUndoAction with the data from an extention of it.
        isExtentionOf must have returned True first!
        """
        searchMine = set(self.children)
        searchOther = set(other.children)
        for searchMineObj in searchMine:
            for searchOtherObj in searchOther:
                if searchOtherObj.isExtentionOf(searchMineObj):
                    searchMineObj.extend(searchOtherObj)
                    searchOther.remove(searchOtherObj)
                    break  # only breaks out of inner loop

    def isNull(self):
        """
        Returns True if this action is effectively a no-op
        """
        return all(c.isNull() for c in self.children)
