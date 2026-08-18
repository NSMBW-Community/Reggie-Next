from PyQt6 import QtCore, QtGui

from reggie import globals_


class Stamp:
    """
    Class that represents a stamp in the list
    """

    def __init__(self, ReggieClip=None, Name=''):
        """
        Initializes the stamp
        """

        self.ReggieClip = ReggieClip
        self.Name = Name
        self.Icon = self.render()

    def renderPreview(self):
        """
        Renders the stamp preview
        """

        minX, minY, maxX, maxY = 24576, 12288, 0, 0

        layers, sprites, _, _, _, _ = globals_.mainWindow.getEncodedObjects(self.ReggieClip, False)

        # Go through the sprites and find the maxs and mins
        for spr in sprites:
            br = spr.getFullRect()

            x1 = br.topLeft().x()
            y1 = br.topLeft().y()
            x2 = x1 + br.width()
            y2 = y1 + br.height()

            if x1 < minX: minX = x1
            if x2 > maxX: maxX = x2
            if y1 < minY: minY = y1
            if y2 > maxY: maxY = y2

        # Go through the objects and find the maxs and mins
        for layer in layers:
            for obj in layer:
                x1 = (obj.objx * 24)
                x2 = x1 + (obj.width * 24)
                y1 = (obj.objy * 24)
                y2 = y1 + (obj.height * 24)

                if x1 < minX: minX = x1
                if x2 > maxX: maxX = x2
                if y1 < minY: minY = y1
                if y2 > maxY: maxY = y2

        # Calculate offset amounts (snap to 24x24 increments)
        offsetX = int(minX // 24) * 24
        offsetY = int(minY // 24) * 24
        drawOffsetX = offsetX - minX
        drawOffsetY = offsetY - minY

        # Go through the things again and shift them by the offset amount
        for spr in sprites:
            spr.objx -= offsetX / 1.5
            spr.objy -= offsetY / 1.5
        for layer in layers:
            for obj in layer:
                obj.objx -= offsetX // 24
                obj.objy -= offsetY // 24

        # Calculate the required pixmap size
        pixmapSize = (maxX - minX, maxY - minY)

        # Create the pixmap, and a painter
        pix = QtGui.QPixmap(int(pixmapSize[0]), int(pixmapSize[1]))
        pix.fill(QtCore.Qt.GlobalColor.transparent)
        painter = QtGui.QPainter(pix)
        painter.setRenderHint(painter.RenderHint.Antialiasing)

        # Paint all objects
        objw, objh = int(pixmapSize[0] // 24) + 1, int(pixmapSize[1] // 24) + 1
        for layer in reversed(layers):
            tmap = []
            for i in range(objh):
                tmap.append([-1] * objw)
            for obj in layer:
                startx = int(obj.objx)
                starty = int(obj.objy)

                desty = starty
                for row in obj.objdata:
                    destrow = tmap[desty]
                    destx = startx
                    for tile in row:
                        if tile > 0:
                            destrow[destx] = tile
                        destx += 1
                    desty += 1

                painter.save()
                desty = 0
                for row in tmap:
                    destx = 0
                    for tile in row:
                        if tile > 0:
                            if globals_.Tiles[tile] is None: continue
                            r = globals_.Tiles[tile].main
                            painter.drawPixmap(int(destx + drawOffsetX), int(desty + drawOffsetY), r)
                        destx += 24
                    desty += 24
                painter.restore()

        # Paint all sprites
        for spr in sprites:
            offx = ((spr.objx + spr.ImageObj.xOffset) * 1.5) + drawOffsetX
            offy = ((spr.objy + spr.ImageObj.yOffset) * 1.5) + drawOffsetY

            painter.save()
            painter.translate(offx, offy)

            spr.paint(painter, None, None, True)

            painter.restore()

            # Paint any auxiliary things
            for aux in spr.ImageObj.aux:
                painter.save()
                painter.translate(
                    offx + aux.x(),
                    offy + aux.y(),
                )

                aux.paint(painter, None, None)

                painter.restore()

        # End painting
        painter.end()
        del painter

        # Scale it
        maxW, maxH = 96, 96
        w, h = pix.width(), pix.height()
        if w > h and w > maxW:
            pix = pix.scaledToWidth(maxW)
        elif h > w and h > maxH:
            pix = pix.scaledToHeight(maxH)

        # Return it
        return pix

    def render(self):
        """
        Renders the stamp icon, preview AND text
        """

        # Get the preview icon
        prevIcon = self.renderPreview()

        # Calculate the total size of the icon
        textSize = self.calculateTextSize(self.Name)
        totalWidth = max(prevIcon.width(), textSize.width())
        totalHeight = prevIcon.height() + 2 + textSize.height()

        # Make a pixmap and painter
        pix = QtGui.QPixmap(int(totalWidth), int(totalHeight))
        pix.fill(QtCore.Qt.GlobalColor.transparent)
        painter = QtGui.QPainter(pix)

        # Draw the preview
        iconXOffset = (totalWidth - prevIcon.width()) / 2
        painter.drawPixmap(int(iconXOffset), 0, prevIcon)

        # Draw the text
        textRect = QtCore.QRectF(0, prevIcon.height() + 2, totalWidth, textSize.height())
        painter.setFont(QtGui.QFont())
        painter.setPen(QtCore.Qt.GlobalColor.gray)
        painter.drawText(textRect, QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.TextFlag.TextWordWrap, self.Name)

        # Return the pixmap
        return pix

    @staticmethod
    def calculateTextSize(text):
        """
        Calculates the size of text. Crops to 96 pixels wide.
        """
        fontMetrics = QtGui.QFontMetrics(QtGui.QFont())
        fontRect = fontMetrics.boundingRect(QtCore.QRect(0, 0, 96, 48), QtCore.Qt.TextFlag.TextWordWrap, text)
        w, h = fontRect.width(), fontRect.height()
        return QtCore.QSizeF(min(w, 96), h)

    def update(self):
        """
        Updates the stamp icon
        """
        self.Icon = self.render()
