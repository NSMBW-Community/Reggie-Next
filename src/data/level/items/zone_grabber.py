from PyQt6 import QtCore, QtGui

import globals_
from src.data.level.items.basic import LevelEditorItem
from src.ui.theme.reggie_theme import setOverrideCursor


class ZoneGrabberItem(LevelEditorItem):
    """
    Level editor item that visually represents a Zone's resize grabbers.
    These are separate to allow for hover events
    """
    def __init__(self, parent, corner):
        """
        Creates a zone grabber with specific data
        """
        LevelEditorItem.__init__(self)
        self.setZValue(50001)
        self.setParentItem(parent)

        if globals_.CursorMode != 0:
            self.setAcceptHoverEvents(True)

        self.BoundingRect = None
        self.corner = corner

    def UpdateRects(self, rect):
        """
        Updates the grabber's bounding rectangle
        """
        self.prepareGeometryChange()
        self.BoundingRect = QtCore.QRectF(rect)

    def paint(self, painter, option, widget = ...):
        """
        Paints the grabber on screen
        """
        if not painter or not option or not globals_.theme:
            return

        painter.setClipRect(option.exposedRect)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        color = globals_.theme.color('zone_corner')
        if color is not None and self.BoundingRect is not None:
            painter.fillRect(self.BoundingRect, color)

    def hoverMoveEvent(self, event):
        # Zones cannot be selected, so the cursor will always be shown for these
        if self.corner in (1, 4):
            setOverrideCursor(QtCore.Qt.CursorShape.SizeFDiagCursor)
        elif self.corner in (2, 3):
            setOverrideCursor(QtCore.Qt.CursorShape.SizeBDiagCursor)

    def hoverLeaveEvent(self, event):
        setOverrideCursor(None)
