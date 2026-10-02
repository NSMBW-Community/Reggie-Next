from PyQt6 import QtCore, QtGui
from data import globals_

def draw_foreground_grid(painter: QtGui.QPainter | None, rect: QtCore.QRectF):
    """
    Draw the foreground grid. This is separate so both
    the LevelScene and LevelView can access it.
    """
    if globals_.GridType is None or globals_.mainWindow is None or painter is None:
        return

    zoom = globals_.mainWindow.ZoomLevel
    drawLine = painter.drawLine
    grid_color = globals_.theme.color('grid')
    if grid_color is None:
        return

    # Classic grid
    if globals_.GridType == 'grid':
        startx = rect.x()
        startx -= (startx % 24)
        endx = startx + rect.width() + 24

        starty = rect.y()
        starty -= (starty % 24)
        endy = starty + rect.height() + 24

        x = startx
        while x <= endx:
            if x % 192 == 0:
                painter.setPen(QtGui.QPen(grid_color, 2, QtCore.Qt.PenStyle.DashLine))
                drawLine(QtCore.QPointF(x, starty), QtCore.QPointF(x, endy))
            elif x % 96 == 0 and zoom >= 25:
                painter.setPen(QtGui.QPen(grid_color, 1, QtCore.Qt.PenStyle.DashLine))
                drawLine(QtCore.QPointF(x, starty), QtCore.QPointF(x, endy))
            elif zoom >= 50:
                painter.setPen(QtGui.QPen(grid_color, 1, QtCore.Qt.PenStyle.DotLine))
                drawLine(QtCore.QPointF(x, starty), QtCore.QPointF(x, endy))
            x += 24

        y = starty
        while y <= endy:
            if y % 192 == 0:
                painter.setPen(QtGui.QPen(grid_color, 2, QtCore.Qt.PenStyle.DashLine))
                drawLine(QtCore.QPointF(startx, y), QtCore.QPointF(endx, y))
            elif y % 96 == 0 and zoom >= 25:
                painter.setPen(QtGui.QPen(grid_color, 1, QtCore.Qt.PenStyle.DashLine))
                drawLine(QtCore.QPointF(startx, y), QtCore.QPointF(endx, y))
            elif zoom >= 50:
                painter.setPen(QtGui.QPen(grid_color, 1, QtCore.Qt.PenStyle.DotLine))
                drawLine(QtCore.QPointF(startx, y), QtCore.QPointF(endx, y))
            y += 24

    # Checkerboard
    else:
        L = 0.2
        D = 0.1  # Change these values to change the checkerboard opacity

        Light = QtGui.QColor(grid_color)
        Dark = QtGui.QColor(grid_color)
        Light.setAlpha(int(Light.alpha() * L))
        Dark.setAlpha(int(Dark.alpha() * D))

        size = 24 if zoom >= 50 else 96

        board = QtGui.QPixmap(8 * size, 8 * size)
        board.fill(QtGui.QColor(0, 0, 0, 0))
        p = QtGui.QPainter(board)
        p.setPen(QtCore.Qt.PenStyle.NoPen)

        p.setBrush(QtGui.QBrush(Light))
        for x, y in ((0, size), (size, 0)):
            p.drawRect(x + (4 * size), y, size, size)
            p.drawRect(x + (4 * size), y + (2 * size), size, size)
            p.drawRect(x + (6 * size), y, size, size)
            p.drawRect(x + (6 * size), y + (2 * size), size, size)

            p.drawRect(x, y + (4 * size), size, size)
            p.drawRect(x, y + (6 * size), size, size)
            p.drawRect(x + (2 * size), y + (4 * size), size, size)
            p.drawRect(x + (2 * size), y + (6 * size), size, size)

        p.setBrush(QtGui.QBrush(Dark))
        for x, y in ((0, 0), (size, size)):
            p.drawRect(x, y, size, size)
            p.drawRect(x, y + (2 * size), size, size)
            p.drawRect(x + (2 * size), y, size, size)
            p.drawRect(x + (2 * size), y + (2 * size), size, size)

            p.drawRect(x, y + (4 * size), size, size)
            p.drawRect(x, y + (6 * size), size, size)
            p.drawRect(x + (2 * size), y + (4 * size), size, size)
            p.drawRect(x + (2 * size), y + (6 * size), size, size)

            p.drawRect(x + (4 * size), y, size, size)
            p.drawRect(x + (4 * size), y + (2 * size), size, size)
            p.drawRect(x + (6 * size), y, size, size)
            p.drawRect(x + (6 * size), y + (2 * size), size, size)

            p.drawRect(x + (4 * size), y + (4 * size), size, size)
            p.drawRect(x + (4 * size), y + (6 * size), size, size)
            p.drawRect(x + (6 * size), y + (4 * size), size, size)
            p.drawRect(x + (6 * size), y + (6 * size), size, size)

        del p

        # Adjust the rectangle to align with the grid, so we don't have to
        # paint pixmaps on non-integer coordinates
        x, y, _, _ = rect.getRect()
        mod = board.width()
        rect.adjust(-(x % mod), -(y % mod), 0, 0)

        painter.drawTiledPixmap(rect, board)
