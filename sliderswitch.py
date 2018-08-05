from PyQt5 import QtCore, QtWidgets, QtGui

# inspired by: https://stackoverflow.com/a/38102598
class QSliderSwitch(QtWidgets.QAbstractButton):
    """
    A slider switch button
    """
    Horizontal = 0
    Vertical = 1

    def __init__(self, direction = Horizontal, brush = QtGui.QColor("#009688"), parent = None):
        """
        Creates the slider switch
        """

        QtWidgets.QAbstractButton.__init__(self)

        self._direction = direction
        self._height = 24
        self._opacity = 0.0
        self._switch = False
        self._margin = 3
        self._thumb = QtGui.QColor("#D5D5D5")
        self._anim = QtCore.QPropertyAnimation(self, b"offset", self)

        self.setOffset(2 * self._margin)
        self._y = self._height / 2

        if isinstance(brush, str):
            # it's a colour hex-string, so convert it to s QColor
            brush = QtGui.QColor(brush)

        self.setBrush(brush)

        self.setSizePolicy(QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
            QtWidgets.QSizePolicy.PushButton
        ))

    def getBrush(self):
        """
        Returns the brush
        """
        return self._brush

    def setBrush(self, brush):
        """
        Sets the brush
        """
        self._brush = brush

    def getOffset(self):
        """
        Returns the offset
        """
        return self._x

    def setOffset(self, offset):
        """
        Sets the offset
        """
        self._x = offset
        self.update()

    offset = QtCore.pyqtProperty(int, fset=setOffset)
    brush = QtCore.pyqtProperty(QtGui.QBrush, fset=setBrush)

    # protected:

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setPen(QtCore.Qt.NoPen)

        if self._direction == QSliderSwitch.Horizontal:
            # rotate 90 degrees to the right
            p.rotate(360 - 90)
            # move down by the height of the slider
            p.translate(- (self._height + 3 * self._margin), 0)

        if self.isEnabled():
            if self._switch:
                p.setBrush(self.getBrush())
                p.setOpacity(0.5)
            else:
                p.setBrush(QtGui.QColor("#000000"))
                p.setOpacity(0.38)

            p.setRenderHint(QtGui.QPainter.Antialiasing, True)

            # track
            p.drawRect(
                self._margin, self._margin,
                self._height + 2 * self._margin, 2 * self._height + 2 * self._margin
            )

            # knob
            p.setBrush(self._thumb)
            p.setOpacity(1.0)

            p.drawRect(
                2 * self._margin, self.getOffset(),
                self._height, self._height
            )

        else:
            p.setBrush(QtCore.Qt.Black)
            p.setOpacity(0.12)
            p.drawRect(QtCore.QRect(
                self._margin, self._margin,
                self.width() - 2 * self._margin, self.height() - 2 * self._margin
            ))

            p.setBrush(QtGui.QColor("#BDBDBD"))
            p.setOpacity(1.0)
            p.drawRect(QtCore.QRect(
                self.getOffset(), 2 * self._margin,
                self._height, self._height
            ))

    def mouseReleaseEvent(self, event):
        if event.button() & QtCore.Qt.LeftButton:
            self._switch = not self._switch
            self.startAnimation()

        QtWidgets.QAbstractButton.mouseReleaseEvent(self, event)

    def startAnimation(self):
        """
        Starts the animation of the button
        """
        if self._switch:
            self._thumb = self._brush
            self._anim.setStartValue(2 * self._margin)
            self._anim.setEndValue(2 * self._margin + self._height)
        else:
            self._thumb = QtGui.QBrush(QtGui.QColor("#D5D5D5"))
            self._anim.setStartValue(self.getOffset())
            self._anim.setEndValue(2 * self._margin)

        self._anim.setDuration(120)
        self._anim.start()

    def enterEvent(self, event):
        self.setCursor(QtCore.Qt.PointingHandCursor)
        QtWidgets.QAbstractButton.enterEvent(self, event)

    def sizeHint(self):
        if self._direction == QSliderSwitch.Horizontal:
            return QtCore.QSize(4 * self._margin + 2 * self._height, 4 * self._margin + self._height)

        return QtCore.QSize(4 * self._margin + self._height, 4 * self._margin + 2 * self._height)

    def getValue(self):
        return self._switch

    def setValue(self, value):
        new = bool(value)
        if self._switch == new:
            return

        self._switch = new

        self.startAnimation()
        self.update()
