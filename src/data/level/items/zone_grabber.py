from PyQt6 import QtCore, QtGui, QtWidgets

from data import globals_
from data.level.items.basic import LevelEditorItem
from ui.theme.reggie_theme import setOverrideCursor


class ZoneGrabberItem(LevelEditorItem):
    """
    Level editor item that visually represents a Zone's resize grabbers.
    These are separate to allow for hover events
    """
    def __init__(self, parent: LevelEditorItem | None, cursor_type: int, paints = True) -> None:
        """
        Creates a zone grabber with specific data
        """
        LevelEditorItem.__init__(self)
        self.setZValue(50001)
        self.setParentItem(parent)

        if globals_.CursorMode != 0:
            self.setAcceptHoverEvents(True)

        self.BoundingRect = None
        self.cursor_type = cursor_type
        self.paints = paints

    def UpdateRects(self, rect: QtCore.QRectF) -> None:
        """
        Updates the grabber's bounding rectangle
        """
        self.prepareGeometryChange()
        self.BoundingRect = QtCore.QRectF(rect)

    def paint(self, painter: QtGui.QPainter | None, option: QtWidgets.QStyleOptionGraphicsItem | None, widget: QtWidgets.QWidget | None = None) -> None:
        """
        Paints the grabber on screen
        """
        if not painter or not option or not globals_.theme or not self.paints:
            return

        painter.setClipRect(option.exposedRect)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        color = globals_.theme.color('zone_corner')
        if color is not None and self.BoundingRect is not None:
            painter.fillRect(self.BoundingRect, color)

    def hoverMoveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent | None) -> None:
        # Zones cannot be selected, so the cursor will always be shown for these
        match self.cursor_type:
            case 1: # Diagonal TL/BR
                cursor = QtCore.Qt.CursorShape.SizeFDiagCursor
            case 2: # Diagonal BL/TR
                cursor = QtCore.Qt.CursorShape.SizeBDiagCursor
            case 3: # Horizontal
                cursor = QtCore.Qt.CursorShape.SizeHorCursor
            case 4: # Vertical
                cursor = QtCore.Qt.CursorShape.SizeVerCursor
            case _:
                cursor = None

        setOverrideCursor(cursor)

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent | None) -> None:
        setOverrideCursor(None)
