from collections.abc import Callable
from typing import Any, cast

from PyQt6 import QtCore, QtGui, QtWidgets

import actorlib
from data import globals_
from data.common.utils import clamp
from data.level.dirty import SetDirty
from data.level.items.basic import InstanceDefinition, LevelEditorItem
from data.level.items.object import ObjectItem
from data.level.items.zone import ZoneItem
from data.actor.actorfield.list import ListActorField
from data.actor.actorfield.actor_field import ActorField
from data.actor.actorfield.value import ValueActorField
from ui.actions.undo.move_item import MoveItemUndoAction
from ui.theme.reggie_theme import setOverrideCursor
from ui.widgets.actoreditor.propertydecoders.property_decoder import PropertyDecoder


class InstanceDefinition_ActorItem(InstanceDefinition):
    """
    Definition of an instance of ActorItem
    """
    fieldNames = (
        'type',
        'actordata',
    )

    @staticmethod
    def itemList() -> list['ActorItem']:
        return globals_.Area.actors

    def createNew(self) -> 'ActorItem':
        return ActorItem(self.fields[0][1], self.objx, self.objy, self.fields[1][1])


class ActorItem(LevelEditorItem):
    """
    Level editor item that represents an actor
    """
    instanceDef = InstanceDefinition_ActorItem
    BoundingRect = QtCore.QRectF(0, 0, 24, 24)
    SelectionRect = QtCore.QRectF(0, 0, 23, 23)

    def __init__(self, actor_num: int, x: float, y: float, data: bytes | bytearray) -> None:
        """
        Creates a actor with specific data
        """
        LevelEditorItem.__init__(self)
        self.setZValue(26000)
        if globals_.CursorMode != 0:
            self.setAcceptHoverEvents(True)

        self.font = globals_.NumberFont
        self.actor_num = actor_num
        self.objx = x
        self.objy = y
        self.actordata = data
        self.LevelRect = QtCore.QRectF(self.objx / 16, self.objy / 16, 1.5, 1.5)
        self.ChangingPos = False
        self.zoneID = -1

        self.ImageObj = actorlib.ActorImage(self)

        if 0 <= actor_num < globals_.NumActors:
            self.name = globals_.Actors[actor_num].name
        else:
            self.name = globals_.trans.string('Actors', 24)

        self.InitializeActor()

        self.setFlag(self.GraphicsItemFlag.ItemIsMovable, not globals_.ActorsFrozen)
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, not globals_.ActorsFrozen)

        globals_.DirtyOverride += 1
        if globals_.ActorImagesShown:
            self.setPos(
                (self.objx + self.ImageObj.xOffset) * 1.5,
                (self.objy + self.ImageObj.yOffset) * 1.5,
            )
        else:
            self.setPos(
                self.objx * 1.5,
                self.objy * 1.5,
            )
        globals_.DirtyOverride -= 1

    @staticmethod
    def CreateActor(x: float, y: float, id_: int | None = None, data: bytes | bytearray | None = None, add_to_scene: bool = True) -> 'ActorItem':
        """
        Creates and returns a new actor and makes sure it's added to the right
        lists if 'add_to_scene' is set.
        If 'id_' is not set, the currently selected actor id is used.
        If 'data' is not set, the current data of the default data editor is used.
        If 'data' is not set and the default data editor is configured for another
        actor id than the id of the actor that is created, a ValueError will
        be raised.
        """
        dummy = ActorItem(-1, -1, -1, b'')
        if globals_.mainWindow is None:
            return dummy

        if id_ is None:
            id_ = globals_.CurrentActor

        if data is None:
            if globals_.mainWindow.defaultDataEditor.actortype != id_:
                raise ValueError(f'The default data editor was configured for actor {globals_.mainWindow.defaultDataEditor.actortype} while trying to use data for actor {id_}')

            data = globals_.mainWindow.defaultDataEditor.data

        spr = ActorItem(id_, x, y, data)
        spr.positionChanged = ActorItem.position_changed

        if add_to_scene:
            # Check if actor data exists for this type
            if not (0 <= id_ < globals_.NumActors) or globals_.Actors[id_] is None:
                # Unknown actor, don't create
                return dummy

            globals_.mainWindow.palette_dock.actor_tab.actor_list.addActor(spr)
            globals_.mainWindow.palette_dock.actor_tab.actor_order_list.addActor(spr)
            globals_.Area.actors.append(spr)

            # Add the ids for the idtype count
            decoder = PropertyDecoder(ActorField())
            sdef = globals_.Actors[id_]

            # Find what values are used by this actor
            for field in sdef.fields:
                if not isinstance(field, (ListActorField, ValueActorField)):
                    # Only values and lists can be idtypes
                    continue

                idtype = field.idtype
                if idtype is None:
                    # Only look at settings with idtypes
                    continue

                value = decoder.retrieve(data, field.bit)

                # 3. Add the value to self.actor_idtypes
                try:
                    counter = globals_.Area.actor_idtypes[idtype]
                except KeyError:
                    globals_.Area.actor_idtypes[idtype] = {value: 1}
                    continue

                counter[value] = counter.get(value, 0) + 1

            globals_.mainWindow.scene.addItem(spr)
            spr.UpdateListItem()

            SetDirty()

        return spr

    def position_changed(self, oldx: float, oldy: float, x: float, y: float) -> None:
        """
        Handle the actor being dragged
        """
        if globals_.mainWindow is None:
            return

        if self == globals_.mainWindow.selObj:
            if oldx == x and oldy == y:
                return

            self.UpdateListItem()
            SetDirty()

            # The actor has changed position, so its LevelRect changed, so the
            # level overview needs to be redrawn.
            globals_.mainWindow.level_overview.update()

    def SetType(self, actor_num: int) -> None:
        """
        Sets the type of the actor
        """
        if 0 <= actor_num < globals_.NumActors:
            self.name = globals_.Actors[actor_num].name
        else:
            self.name = globals_.trans.string('Actors', 24) # 'UNKNOWN'

        self.setToolTip(globals_.trans.string('Actors', 0, '[type]', actor_num, '[name]', self.name))
        self.actor_num = actor_num

        self.InitializeActor()
        self.UpdateListItem()

    def __lt__(self, other: 'ActorItem') -> bool:
        # Sort by objx, then objy, then actor type
        score = lambda actor: (actor.objx, actor.objy, actor.type)

        return score(self) < score(other)

    def InitializeActor(self) -> None:
        """
        Initializes actor and creates any auxiliary objects needed
        """
        actor_num = self.actor_num

        if not 0 <= actor_num < globals_.NumActors:
            return

        self.name = globals_.Actors[actor_num].name
        self.setToolTip(globals_.trans.string('Actors', 0, '[type]', self.actor_num, '[name]', self.name))

        imgs = globals_.gamedef.getImageClasses()
        if actor_num in imgs:
            self.setImageObj(imgs[actor_num])

    def setImageObj(self, obj: Callable) -> None:
        """
        Sets a new actor image object for this ActorItem
        """
        for aux_obj in self.ImageObj.aux:
            aux_obj = cast(actorlib.AuxiliaryActorItem, aux_obj)
            scene = aux_obj.scene()

            if scene is not None:
                scene.removeItem(aux_obj)

        self.setZValue(26000)
        self.resetTransform()

        if (self.actor_num in globals_.gamedef.getImageClasses()) and (self.actor_num not in actorlib.ActorImagesLoaded):
            globals_.gamedef.getImageClasses()[self.actor_num].loadImages()
            actorlib.ActorImagesLoaded.add(self.actor_num)

        self.ImageObj = obj(self) if obj else actorlib.ActorImage(self)

        # show auxiliary objects properly
        for aux in self.ImageObj.aux:
            aux = cast(actorlib.AuxiliaryActorItem, aux)
            aux.setVisible(globals_.ActorImagesShown)

        self.UpdateDynamicSizing()

    def UpdateDynamicSizing(self) -> None:
        """
        Updates the sizes for dynamically sized actors
        """
        curr_rect = QtCore.QRectF(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())
        curr_aux_rects = []
        for aux_obj in self.ImageObj.aux:
            aux_obj = cast(actorlib.AuxiliaryActorItem, aux_obj)

            curr_aux_rects.append(QtCore.QRectF(
                aux_obj.x() + self.x(),
                aux_obj.y() + self.y(),
                aux_obj.boundingRect().width(),
                aux_obj.boundingRect().height(),
            ))

        self.ImageObj.dataChanged()

        if globals_.ActorImagesShown:
            self.UpdateRects()
            self.ChangingPos = True
            self.setPos(
                (self.objx + self.ImageObj.xOffset) * 1.5,
                (self.objy + self.ImageObj.yOffset) * 1.5,
            )
            self.ChangingPos = False

        scene = self.scene()
        if scene is not None:
            scene.update(curr_rect)
            scene.update(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())
            for auxUpdateRect in curr_aux_rects:
                scene.update(auxUpdateRect)

    def UpdateRects(self) -> None:
        """
        Creates all the rectangles for the actor
        """
        self.prepareGeometryChange()

        # Get rects
        imgRect = QtCore.QRectF(
            0, 0,
            self.ImageObj.width * 1.5,
            self.ImageObj.height * 1.5,
        )
        actorboxRect = QtCore.QRectF(
            0, 0,
            self.ImageObj.actorbox.BoundingRect.width(),
            self.ImageObj.actorbox.BoundingRect.height(),
        )
        imgOffsetRect = imgRect.translated(
            (self.objx + self.ImageObj.xOffset) * 1.5,
            (self.objy + self.ImageObj.yOffset) * 1.5,
        )
        actorboxOffsetRect = actorboxRect.translated(
            (self.objx * 1.5) + self.ImageObj.actorbox.BoundingRect.topLeft().x(),
            (self.objy * 1.5) + self.ImageObj.actorbox.BoundingRect.topLeft().y(),
        )

        if globals_.ActorImagesShown:
            unitedRect = imgRect.united(actorboxRect)

            if self.ImageObj.actorbox.shown:
                unitedOffsetRect = imgOffsetRect.united(actorboxOffsetRect)
            else:
                unitedOffsetRect = imgOffsetRect

            # SelectionRect: Used to determine the size of the
            # "this actor is selected" translucent white box that
            # appears when a actor with an image is selected.
            self.SelectionRect = QtCore.QRectF(
                0.5, 0.5,
                imgRect.width() - 1,
                imgRect.height() - 1,
            )

            # LevelRect: Used by the Level Overview to determine
            # the size and position of the actor in the level.
            # Measured in blocks.
            self.LevelRect = QtCore.QRectF(
                unitedOffsetRect.topLeft() / 24,
                unitedOffsetRect.size() / 24,
            )

            # BoundingRect: The actor can only paint within
            # this area.
            self.BoundingRect = unitedRect.translated(
                self.ImageObj.actorbox.BoundingRect.topLeft()
            )

        else:
            self.SelectionRect = QtCore.QRectF(0.5, 0.5, 23, 23)

            self.LevelRect = QtCore.QRectF(
                actorboxOffsetRect.topLeft() / 24,
                actorboxOffsetRect.size() / 24,
            )

            # BoundingRect: The actor can only paint within
            # this area.
            self.BoundingRect = self.ImageObj.actorbox.BoundingRect

    def getFullRect(self) -> QtCore.QRectF:
        """
        Returns a rectangle that contains the actor and all
        auxiliary objects.
        """
        self.UpdateRects()

        br = self.BoundingRect.translated(
            self.x(),
            self.y(),
        )
        for aux in self.ImageObj.aux:
            aux = cast(actorlib.AuxiliaryActorItem, aux)

            br = br.united(
                aux.boundingRect().translated(
                    aux.x() + self.x(),
                    aux.y() + self.y(),
                )
            )

        return br

    def itemChange(self, change: QtWidgets.QGraphicsItem.GraphicsItemChange, value: Any) -> QtCore.QPointF | None:
        """
        Makes sure positions don't go out of bounds and updates them as necessary
        """

        if change == QtWidgets.QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            scene = self.scene()
            if scene is None or globals_.mainWindow is None:
                return value

            if self.ChangingPos:
                return value

            # The actor image offset as a point
            if globals_.ActorImagesShown:
                offset_point = QtCore.QPointF(*self.ImageObj.getOffset())
            else:
                offset_point = QtCore.QPointF()

            # Convert the new position from 24 units per block into 16 units per
            # block
            new_pos = value / 1.5

            # Move the position to actor origin space by subtracting the image
            # offset
            origin_pos = (new_pos - offset_point).toPoint()

            # Snap this position to the grid
            drag_offset = None
            if globals_.OverrideSnapping or QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.KeyboardModifier.AltModifier:
                # Snap the smallest amount possible -> 1/16th of a block
                snap_level = 1
            elif self.isSelected() and len(globals_.mainWindow.CurrentSelection) > 1:
                objects_selected = any(isinstance(x, ObjectItem) for x in globals_.mainWindow.CurrentSelection)

                # dragoffsetx and y are in 24 = 1 block units, so convert it to
                # 16 = 1 block units
                drag_offset = QtCore.QPointF(self.dragoffsetx, self.dragoffsety) / 1.5

                origin_pos = (QtCore.QPointF(origin_pos) + drag_offset).toPoint()

                if objects_selected:
                    # Snap to full blocks (16/16)
                    snap_level = 16
                else:
                    # Snap to half blocks, but adjust for drag offset
                    snap_level = 8

            else:
                # Snap to half-blocks (8/16)
                snap_level = 8

            # Make sure the position is in bounds
            x = clamp(origin_pos.x(), 0, 16368)
            y = clamp(origin_pos.y(), 0, 8176)

            # When snapping, round to the nearest multiple of snap_level. Round
            # up when two multiples are equally far apart.
            origin_pos.setX(int((x + (snap_level / 2)) // snap_level) * snap_level)
            origin_pos.setY(int((y + (snap_level / 2)) // snap_level) * snap_level)

            if drag_offset is not None:
                origin_pos = (QtCore.QPointF(origin_pos) - drag_offset).toPoint()

            # Move position back to actor image space by adding the image offset
            # and calculate objx and objy based on the actor origin position.
            new_pos = QtCore.QPointF(QtCore.QPointF(origin_pos) + offset_point) * 1.5

            x = origin_pos.x()
            y = origin_pos.y()

            if x != self.objx or y != self.objy:
                updRect = QtCore.QRectF(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())
                scene.update(updRect)

                self.LevelRect.moveTo(new_pos / 24)

                for aux_obj in self.ImageObj.aux:
                    aux_obj = cast(actorlib.AuxiliaryActorItem, aux_obj)

                    update_rect = QtCore.QRectF(
                        self.pos() + aux_obj.pos(),
                        aux_obj.boundingRect().size(),
                    )
                    scene.update(update_rect)

                scene.update(
                    self.ImageObj.actorbox.BoundingRect.translated(self.pos())
                )

                oldx = self.objx
                oldy = self.objy
                self.objx = x
                self.objy = y
                if self.positionChanged is not None:
                    self.positionChanged(self, oldx, oldy, x, y)

                # Add moving this actor to the undo stack.
                if len(globals_.mainWindow.CurrentSelection) == 1:
                    act = MoveItemUndoAction(self, oldx, oldy, x, y)
                    globals_.mainWindow.undoStack.addOrExtendAction(act)
                elif len(globals_.mainWindow.CurrentSelection) > 1:
                    pass

                self.ImageObj.positionChanged()

                SetDirty()

            return new_pos

        return QtWidgets.QGraphicsItem.itemChange(self, change, value)

    def setNewObjPos(self, newobjx: float, newobjy: float) -> None:
        """
        Sets a new position, through objx and objy
        """
        self.objx, self.objy = newobjx, newobjy

        if globals_.ActorImagesShown:
            newobjx += self.ImageObj.xOffset
            newobjy += self.ImageObj.yOffset

        self.setPos(newobjx * 1.5, newobjy * 1.5)

    @staticmethod
    def moveToActor(item: 'ActorItem') -> None:
        """
        Moves the view to the actor and selects it.
        """
        actor = item.data(QtCore.Qt.ItemDataRole.UserRole)

        if actor is None:
            return

        actor.ensureVisible(xMargin=192, yMargin=192)
        actor.scene().clearSelection()
        actor.setSelected(True)

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """
        Overrides mouse pressing events if needed for cloning
        """
        if not event or not globals_.mainWindow:
            return

        if event.button() != QtCore.Qt.MouseButton.LeftButton or QtWidgets.QApplication.keyboardModifiers() != QtCore.Qt.KeyboardModifier.ControlModifier:
            old_pos = (self.objx, self.objy)

            LevelEditorItem.mousePressEvent(self, event)

            if not globals_.ActorImagesShown:
                self.setNewObjPos(*old_pos)

            return

        self.CreateActor(self.objx, self.objy, self.actor_num, self.actordata)
        globals_.mainWindow.scene.clearSelection()
        self.setSelected(True)

    def hoverMoveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        LevelEditorItem.hoverMoveEvent(self, event)
        if (self.isSelected() or globals_.CursorMode == 2) and not globals_.ActorsFrozen:
            setOverrideCursor(QtCore.Qt.CursorShape.SizeAllCursor)

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        LevelEditorItem.hoverLeaveEvent(self, event)
        setOverrideCursor(None)

    def nearestZone(self, obj: bool = False) -> ZoneItem | int | None:
        """
        Calls a modified MapPositionToZoneID (if obj = True, it returns the
        actual ZoneItem object). If the area is not fully loaded yet, or there
        are no zones, it returns None.
        """
        if not hasattr(globals_.Area, 'zones'):
            return None

        zone_idx = actorlib.MapPositionToZoneID(globals_.Area.zones, self.objx, self.objy)

        if zone_idx == -1:
            return None

        zone_obj = globals_.Area.zones[zone_idx]

        return zone_obj if obj else zone_obj.id

    def updateScene(self) -> None:
        """
        Calls self.scene().update()
        """
        # Some of the more advanced painters need to update the whole scene
        # and this is a convenient way to do it:
        # self.parent.updateScene()
        scene = self.scene()
        if scene is not None:
            scene.update()

    def paint(self, painter: QtGui.QPainter | None, option: QtWidgets.QStyleOptionGraphicsItem | None = None,
              widget: QtWidgets.QWidget | None = None, overrideGlobals: bool = False) -> None:
        """
        Paints the actor
        """
        if not painter or not self.font:
            return

        # Setup stuff
        if option is not None:
            painter.setClipRect(option.exposedRect)
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # Turn aux things on or off
        for aux in self.ImageObj.aux:
            aux = cast(actorlib.AuxiliaryActorItem, aux)
            aux.setVisible(globals_.ActorImagesShown)

        # Default actorbox
        drawActorbox = True
        actorboxRect = QtCore.QRectF(1, 1, 22, 22)

        if globals_.ActorImagesShown or overrideGlobals:
            self.ImageObj.paint(painter)

            drawActorbox = self.ImageObj.actorbox.shown

            # Draw the selected-actor-image overlay box
            if self.isSelected() and (not drawActorbox or self.ImageObj.size != (16, 16)):
                color = globals_.theme.color('actor_lines_s')
                if color is not None:
                    painter.setPen(QtGui.QPen(color, 1, QtCore.Qt.PenStyle.DashLine))
                painter.drawRect(self.SelectionRect)
                color = globals_.theme.color('actor_fill_s')
                if color is not None:
                    painter.fillRect(self.SelectionRect, color)

            # Determine the actorbox position
            if drawActorbox:
                actorboxRect = self.ImageObj.actorbox.RoundedRect

        # Draw the actorbox if applicable
        if drawActorbox:
            if self.isSelected():
                painter.setBrush(QtGui.QBrush(globals_.theme.color('actorbox_fill_s')))
                color = globals_.theme.color('actorbox_lines_s')
                if color is not None:
                    painter.setPen(QtGui.QPen(color, 1))
            else:
                painter.setBrush(QtGui.QBrush(globals_.theme.color('actorbox_fill')))
                color = globals_.theme.color('actorbox_lines')
                if color is not None:
                    painter.setPen(QtGui.QPen(color, 1))

            if globals_.UseRoundedRectangles:
                painter.drawRoundedRect(actorboxRect, 4, 4)
            else:
                painter.drawRect(actorboxRect)

            painter.setFont(self.font)
            painter.drawText(actorboxRect, QtCore.Qt.AlignmentFlag.AlignCenter, str(self.actor_num))

    def scene(self) -> QtWidgets.QGraphicsScene | None:
        """
        Solves a small bug
        """
        if globals_.mainWindow is not None:
            return globals_.mainWindow.scene

    def delete(self) -> None:
        """
        Delete the actor from the level
        """
        if globals_.mainWindow is None:
            return

        self.ImageObj.remove()
        globals_.mainWindow.UpdateFlag = True
        globals_.mainWindow.palette_dock.actor_tab.actor_list.takeActor(self)
        globals_.mainWindow.palette_dock.actor_tab.actor_order_list.takeActor(self)
        globals_.mainWindow.UpdateFlag = False

        sel_model = globals_.mainWindow.palette_dock.actor_tab.actor_list.selectionModel()
        if sel_model is not None:
            sel_model.clearSelection()

        sel_model = globals_.mainWindow.palette_dock.actor_tab.actor_order_list.selectionModel()
        if sel_model is not None:
            sel_model.clearSelection()
        globals_.Area.RemoveActor(self)

        # The zone painters need for the whole thing to update
        scene = self.scene()
        if scene is not None:
            scene.update()

        setOverrideCursor(None)
