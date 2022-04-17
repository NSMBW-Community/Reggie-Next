import math
import pickletools

from PyQt5 import QtCore, QtGui, QtWidgets

import globals_
from levelitems import ListWidgetItem_SortsByOther, PathItem, CommentItem, SpriteItem, EntranceItem, LocationItem, ObjectItem, PathEditorLineItem
from dirty import SetDirty

class LevelScene(QtWidgets.QGraphicsScene):
    """
    GraphicsScene subclass for the level scene
    """

    def __init__(self, *args):
        QtWidgets.QGraphicsScene.__init__(self, *args)
        self.setBackgroundBrush(QtGui.QBrush(globals_.theme.color('bg')))

    def drawBackground(self, painter, rect):
        """
        Draws all visible tiles
        """
        QtWidgets.QGraphicsScene.drawBackground(self, painter, rect)
        if not hasattr(globals_.Area, 'layers'): return

        drawrect = QtCore.QRectF(rect.x() / 24, rect.y() / 24, rect.width() / 24 + 1, rect.height() / 24 + 1)
        isect = drawrect.intersects

        layer0 = []
        layer1 = []
        layer2 = []

        x1 = 1024
        y1 = 512
        x2 = 0
        y2 = 0

        # iterate through each object
        funcs = [layer0.append, layer1.append, layer2.append]
        show = [globals_.Layer0Shown, globals_.Layer1Shown, globals_.Layer2Shown]
        for layer, add, process in zip(globals_.Area.layers, funcs, show):
            if not process:
                continue

            for item in layer:
                if not isect(item.LevelRect):
                    continue

                add(item)
                x1 = min(x1, item.objx)
                x2 = max(x2, item.objx + item.width)
                y1 = min(y1, item.objy)
                y2 = max(y2, item.objy + item.height)

        width = x2 - x1
        height = y2 - y1

        # Assigning global variables to local variables for performance
        tiles = globals_.Tiles
        odefs = globals_.ObjectDefinitions
        unkn_tile = globals_.Overrides[globals_.OVERRIDE_UNKNOWN].getCurrentTile()

        # create and draw the tilemaps
        for layer_idx, layer in enumerate([layer2, layer1, layer0]):
            if not layer:
                continue

            tmap = [[None] * width for _ in range(height)]

            for item in layer:
                startx = item.objx - x1
                desty = item.objy - y1

                if odefs[item.tileset] is None or \
                        odefs[item.tileset][item.type] is None:
                    # This is an unknown object, so place -1 in the tile map.
                    for i, row in enumerate(item.objdata, desty):
                        destrow = tmap[i]
                        for j in range(startx, startx + len(row)):
                            destrow[j] = -1

                    continue

                # This is not an unkown object, so update the tile map normally.
                for i, row in enumerate(item.objdata, desty):
                    destrow = tmap[i]
                    for j, tile in enumerate(row, startx):
                        if tile > 0:
                            destrow[j] = tile

            painter.save()
            painter.translate(x1 * 24, y1 * 24)

            desty = -24
            for row in tmap:
                desty += 24
                destx = -24
                for tile in row:
                    destx += 24
                    if tile == -1:
                        # Draw unknown tiles
                        painter.drawPixmap(destx, desty, unkn_tile)
                    elif tile is not None:
                        # Only show collisions on layer 1 (i.e. layer_idx == 1)
                        pixmap = tiles[tile].getCurrentTile(layer_idx == 1)
                        painter.drawPixmap(destx, desty, pixmap)

            painter.restore()

    def getMainWindow(self):
        return globals_.mainWindow


class LevelViewWidget(QtWidgets.QGraphicsView):
    """
    QGraphicsView subclass for the level view
    """
    PositionHover = QtCore.pyqtSignal(int, int)
    FrameSize = QtCore.pyqtSignal(int, int)
    repaint = QtCore.pyqtSignal()
    dragstamp = False

    def __init__(self, scene, parent):
        """
        Constructor
        """
        super(LevelViewWidget, self).__init__(scene, parent)

        self.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setMouseTracking(True)
        self.YScrollBar = QtWidgets.QScrollBar(QtCore.Qt.Vertical, parent)
        self.XScrollBar = QtWidgets.QScrollBar(QtCore.Qt.Horizontal, parent)
        self.setVerticalScrollBar(self.YScrollBar)
        self.setHorizontalScrollBar(self.XScrollBar)

        short_HOME = QtWidgets.QShortcut(QtGui.QKeySequence.MoveToStartOfLine, self.XScrollBar)
        short_HOME.activated.connect(lambda: self.XScrollBar.setValue(self.XScrollBar.value() - self.XScrollBar.pageStep()))

        short_END = QtWidgets.QShortcut(QtGui.QKeySequence.MoveToEndOfLine, self.XScrollBar)
        short_END.activated.connect(lambda: self.XScrollBar.setValue(self.XScrollBar.value() + self.XScrollBar.pageStep()))

        self.currentobj = None
        self.lastCursorPosForMidButtonScroll = None
        self.cursorEdgeScrollTimer = None

    def mousePressEvent(self, event):
        """
        Overrides mouse pressing events if needed
        """

        if event.button() == QtCore.Qt.BackButton:
            self.xButtonScrollTimer = QtCore.QTimer()
            self.xButtonScrollTimer.timeout.connect(
                lambda: self.XScrollBar.setValue(self.XScrollBar.value() - self.XScrollBar.singleStep())
            )
            self.xButtonScrollTimer.start(100)

        elif event.button() == QtCore.Qt.ForwardButton:
            self.xButtonScrollTimer = QtCore.QTimer()
            self.xButtonScrollTimer.timeout.connect(
                lambda: self.XScrollBar.setValue(self.XScrollBar.value() + self.XScrollBar.singleStep())
            )
            self.xButtonScrollTimer.start(100)

        elif event.button() == QtCore.Qt.RightButton:
            clicked = globals_.mainWindow.view.mapToScene(event.x(), event.y())
            if clicked.x() < 0: clicked.setX(0)
            if clicked.y() < 0: clicked.setY(0)

            if 0 <= globals_.CurrentPaintType < 4 and globals_.CurrentObject != -1 and [globals_.Layer0Shown, globals_.Layer1Shown, globals_.Layer2Shown][globals_.CurrentLayer]:
                # paint an object
                clickedx = int(clicked.x() / 24)
                clickedy = int(clicked.y() / 24)

                obj = globals_.mainWindow.CreateObject(
                    globals_.CurrentPaintType, globals_.CurrentObject, globals_.CurrentLayer,
                    clickedx, clickedy
                )

                self.dragstamp = False
                self.currentobj = obj
                self.dragstartx = clickedx
                self.dragstarty = clickedy

            elif globals_.CurrentPaintType == 4 and globals_.CurrentSprite >= 0 and globals_.SpritesShown:
                # paint a sprite
                clickedx = int((clicked.x() - 12) / 12) * 8
                clickedy = int((clicked.y() - 12) / 12) * 8

                spr = globals_.mainWindow.CreateSprite(clickedx, clickedy, globals_.CurrentSprite)
                spr.UpdateDynamicSizing()

                self.dragstamp = False
                self.currentobj = spr
                self.dragstartx = clickedx
                self.dragstarty = clickedy

                self.scene().update()

            elif globals_.CurrentPaintType == 5:
                # paint an entrance
                clickedx = int((clicked.x() - 12) / 1.5)
                clickedy = int((clicked.y() - 12) / 1.5)

                ent = globals_.mainWindow.CreateEntrance(clickedx, clickedy)

                self.dragstamp = False
                self.currentobj = ent
                self.dragstartx = clickedx
                self.dragstarty = clickedy

            elif globals_.CurrentPaintType == 6 and globals_.PathsShown:
                # paint a path node
                clickedx = int((clicked.x() - 12) / 1.5)
                clickedy = int((clicked.y() - 12) / 1.5)
                plist = globals_.mainWindow.pathList
                selectedpn = None if not plist.selectedItems() else plist.selectedItems()[0]

                if selectedpn is None:
                    getids = [False for _ in range(256)]
                    getids[0] = True

                    for path in globals_.Area.paths:
                        getids[path._id] = True

                    if False not in getids:
                        # There already are 255 paths in this area. That should
                        # be enough. Also, the game doesn't allow path ids greater
                        # than 255 anyway, so just don't let the user create the
                        # path.
                        return

                    newpathid = getids.index(False)

                    from levelitems import Path

                    path = Path(newpathid, globals_.mainWindow.scene)
                    new_node = path.add_node(clickedx, clickedy)

                    new_node.listitem.setSelected(True)
                    new_node.setSelected(True)
                    new_node.positionChanged = globals_.mainWindow.HandlePathPosChange

                    globals_.Area.paths.append(path)

                else:
                    path_node = selectedpn.reference

                    path = path_node.path

                    if globals_.InsertPathNode:
                        idx = path.get_index(path_node) + 1
                    else:
                        idx = len(path)

                    new_node = path.add_node(clickedx, clickedy, index=idx)
                    new_node.positionChanged = globals_.mainWindow.HandlePathPosChange

                    # The path length changed, so update the editor's maximums
                    globals_.mainWindow.pathEditor.UpdatePathLength()

                self.dragstamp = False
                self.currentobj = new_node
                self.dragstartx = clickedx
                self.dragstarty = clickedy

                SetDirty()

            elif globals_.CurrentPaintType == 7 and globals_.LocationsShown:
                # paint a location
                clickedx = int(clicked.x() / 1.5)
                clickedy = int(clicked.y() / 1.5)

                loc = globals_.mainWindow.CreateLocation(clickedx, clickedy)

                self.dragstamp = False
                self.currentobj = loc
                self.dragstartx = clickedx
                self.dragstarty = clickedy

            elif globals_.CurrentPaintType == 8:
                # paint a stamp

                clickedx = int(clicked.x() / 1.5)
                clickedy = int(clicked.y() / 1.5)

                stamp = globals_.mainWindow.stampChooser.currentlySelectedStamp()
                if stamp is not None:
                    objs = globals_.mainWindow.placeEncodedObjects(stamp.ReggieClip, False, clickedx, clickedy)

                    for obj in objs:
                        obj.dragstartx = obj.objx
                        obj.dragstarty = obj.objy
                        obj.update()

                    globals_.mainWindow.scene.update()

                    self.dragstamp = True
                    self.dragstartx = clickedx
                    self.dragstarty = clickedy
                    self.currentobj = objs

                    SetDirty()

            elif globals_.CurrentPaintType == 9 and globals_.CommentsShown:
                # paint a comment
                clickedx = int((clicked.x() - 12) / 1.5)
                clickedy = int((clicked.y() - 12) / 1.5)

                com = CommentItem(clickedx, clickedy, '')
                mw = globals_.mainWindow
                com.positionChanged = mw.HandleComPosChange
                com.textChanged = mw.HandleComTxtChange
                mw.scene.addItem(com)
                com.setVisible(globals_.CommentsShown)

                clist = mw.commentList
                com.listitem = QtWidgets.QListWidgetItem()
                clist.addItem(com.listitem)

                globals_.Area.comments.append(com)

                self.dragstamp = False
                self.currentobj = com
                self.dragstartx = clickedx
                self.dragstarty = clickedy

                globals_.mainWindow.SaveComments()

                com.UpdateListItem()

                SetDirty()

            event.accept()

        elif event.button() == QtCore.Qt.MidButton:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self.lastCursorPosForMidButtonScroll = event.pos()
            QtWidgets.QGraphicsView.mousePressEvent(self, event)

        elif (event.button() == QtCore.Qt.LeftButton) and (QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier):
            mw = globals_.mainWindow

            pos = mw.view.mapToScene(event.x(), event.y())
            addsel = mw.scene.items(pos)
            for i in addsel:
                if i.flags() & i.ItemIsSelectable:
                    i.setSelected(not i.isSelected())
                    break

        else:
            QtWidgets.QGraphicsView.mousePressEvent(self, event)

        globals_.mainWindow.levelOverview.update()

    def resizeEvent(self, event):
        """
        Catches resize events
        """
        self.FrameSize.emit(event.size().width(), event.size().height())
        event.accept()
        QtWidgets.QGraphicsView.resizeEvent(self, event)

    def mouseMoveEvent(self, event):
        """
        Overrides mouse movement events if needed
        """
        pos = self.mapToScene(event.pos())
        if pos.x() < 0: pos.setX(0)
        if pos.y() < 0: pos.setY(0)
        self.PositionHover.emit(int(pos.x()), int(pos.y()))

        if ((event.buttons() & (QtCore.Qt.MouseButton.LeftButton | QtCore.Qt.MouseButton.RightButton))
                and not self.cursorEdgeScrollTimer):
            # We set this up here instead of in mousePressEvent because
            # otherwise the view would jerk to one side if you clicked
            # near its edge. This way, it'll only scroll if you click
            # and drag.
            self.cursorEdgeScrollTimer = QtCore.QTimer()
            self.cursorEdgeScrollTimer.timeout.connect(self.scrollIfCursorNearEdge)
            self.cursorEdgeScrollTimer.start(1000 // 60)  # ~ 60 fps

        if self.updatePaintDraggedItems():
            event.accept()

        elif event.buttons() == QtCore.Qt.MouseButton.MiddleButton and self.lastCursorPosForMidButtonScroll is not None:
            # https://stackoverflow.com/a/15785851
            delta = event.pos() - self.lastCursorPosForMidButtonScroll
            self.XScrollBar.setValue(self.XScrollBar.value() + (delta.x() if self.isRightToLeft() else -delta.x()))
            self.YScrollBar.setValue(self.YScrollBar.value() - delta.y())
            self.lastCursorPosForMidButtonScroll = event.pos()

        else:
            QtWidgets.QGraphicsView.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        """
        Overrides mouse release events if needed
        """
        if event.button() in (QtCore.Qt.BackButton, QtCore.Qt.ForwardButton):
            self.xButtonScrollTimer.stop()
            return

        if event.button() == QtCore.Qt.RightButton:
            self.currentobj = None
        elif event.button() == QtCore.Qt.MidButton:
            self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)

        if self.cursorEdgeScrollTimer:
            self.cursorEdgeScrollTimer.stop()
            self.cursorEdgeScrollTimer = None

        QtWidgets.QGraphicsView.mouseReleaseEvent(self, event)

    def updatePaintDraggedItems(self):
        """Update items that are being paint-dragged (painted with
        right-click, and dragged while it's still held down). Returns
        True if any items are being paint-dragged, False otherwise"""
        if globals_.app.mouseButtons() != QtCore.Qt.MouseButton.RightButton or self.currentobj is None:
            return False

        pos = self.mapToScene(self.mapFromGlobal(QtGui.QCursor.pos()))
        obj = self.currentobj

        if not self.dragstamp:
            # possibly a small optimization
            type_obj = ObjectItem
            type_spr = SpriteItem
            type_ent = EntranceItem
            type_loc = LocationItem
            type_path = PathItem
            type_com = CommentItem

            # iterate through the objects if there's more than one
            if isinstance(self.currentobj, (list, tuple)):
                objlist = self.currentobj
            else:
                objlist = (self.currentobj,)

            for obj in objlist:

                if isinstance(obj, type_obj):
                    # Resize the current object. The new object should fill a
                    # rectangle, with two diagonal corners at self.dragstart and
                    # pos / 24. This rectangle should contain self.dragstart.
                    dsx = self.dragstartx
                    dsy = self.dragstarty
                    clicked = pos / 24

                    clickx = max(0, clicked.x())
                    clicky = max(0, clicked.y())

                    # calculate rectangle
                    x = int(min(dsx, clickx))
                    width = max(1, int(max(dsx, clickx) + 1 - x))

                    y = int(min(dsy, clicky))
                    height = max(1, int(max(dsy, clicky) + 1 - y))

                    # Check if the tile has been moved to full size already. If
                    # not, don't change the tile's position / size.
                    if not obj.wasExtended:
                        obj.wasExtended = (width >= obj.width) and (height >= obj.height)
                        continue

                    # if the position changed, set the new one
                    if obj.objx != x or obj.objy != y:
                        obj.objx = x
                        obj.objy = y
                        obj.setPos(x * 24, y * 24)
                        globals_.mainWindow.levelOverview.update()

                    # if the size changed, recache it and update the area
                    if obj.width != width or obj.height != height:
                        obj.updateObjCacheWH(width, height)
                        obj.width = width
                        obj.height = height

                        oldrect = obj.BoundingRect
                        oldrect.translate(obj.objx * 24, obj.objy * 24)
                        newrect = QtCore.QRectF(obj.x(), obj.y(), obj.width * 24, obj.height * 24)
                        updaterect = oldrect.united(newrect)

                        obj.UpdateRects()
                        obj.scene().update(updaterect)
                        globals_.mainWindow.levelOverview.update()

                elif isinstance(obj, type_loc):
                    # resize/move the current location
                    change = obj.dragResize(pos, self.dragstartx, self.dragstarty)

                    if change:  # Update the location editor
                        globals_.mainWindow.locationEditor.setLocation(obj)
                        globals_.mainWindow.levelOverview.update()

                elif isinstance(obj, type_spr):
                    # move the created sprite
                    clickedx = int((pos.x() - 12) / 1.5)
                    clickedy = int((pos.y() - 12) / 1.5)

                    if obj.objx != clickedx or obj.objy != clickedy:
                        obj.setNewObjPos(clickedx, clickedy)
                        obj.ImageObj.positionChanged()
                        obj.UpdateListItem()
                        globals_.mainWindow.levelOverview.update()

                elif isinstance(obj, (type_ent, type_path, type_com)):
                    # move the created entrance/path/comment
                    clickedx = int((pos.x() - 12) / 1.5)
                    clickedy = int((pos.y() - 12) / 1.5)

                    if obj.objx != clickedx or obj.objy != clickedy:
                        obj.objx = clickedx
                        obj.objy = clickedy
                        obj.setPos(int(clickedx * 1.5), int(clickedy * 1.5))

                        if isinstance(obj, type_path):
                            obj.path.node_moved(obj)

                        obj.UpdateListItem()
                        globals_.mainWindow.levelOverview.update()

        else:
            # The user is dragging a stamp - many objects.

            # possibly a small optimization
            type_obj = ObjectItem
            type_spr = SpriteItem

            # iterate through the objects if there's more than one
            if isinstance(self.currentobj, list) or isinstance(self.currentobj, tuple):
                objlist = self.currentobj
            else:
                objlist = (self.currentobj,)

            changex = pos.x() - (self.dragstartx * 1.5)
            changey = pos.y() - (self.dragstarty * 1.5)
            changexobj = int(changex / 24)
            changeyobj = int(changey / 24)
            changexspr = changex * 2 / 3
            changeyspr = changey * 2 / 3

            for obj in objlist:
                if isinstance(obj, type_obj):
                    # move the current object
                    newx = int(obj.dragstartx + changexobj)
                    newy = int(obj.dragstarty + changeyobj)

                    if obj.objx != newx or obj.objy != newy:
                        obj.objx = newx
                        obj.objy = newy
                        obj.setPos(newx * 24, newy * 24)
                        obj.UpdateRects()

                elif isinstance(obj, type_spr):
                    # move the created sprite

                    newx = int(obj.dragstartx + changexspr)
                    newy = int(obj.dragstarty + changeyspr)

                    if obj.objx != newx or obj.objy != newy:
                        obj.setNewObjPos(newx, newy)
                        obj.ImageObj.positionChanged()

            self.scene().update()
            globals_.mainWindow.levelOverview.update()

    def scrollIfCursorNearEdge(self):
        """Scroll the view if the cursor is dragging and near the edge"""
        pos = self.mapFromGlobal(QtGui.QCursor.pos())

        distFromL = pos.x()
        distFromR = self.width() - self.YScrollBar.width() - pos.x()
        distFromT = pos.y()
        distFromB = self.height() - self.XScrollBar.height() - pos.y()

        EDGE_PAD = 60
        SCALE_FACTOR = 0.3

        scrollDx = scrollDy = 0

        if distFromL < EDGE_PAD:
            scrollDx = -(EDGE_PAD - distFromL) * SCALE_FACTOR
        if distFromR < EDGE_PAD:
            scrollDx = (EDGE_PAD - distFromR) * SCALE_FACTOR
        if distFromT < EDGE_PAD:
            scrollDy = -(EDGE_PAD - distFromT) * SCALE_FACTOR
        if distFromB < EDGE_PAD:
            scrollDy = (EDGE_PAD - distFromB) * SCALE_FACTOR

        if scrollDx:
            self.XScrollBar.setValue(int(self.XScrollBar.value() + scrollDx))
        if scrollDy:
            self.YScrollBar.setValue(int(self.YScrollBar.value() + scrollDy))

        self.updatePaintDraggedItems()

    def wheelEvent(self, event):
        """
        Handle wheel events for zooming in/out
        """
        if event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                globals_.mainWindow.HandleZoomIn(towardsCursor=True)
            else:
                globals_.mainWindow.HandleZoomOut(towardsCursor=True)

        else:
            super().wheelEvent(event)

    def paintEvent(self, e):
        """
        Handles paint events and fires a signal
        """
        self.repaint.emit()
        QtWidgets.QGraphicsView.paintEvent(self, e)

    def drawForeground(self, painter, rect):
        """
        Draws a foreground grid and other stuff
        """
        # Draws a foreground grid
        if globals_.GridType is None: return

        Zoom = globals_.mainWindow.ZoomLevel
        drawLine = painter.drawLine
        GridColor = globals_.theme.color('grid')

        if globals_.GridType == 'grid':  # draw a classic grid
            startx = rect.x()
            startx -= (startx % 24)
            endx = startx + rect.width() + 24

            starty = rect.y()
            starty -= (starty % 24)
            endy = starty + rect.height() + 24

            x = startx
            while x <= endx:
                if x % 192 == 0:
                    painter.setPen(QtGui.QPen(GridColor, 2, QtCore.Qt.DashLine))
                    drawLine(QtCore.QPointF(x, starty), QtCore.QPointF(x, endy))
                elif x % 96 == 0 and Zoom >= 25:
                    painter.setPen(QtGui.QPen(GridColor, 1, QtCore.Qt.DashLine))
                    drawLine(QtCore.QPointF(x, starty), QtCore.QPointF(x, endy))
                elif Zoom >= 50:
                    painter.setPen(QtGui.QPen(GridColor, 1, QtCore.Qt.DotLine))
                    drawLine(QtCore.QPointF(x, starty), QtCore.QPointF(x, endy))
                x += 24

            y = starty
            while y <= endy:
                if y % 192 == 0:
                    painter.setPen(QtGui.QPen(GridColor, 2, QtCore.Qt.DashLine))
                    drawLine(QtCore.QPointF(startx, y), QtCore.QPointF(endx, y))
                elif y % 96 == 0 and Zoom >= 25:
                    painter.setPen(QtGui.QPen(GridColor, 1, QtCore.Qt.DashLine))
                    drawLine(QtCore.QPointF(startx, y), QtCore.QPointF(endx, y))
                elif Zoom >= 50:
                    painter.setPen(QtGui.QPen(GridColor, 1, QtCore.Qt.DotLine))
                    drawLine(QtCore.QPointF(startx, y), QtCore.QPointF(endx, y))
                y += 24

        else:  # draw a checkerboard
            L = 0.2
            D = 0.1  # Change these values to change the checkerboard opacity

            Light = QtGui.QColor(GridColor)
            Dark = QtGui.QColor(GridColor)
            Light.setAlpha(int(Light.alpha() * L))
            Dark.setAlpha(int(Dark.alpha() * D))

            size = 24 if Zoom >= 50 else 96

            board = QtGui.QPixmap(8 * size, 8 * size)
            board.fill(QtGui.QColor(0, 0, 0, 0))
            p = QtGui.QPainter(board)
            p.setPen(QtCore.Qt.NoPen)

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

def DecodeOldReggieInfo(data, validKeys):
    """
    Decode the provided level info data into a dictionary, which will
    have only the keys specified. Raises an exception if the data can't
    be parsed.
    """
    # The idea here is that we implement just enough of the pickle
    # protocol (v2) to be able to parse the dictionaries that past
    # Reggies have pickled, even if PyQt4 isn't available.
    #
    # We keep track of the stack and memo, just enough to figure out
    # in what order the strings are pushed to the stack. (We need to
    # implement the memo because default level info uses memoization to
    # avoid encoding the '-' string more than once.) Then we filter out
    # 'PyQt4.QtCore' and 'QString'. Assuming nobody's crazy enough to
    # use those as actual level info field values, that should leave us
    # with exactly 12 strings (6 field names and 6 fields). Then we just
    # put the dictionary together in the same way as the SETITEMS pickle
    # instruction, and we're done.

    # Figure out in what order strings are pushed to the pickle stack
    stack = []
    memo = {}
    for inst, arg, _ in pickletools.genops(data):
        if inst.name in ['SHORT_BINSTRING', 'BINSTRING', 'BINUNICODE']:
            stack.append(arg)
        elif inst.name == 'GLOBAL':
            # In practice, this is used to push sip._unpickle_type,
            # which then gets BINGET'd over and over. So we have to take
            # it into account, or else we get confused and end up
            # pushing some random string to the stack repeatedly instead
            stack.append(None)
        elif inst.name == 'BINPUT' and stack:
            memo[arg] = stack[-1]
        elif inst.name == 'BINGET' and arg in memo:
            stack.append(memo[arg])

    # Filter out uninteresting strings and check that the length is right
    strings = [s for s in stack if s not in {'PyQt4.QtCore', 'QString', None}]
    if len(strings) != 12:
        raise ValueError('Wrong number of strings in level metadata (%d)' % len(strings))

    # Convert e.g. [a, b, c, d, e, f] -> {a: b, c: d, e: f}
    # https://stackoverflow.com/a/12739974
    it = iter(strings)
    levelinfo = dict(zip(it, it))

    # Double-check that the keys are as expected, and return
    if set(levelinfo) != validKeys:
        raise ValueError('Wrong keys in level metadata: ' + str(set(levelinfo)))

    return levelinfo
