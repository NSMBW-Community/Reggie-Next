from PyQt6 import QtWidgets, QtGui, QtCore

import globals_

class LevelOverviewWidget(QtWidgets.QWidget):
    """
    Widget that shows an overview of the level and can be clicked to move the view
    """
    moved = QtCore.pyqtSignal(float, float)

    def __init__(self):
        """
        Constructor for the level overview widget
        """
        QtWidgets.QWidget.__init__(self)
        self.setSizePolicy(
            QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.MinimumExpanding))

        self.bg_brush = QtGui.QBrush(globals_.theme.color('bg'))
        self.obj_brush = QtGui.QBrush(globals_.theme.color('overview_object'))
        self.view_brush = QtGui.QBrush(globals_.theme.color('overview_zone_fill'))
        self.view = QtCore.QRectF()
        self.sprite_brush = QtGui.QBrush(globals_.theme.color('overview_sprite'))
        self.entrance_brush = QtGui.QBrush(globals_.theme.color('overview_entrance'))
        self.location_brush = QtGui.QBrush(globals_.theme.color('overview_location_fill'))
        self.path_brush = QtGui.QBrush(globals_.theme.color('overview_path'))

        self.reset()

        self.pos_x_locator = 0
        self.pos_y_locator = 0
        self.height_locator = 50
        self.width_locator = 80
        self.main_window_scale = 1

    def reset(self):
        """
        Resets the max and scale variables
        """
        self.max_x = 100
        self.max_y = 40
        self.rescale()

    def mouseMoveEvent(self, a0):
        """
        Handles mouse movement over the widget
        """
        super().mouseMoveEvent(a0)
        if a0 is not None:
            if a0.buttons() == QtCore.Qt.MouseButton.LeftButton:
                self.moved.emit(a0.pos().x() * self.pos_mult, a0.pos().y() * self.pos_mult)

    def mousePressEvent(self, a0):
        """
        Handles mouse pressing events over the widget
        """
        super().mouseMoveEvent(a0)
        if a0 is not None:
            if a0.button() == QtCore.Qt.MouseButton.LeftButton:
                self.moved.emit(a0.pos().x() * self.pos_mult, a0.pos().y() * self.pos_mult)

    def paintEvent(self, a0):
        """
        Paints the level overview widget
        """
        if not hasattr(globals_.Area, 'layers'):
            # Fixes race condition where this widget is painted after
            # the level is created, but before it's loaded
            return

        if a0 is None:
            return

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)

        self.calc_size()
        self.rescale()

        painter.fillRect(a0.rect(), self.bg_brush)
        painter.scale(self.scale, self.scale)

        transform = QtGui.QTransform() / 24

        b = self.view_brush
        color = globals_.theme.color('overview_zone_lines')
        if color is not None:
            painter.setPen(QtGui.QPen(color, 1))

        for zone in globals_.Area.zones:
            rect = transform.mapRect(zone.sceneBoundingRect())
            painter.fillRect(rect, b)
            painter.drawRect(rect)

        b = self.obj_brush

        for layer in globals_.Area.layers:
            for obj in layer:
                painter.fillRect(obj.LevelRect, b)

        b = self.sprite_brush

        for sprite in globals_.Area.sprites:
            painter.fillRect(sprite.LevelRect, b)

        b = self.entrance_brush

        for ent in globals_.Area.entrances:
            painter.fillRect(ent.LevelRect, b)

        b = self.location_brush
        color = globals_.theme.color('overview_location_lines')
        if color is not None:
            painter.setPen(QtGui.QPen(color, 1))

        for location in globals_.Area.locations:
            rect = transform.mapRect(location.sceneBoundingRect())
            painter.fillRect(rect, b)
            painter.drawRect(rect)

        b = self.path_brush

        for path in globals_.Area.paths:
            for node in path._nodes:
                rect = transform.mapRect(node.sceneBoundingRect())
                painter.fillRect(rect, b)

            # TODO: Draw the path lines

        color = globals_.theme.color('overview_viewbox')
        if color is not None:
            painter.setPen(QtGui.QPen(color, 1))

        scalar = 1 / (24 * self.main_window_scale)
        painter.drawRect(QtCore.QRectF(
            scalar * self.pos_x_locator, scalar * self.pos_y_locator,
            scalar * self.width_locator, scalar * self.height_locator
        ))

    def calc_size(self):
        """
        Calculates self.max_x and self.max_y
        """
        if globals_.Area.areanum == -1:
            # Fixes race condition where this widget's size is calculated
            # after the level is created, but before it's loaded
            self.max_x = 100
            self.max_y = 40
            return

        transform = QtGui.QTransform() / 24
        rect = QtCore.QRectF()

        for zone in globals_.Area.zones:
            rect |= transform.mapRect(zone.sceneBoundingRect())

        for layer in globals_.Area.layers:
            for obj in layer:
                rect |= obj.LevelRect

        for sprite in globals_.Area.sprites:
            rect |= sprite.LevelRect

        for ent in globals_.Area.entrances:
            rect |= ent.LevelRect

        for location in globals_.Area.locations:
            rect |= transform.mapRect(location.sceneBoundingRect())

        for path in globals_.Area.paths:
            for node in path._nodes:
                rect |= node.LevelRect

        _, _, self.max_x, self.max_y = rect.getCoords()

    def rescale(self):
        """
        Calculates self.scale and self.pos_mult.
        """
        x_scale = self.width() / (self.max_x + 45)
        y_scale = self.height() / (self.max_y + 25)

        self.scale = max(0.002, min(x_scale, y_scale))
        self.pos_mult = 24 / self.scale
