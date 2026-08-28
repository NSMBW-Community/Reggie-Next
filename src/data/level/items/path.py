from PyQt6 import QtCore, QtGui

import globals_
from src.data.level.items.basic import InstanceDefinition, LevelEditorItem
from src.ui.theme.reggie_theme import setOverrideCursor
from src.ui.widgets.item_sorts_by_other import ListWidgetItem_SortsByOther


class InstanceDefinition_PathItem(InstanceDefinition):
    """
    Definition of an instance of PathItem
    """
    fieldNames = (
        'pathid',
        'nodeid',
        'path',
    )

    @staticmethod
    def itemList():
        return globals_.Area.paths

    def createNew(self):
        return PathItem(self.objx, self.objy, *(field for field in self.fields))


class PathItem(LevelEditorItem):
    """
    Level editor item that represents a path node
    """
    instanceDef = InstanceDefinition_PathItem
    BoundingRect = QtCore.QRectF(0, 0, 24, 24)
    RoundedRect = QtCore.QRectF(1, 1, 22, 22)

    def __init__(self, objx, objy, path_id, node_id, parent):
        """
        Creates a path node with specific data
        """
        LevelEditorItem.__init__(self)
        if globals_.CursorMode != 0:
            self.setAcceptHoverEvents(True)

        self.font = globals_.NumberFont
        self.objx = objx
        self.objy = objy
        self.pathid = path_id
        self.nodeid = node_id
        self.path = parent

        list_str = self.ListString()
        if list_str is not None:
            self.listitem = ListWidgetItem_SortsByOther(self, list_str)

        self.LevelRect = QtCore.QRectF(self.objx / 16, self.objy / 16, 1.5, 1.5)
        self.setFlag(self.GraphicsItemFlag.ItemIsMovable, not globals_.PathsFrozen)
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, not globals_.PathsFrozen)

        old_snap = globals_.OverrideSnapping
        globals_.OverrideSnapping = True

        globals_.DirtyOverride += 1
        self.setPos(objx * 1.5, objy * 1.5)
        globals_.DirtyOverride -= 1

        globals_.OverrideSnapping = old_snap

        self.setZValue(25003)
        self.UpdateTooltip()
        self.UpdateListItem()

    def set_path_id(self, new_id):
        self.pathid = new_id

        self.UpdateTooltip()
        if self.listitem is not None:
            self.listitem.setText(self.ListString())
        self.update()

    def UpdateTooltip(self):
        """
        Updates the path node's tooltip
        """
        self.setToolTip(globals_.trans.string('Paths', 0, '[path]', self.pathid, '[node]', self.nodeid))

    def ListString(self):
        """
        Returns a string that can be used to describe the path node in a list
        """
        return globals_.trans.string('Paths', 1, '[path]', self.pathid, '[node]', self.nodeid)

    def __lt__(self, other):
        return (self.pathid, self.nodeid) < (other.pathid, other.nodeid)

    def update_id(self, new_id):
        """
        Path was changed, find our new node id
        """
        self.nodeid = new_id
        self.UpdateTooltip()
        self.UpdateListItem()
        self.update()

    def paint(self, painter, option, widget = ...):
        """
        Paints the path node
        """
        if not painter or not option or not self.font or not globals_.theme:
            return

        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setClipRect(option.exposedRect)

        if self.isSelected():
            painter.setBrush(QtGui.QBrush(globals_.theme.color('path_fill_s')))
            painter.setPen(QtGui.QPen(globals_.theme.color('path_lines_s')))
        else:
            painter.setBrush(QtGui.QBrush(globals_.theme.color('path_fill')))
            painter.setPen(QtGui.QPen(globals_.theme.color('path_lines')))

        if globals_.UseRoundedRectangles:
            painter.drawRoundedRect(self.RoundedRect, 4, 4)
        else:
            painter.drawRect(self.RoundedRect)

        painter.setFont(self.font)
        painter.drawText(4, 11, str(self.pathid))
        painter.drawText(4, 9 + QtGui.QFontMetrics(self.font).height(), str(self.nodeid))

    def delete(self):
        """
        Delete the path from the level
        """
        setOverrideCursor(None)
        was_last = self.path.remove_node(self.path.get_index(self))

        if was_last:
            globals_.Area.paths.remove(self.path)

    def hoverMoveEvent(self, event):
        LevelEditorItem.hoverMoveEvent(self, event)
        if (self.isSelected() or globals_.CursorMode == 2) and not globals_.PathsFrozen:
            setOverrideCursor(QtCore.Qt.CursorShape.SizeAllCursor)

    def hoverLeaveEvent(self, event):
        LevelEditorItem.hoverLeaveEvent(self, event)
        setOverrideCursor(None)
