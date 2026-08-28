from PyQt6 import QtCore, QtGui, QtWidgets

import globals_


class PathEditorLineItem(QtWidgets.QGraphicsPathItem):
    """
    Level editor item to draw a line between the path nodes that belong to the
    same path.
    """

    def __init__(self, path):
        """
        Creates a path line that belongs to a given path.
        """
        super().__init__()

        self._path = path

        self.setFlag(self.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, False)

        color = globals_.theme.color('path_connector')
        if color is not None:
            self.setPen(QtGui.QPen(color, 3, join=QtCore.Qt.PenJoinStyle.RoundJoin, cap=QtCore.Qt.PenCapStyle.RoundCap))

        self.update_path()
        self.setZValue(25002)

    def update_path(self):
        """
        Updates the path. This should be called whenever at least one of the
        nodes of the path moves, is added or is deleted.
        """
        points = self._path.get_points()

        line_path = QtGui.QPainterPath()
        line_path.addPolygon(QtGui.QPolygonF(points))

        old_rect = self.boundingRect()

        self.setPath(line_path)

        # Bug in Qt? The old rect of the path is not updated, so artifacts
        # remain on the scene if we do not update the scene manually...
        if globals_.mainWindow is not None:
            globals_.mainWindow.scene.update(old_rect)
