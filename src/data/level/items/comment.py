from PyQt6 import QtCore, QtGui, QtWidgets

import globals_
from src.data.level.items.basic import InstanceDefinition, LevelEditorItem
from src.ui.theme.reggie_theme import GetIcon, clipStr, setOverrideCursor


class InstanceDefinition_CommentItem(InstanceDefinition):
    """
    Definition of an instance of CommentItem
    """
    fieldNames = (
        'text',
    )

    @staticmethod
    def itemList():
        return globals_.Area.comments

    def createNew(self):
        return CommentItem(self.objx, self.objy, self.fields[0][1])


class CommentItem(LevelEditorItem):
    """
    Level editor item that represents a in-level comment
    """
    instanceDef = InstanceDefinition_CommentItem
    BoundingRect = QtCore.QRectF(-8, -8, 48, 48)
    SelectionRect = QtCore.QRectF(-4, -4, 4, 4)
    Circle = QtCore.QRectF(0, 0, 32, 32)

    def __init__(self, x, y, text=''):
        """
        Creates a in-level comment
        """
        LevelEditorItem.__init__(self)
        if globals_.CursorMode != 0:
            self.setAcceptHoverEvents(True)
        zval = 50000
        self.zval = zval

        self.text = text

        self.objx = x
        self.objy = y
        self.listitem = None
        self.LevelRect = (QtCore.QRectF(self.objx / 16, self.objy / 16, 2.25, 2.25))

        self.setFlag(self.GraphicsItemFlag.ItemIsMovable, not globals_.CommentsFrozen)
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, not globals_.CommentsFrozen)

        globals_.DirtyOverride += 1
        self.setPos(int(x * 1.5), int(y * 1.5))
        globals_.DirtyOverride -= 1

        self.setZValue(zval + 1)
        self.UpdateTooltip()

        if globals_.mainWindow is None:
            return

        self.TextEdit = QtWidgets.QPlainTextEdit()
        self.TextEditProxy = globals_.mainWindow.scene.addWidget(self.TextEdit)
        if self.TextEditProxy is not None:
            self.TextEditProxy.setZValue(self.zval)
            self.TextEditProxy.setCursor(QtCore.Qt.CursorShape.IBeamCursor)
            self.TextEditProxy.boundingRect = lambda: QtCore.QRectF(0, 0, 4000, 4000)
        self.TextEdit.setVisible(False)
        self.TextEdit.setMaximumWidth(192)
        self.TextEdit.setMaximumHeight(128)
        self.TextEdit.setPlainText(self.text)
        self.TextEdit.textChanged.connect(self.handleTextChanged)
        self.reposTextEdit()

    def mousePressEvent(self, event):
        """
        Override the mouse press event to delegate it to the text edit
        if required. This ensures the user can select the first characters of the
        comment text.
        """
        if event is None:
            return

        # Also check the position to only allow clicks in the region that
        # overlaps with the text edit.
        if self.isSelected() and event.pos().x() > 22 and event.pos().y() > 15:
            event.ignore()
            return

        # We're not selected yet. Pass the event to the base class so we get
        # selected properly.
        LevelEditorItem.mousePressEvent(self, event)

    def UpdateTooltip(self):
        """
        For compatibility, just in case
        """
        self.setToolTip(globals_.trans.string('Comments', 1, '[x]', self.objx, '[y]', self.objy))

    def ListString(self):
        """
        Returns a string that can be used to describe the comment in a list
        """
        t = self.OneLineText()
        return globals_.trans.string('Comments', 0, '[x]', self.objx, '[y]', self.objy, '[text]', t)

    def OneLineText(self):
        """
        Returns the text of this comment in a format that can be written on one line
        """
        t = str(self.text)
        if not t.strip():
            t = globals_.trans.string('Comments', 3)

        if t is None:
            return ''

        while '\n\n' in t:
            t = t.replace('\n\n', '\n')

        new = globals_.trans.string('Comments', 2)
        if new is not None:
            t = t.replace('\n', new)

        f = None
        if self.listitem is not None:
            f = self.listitem.font()

        t2 = clipStr(t, 128, f)
        if t2 is not None:
            t = t2 + '...'

        return t

    def paint(self, painter, option, widget = ...):
        """
        Paints the comment
        """
        if not painter or not option or not globals_.mainWindow:
            return

        painter.setClipRect(option.exposedRect)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        if self.isSelected():
            painter.setBrush(QtGui.QBrush(globals_.theme.color('comment_fill_s')))
            p = QtGui.QPen(globals_.theme.color('comment_lines_s'))
            p.setWidth(3)
            painter.setPen(p)
        else:
            painter.setBrush(QtGui.QBrush(globals_.theme.color('comment_fill')))
            p = QtGui.QPen(globals_.theme.color('comment_lines'))
            p.setWidth(3)
            painter.setPen(p)

        if globals_.UseRoundedRectangles:
            painter.drawEllipse(self.Circle)
        else:
            painter.drawRect(self.Circle)

        if not self.isSelected():
            painter.setOpacity(.5)
        painter.drawPixmap(4, 4, GetIcon('comments', True).pixmap(24, 24))
        painter.setOpacity(1)

        # Set the text edit visibility
        try:
            shouldBeVisible = (len(globals_.mainWindow.scene.selectedItems()) == 1) and self.isSelected()
        except RuntimeError:
            shouldBeVisible = False
        try:
            self.TextEdit.setVisible(shouldBeVisible)
        except RuntimeError:
            # Sometimes Qt deletes my text edit.
            # Therefore, I need to make a new one.
            self.TextEdit = QtWidgets.QPlainTextEdit()
            self.TextEditProxy = globals_.mainWindow.scene.addWidget(self.TextEdit)
            if self.TextEditProxy is not None:
                self.TextEditProxy.setZValue(self.zval)
                self.TextEditProxy.setCursor(QtCore.Qt.CursorShape.IBeamCursor)
                self.TextEditProxy.boundingRect = lambda: QtCore.QRectF(0, 0, 4000, 4000)
            self.TextEdit.setMaximumWidth(192)
            self.TextEdit.setMaximumHeight(128)
            self.TextEdit.setPlainText(self.text)
            self.TextEdit.textChanged.connect(self.handleTextChanged)
            self.reposTextEdit()
            self.TextEdit.setVisible(shouldBeVisible)

        # Stop focusing on the textbox. Comments cannot be deleted
        # while the textbox is focused, which is rather annoying
        if not self.isSelected():
            # Stop selecting any highlighted text
            cursor = self.TextEdit.textCursor()
            cursor.clearSelection()
            self.TextEdit.setTextCursor(cursor)

            self.TextEdit.clearFocus()

    def handleTextChanged(self):
        """
        Handles the text being changed
        """
        self.text = str(self.TextEdit.toPlainText())
        if hasattr(self, 'textChanged'):
            self.textChanged(self)

    def reposTextEdit(self):
        """
        Repositions the text edit
        """
        if self.TextEditProxy is not None:
            self.TextEditProxy.setPos((self.objx * 3 / 2) + 24, (self.objy * 3 / 2) + 16)

    def handlePosChange(self, oldx, oldy):
        """
        Handles the position changing
        """
        self.reposTextEdit()

        # Manual scene update :(
        w = 192 + 24
        h = 128 + 24
        oldx *= 1.5
        oldy *= 1.5
        oldRect = QtCore.QRectF(oldx, oldy, w, h)
        scene = self.scene()
        if scene is not None:
            scene.update(oldRect)

    def delete(self):
        """
        Delete the comment from the level
        """
        if globals_.mainWindow is None:
            return

        comment_list = globals_.mainWindow.commentList

        globals_.mainWindow.UpdateFlag = True
        comment_list.takeItem(comment_list.row(self.listitem))
        globals_.mainWindow.UpdateFlag = False
        sel_model = comment_list.selectionModel()
        if sel_model is not None:
            sel_model.clearSelection()

        proxy = self.TextEditProxy
        if proxy is not None:
            proxy.setSelected(False)

        globals_.mainWindow.scene.removeItem(proxy)
        globals_.Area.comments.remove(self)

        scene = self.scene()
        if scene is not None:
            scene.update(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())

        globals_.mainWindow.SaveComments()
        setOverrideCursor(None)

    def hoverMoveEvent(self, event):
        LevelEditorItem.hoverMoveEvent(self, event)
        if (self.isSelected() or globals_.CursorMode == 2) and not globals_.CommentsFrozen:
            setOverrideCursor(QtCore.Qt.CursorShape.SizeAllCursor)

    def hoverLeaveEvent(self, event):
        LevelEditorItem.hoverLeaveEvent(self, event)
        setOverrideCursor(None)
