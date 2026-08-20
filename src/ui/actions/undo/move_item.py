import globals_
from src.ui.actions.undo.undo_action import UndoAction


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
        from levelitems import ObjectItem, PathItem, SpriteItem

        main_window = globals_.mainWindow

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

            if main_window is not None:
                main_window.scene.update(oldBR)
                main_window.scene.update(newBR)

        elif isinstance(obj, PathItem):
            obj.objx, obj.objy = newX, newY
            obj.setPos(newX * 1.5, newY * 1.5)
            obj.updatePos()

            # Update the path line
            obj.path._line_item.update_path()

        else:
            # Everything else is normal
            obj.objx, obj.objy = newX, newY
            obj.setPos(newX * 1.5, newY * 1.5)

        if main_window is not None:
            main_window.level_overview.update()

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
