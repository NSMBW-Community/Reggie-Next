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
        globals_.mainWindow.actions['undo'].setEnabled(bool(self.pastActions))
        globals_.mainWindow.actions['redo'].setEnabled(bool(self.futureActions))


class UndoAction:
    """
    Abstract undo action
    """

    def undo(self):
        """
        Sets the target to its initial state
        """
        pass

    def redo(self):
        """
        Sets the target to its final state
        """
        pass

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
        pass

    def isNull(self):
        """
        Returns True if this action is effectively a no-op
        """
        return True


class MoveItemUndoAction(UndoAction):
    """
    An UndoAction for movement of a single level item that is not an object
    """

    def __init__(self, target, origX, origY, finalX, finalY):
        """
        Initializes the undo action
        """
        defType = target.instanceDef
        self.origDef = defType(target)
        self.finalDef = defType(target)
        self.origDef.objx = origX
        self.origDef.objy = origY
        self.finalDef.objx = finalX
        self.finalDef.objy = finalY

    def undo(self):
        """
        Sets the target object's position to the original position
        """
        instance = self.finalDef.findInstance()
        if instance:
            self.changeObjectPos(instance, self.origDef.objx, self.origDef.objy)
        else:
            print('Undo Move Item: Cannot find item instance! ' + str(self.finalDef))

    def redo(self):
        """
        Sets the target object's position to the final position
        """
        instance = self.origDef.findInstance()
        if instance:
            self.changeObjectPos(instance, self.finalDef.objx, self.finalDef.objy)
        else:
            print('Redo Move Item: Cannot find item instance! ' + str(self.origDef))

    @staticmethod
    def changeObjectPos(obj, newX, newY):
        """
        Changes the position of an object
        """
        from levelitems import SpriteItem, ObjectItem, PathItem

        if isinstance(obj, SpriteItem):
            # Sprites are weird so they handle this themselves
            obj.setNewObjPos(newX, newY)

        elif isinstance(obj, ObjectItem):
            # Objects use the objx and objy properties differently
            oldBR = obj.getFullRect()

            obj.objx, obj.objy = newX, newY
            obj.setPos(newX * 24, newY * 24)
            obj.UpdateRects()

            newBR = obj.getFullRect()

            globals_.mainWindow.scene.update(oldBR)
            globals_.mainWindow.scene.update(newBR)

        elif isinstance(obj, PathItem):
            obj.objx, obj.objy = newX, newY
            obj.setPos(newX * 1.5, newY * 1.5)
            obj.updatePos()

        else:
            # Everything else is normal
            obj.objx, obj.objy = newX, newY
            obj.setPos(newX * 1.5, newY * 1.5)

        globals_.mainWindow.levelOverview.update()

    def isExtentionOf(self, other):
        """
        Returns True if this MoveItemUndoAction extends another
        """
        return hasattr(other, 'origDef') and self.origDef.defMatchesData(other.origDef)

    def extend(self, other):
        """
        Extends this MoveItemUndoAction with the data from an extention of it.
        isExtentionOf must have returned True first!
        """
        self.finalDef.objx = other.finalDef.objx
        self.finalDef.objy = other.finalDef.objy

    def isNull(self):
        """
        Returns True if this action is effectively a no-op
        """
        return self.origDef.objx == self.finalDef.objx and self.origDef.objy == self.finalDef.objy


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
