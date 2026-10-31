from PyQt6 import QtCore, QtGui, QtWidgets
from typing import cast

from data import globals_
from data.common.settings import setSetting
from data.level.items.basic import LevelEditorItem
from data.level.items.comment import CommentItem
from data.level.items.entrance import EntranceItem
from data.level.items.location import LocationItem
from data.level.items.object import ObjectItem
from data.level.items.path import PathItem
from data.level.items.sprite import SpriteItem
from ui.graphics.grid import draw_foreground_grid
import spritelib

class LevelScene(QtWidgets.QGraphicsScene):
    """
    GraphicsScene subclass for the level scene
    """

    def __init__(self, *args):
        QtWidgets.QGraphicsScene.__init__(self, *args)
        self.setBackgroundBrush(QtGui.QBrush(globals_.theme.color('bg')))
        self.is_screenshot = False
        self.selectionChanged.connect(self.change_selection)

    def drawForeground(self, painter, rect):
        """
        Draw a grid for screenshots
        """
        if self.is_screenshot:
            draw_foreground_grid(painter, rect, True)

    def drawBackground(self, painter: QtGui.QPainter | None, rect: QtCore.QRectF) -> None:
        """
        Draws all visible tiles
        """
        QtWidgets.QGraphicsScene.drawBackground(self, painter, rect)
        if not hasattr(globals_.Area, 'layers'):
            return

        if painter is None:
            return

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
                        odefs[item.tileset][item.object_num] is None:
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

    def play_tile_anim(self, checked: bool) -> None:
        """
        Toggles tileset animations
        """
        globals_.TilesetsAnimating = checked

        for tile in globals_.Tiles:
            if tile is not None:
                tile.resetAnimation()

        self.update()

    def show_tile_collision(self, checked: bool) -> None:
        """
        Toggles tileset collision previews
        """
        globals_.CollisionsShown = checked

        setSetting('ShowCollisions', globals_.CollisionsShown)
        self.update()

    def show_real_view(self, checked: bool) -> None:
        """
        Toggles Real View mode
        """
        globals_.RealViewEnabled = checked
        spritelib.RealViewEnabled = globals_.RealViewEnabled

        setSetting('RealViewEnabled', globals_.RealViewEnabled)
        self.update()

    def switch_grid(self) -> None:
        """
        Switches the current grid type
        """
        if globals_.GridType is None:
            globals_.GridType = 'grid'
        elif globals_.GridType == 'grid':
            globals_.GridType = 'checker'
        else:
            globals_.GridType = None

        setSetting('GridType', globals_.GridType)
        self.update()

    def change_selection(self) -> None:
        """
        Update visible docks whenever the selected item(s) change
        """
        main_window = globals_.mainWindow
        if main_window.SelectionUpdateFlag:
            return

        try:
            selitems = main_window.scene.selectedItems()
        except RuntimeError:
            # Must catch this error: If you close the app while something is selected,
            # you get a RuntimeError about the 'underlying C++ object being deleted'
            return

        # Do this to avoid flickering
        show_sprite_dock = False
        show_entrance_dock = False
        show_location_dock = False
        show_path_dock = False
        update_docks = False

        # Clear our variables
        main_window.selObj = None

        main_window.palette_dock.entrance_tab.entrance_list.setCurrentItem(None)
        main_window.palette_dock.location_tab.location_list.setCurrentItem(None)
        main_window.palette_dock.path_tab.path_list.setCurrentItem(None)
        main_window.palette_dock.comment_tab.comment_list.setCurrentItem(None)

        # possibly a small optimization
        func_ii = isinstance
        type_obj = ObjectItem
        type_spr = SpriteItem
        type_ent = EntranceItem
        type_loc = LocationItem
        type_path = PathItem
        type_com = CommentItem

        allow_stamp = True
        action_list = main_window.action_list

        # Nothing is selected
        if not selitems:
            action_list['cut'].setEnabled(False)
            action_list['copy'].setEnabled(False)
            action_list['shiftitems'].setEnabled(False)
            action_list['mergelocations'].setEnabled(False)

        # Only one item selected
        elif len(selitems) == 1:
            action_list['cut'].setEnabled(True)
            action_list['copy'].setEnabled(True)
            action_list['shiftitems'].setEnabled(True)
            action_list['mergelocations'].setEnabled(False)
            update_docks = True

            item = selitems[0]
            main_window.selObj = cast(LevelEditorItem, item)

            if func_ii(item, type_obj):
                allow_stamp = True
                update_docks = False
            elif func_ii(item, type_spr):
                show_sprite_dock = True
                allow_stamp = True
            elif func_ii(item, type_ent):
                globals_.mainWindow.palette_dock.entrance_tab.set_item(item)
                show_entrance_dock = True
                allow_stamp = False
            elif func_ii(item, type_loc):
                globals_.mainWindow.palette_dock.location_tab.set_item(item)
                show_location_dock = True
                allow_stamp = False
            elif func_ii(item, type_path):
                globals_.mainWindow.palette_dock.path_tab.set_item(item)
                show_path_dock = True
                allow_stamp = False
            elif func_ii(item, type_com):
                globals_.mainWindow.palette_dock.comment_tab.set_item(item)
                allow_stamp = False

        # Multiple items selected
        else:
            update_docks = True

            for item in selitems:
                if not func_ii(item, (type_obj, type_spr)):
                    allow_stamp = False

            action_list['cut'].setEnabled(True)
            action_list['copy'].setEnabled(True)
            action_list['shiftitems'].setEnabled(True)

        # Turn on the Stamp Add button if applicable
        main_window.palette_dock.stamp_tab.add_button.setEnabled(bool(selitems) and allow_stamp)

        # Count how many of each item we have
        spr = 0
        ent = 0
        obj = 0
        loc = 0
        path = 0
        com = 0

        for item in selitems:
            if func_ii(item, type_spr):
                spr += 1
            if func_ii(item, type_ent):
                ent += 1
            if func_ii(item, type_obj):
                obj += 1
            if func_ii(item, type_loc):
                loc += 1
            if func_ii(item, type_path):
                path += 1
            if func_ii(item, type_com):
                com += 1

        action_list['mergelocations'].setEnabled(loc >= 2)
        main_window.palette_dock.object_tab.layer_change_button.setEnabled(obj != 0)

        # Write the statusbar label text
        # TODO: This should be all cleaned up in the future, not exactly
        # sure what the best way to do that is, though...
        text = ''

        if selitems:
            singleitem = len(selitems) == 1
            if singleitem:
                if obj:
                    text = globals_.trans.string('Statusbar', 0)  # 1 object selected
                elif spr:
                    text = globals_.trans.string('Statusbar', 1)  # 1 sprite selected
                elif ent:
                    text = globals_.trans.string('Statusbar', 2)  # 1 entrance selected
                elif loc:
                    text = globals_.trans.string('Statusbar', 3)  # 1 location selected
                elif path:
                    text = globals_.trans.string('Statusbar', 4)  # 1 path node selected
                else:
                    text = globals_.trans.string('Statusbar', 29)  # 1 comment selected

            # Multiple things selected; see if they're all the same type
            else:
                if not any((spr, ent, loc, path, com)):
                    text = globals_.trans.string('Statusbar', 5, '[x]', obj)  # X objects selected
                elif not any((obj, ent, loc, path, com)):
                    text = globals_.trans.string('Statusbar', 6, '[x]', spr)  # X sprites selected
                elif not any((obj, spr, loc, path, com)):
                    text = globals_.trans.string('Statusbar', 7, '[x]', ent)  # X entrances selected
                elif not any((obj, spr, ent, path, com)):
                    text = globals_.trans.string('Statusbar', 8, '[x]', loc)  # X locations selected
                elif not any((obj, spr, ent, loc, com)):
                    text = globals_.trans.string('Statusbar', 9, '[x]', path) # X path nodes selected
                elif not any((obj, spr, ent, path, loc)):
                    text = globals_.trans.string('Statusbar', 30, '[x]', com) # X comments selected
                else:  # Different types
                    text = globals_.trans.string('Statusbar', 10, '[x]', len(selitems)) # X items selected
                    text = cast(str, text)

                    # Count, single ID, multi ID
                    types = (
                        (obj, 12, 13),
                        (spr, 14, 15),
                        (ent, 16, 17),
                        (loc, 18, 19),
                        (path, 20, 21),
                        (com, 31, 32),
                    )

                    first = True
                    for count, single_code, multi_code in types:
                        if count > 0:
                            if not first:
                                text += str(globals_.trans.string('Statusbar', 11))

                            first = False
                            text += str(globals_.trans.string('Statusbar', (single_code if count == 1 else multi_code), '[x]', count))

                    text += str(globals_.trans.string('Statusbar', 22))  # ')'

        main_window.selectionLabel.setText(text)
        main_window.CurrentSelection = selitems

        for item in selitems:
            # This helps sync non-objects with objects while dragging
            if not isinstance(item, ObjectItem):
                item = cast(LevelEditorItem, item)
                item.dragoffsetx = int((((item.objx // 16) * 16) - item.objx) * 1.5)
                item.dragoffsety = int((((item.objy // 16) * 16) - item.objy) * 1.5)

        main_window.spriteEditorDock.set_active(show_sprite_dock)
        main_window.entrance_editor_dock.set_active(show_entrance_dock)
        main_window.location_editor_dock.set_active(show_location_dock)
        main_window.path_editor_dock.set_active(show_path_dock)

        action_list['deselect'].setEnabled(bool(selitems))

        if update_docks:
            globals_.DirtyOverride += 1
            main_window.update_dock()
            globals_.DirtyOverride -= 1
