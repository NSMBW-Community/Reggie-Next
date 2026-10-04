from PyQt6 import QtCore, QtWidgets

from data import globals_
from data.level.dirty import SetDirty
from data.level.items.basic import LevelEditorItem
from data.level.items.entrance import EntranceItem
from data.level.items.location import LocationItem
from data.level.items.object import ObjectItem
from data.level.items.path import PathItem
from data.level.items.sprite import SpriteItem
from data.level.items.comment import CommentItem
from data.level.path import Path


class ReggieClip:
    """
    Represents Reggie level items encoded as plaintext
    """

    @staticmethod
    def get_reggie_clip(items: list[LevelEditorItem]) -> str:
        """
        Generates a ReggieClip from a list of items and returns it
        """
        if globals_.mainWindow is None:
            return ''

        objects = []
        sprites = []
        entrances = []
        locations = []
        path_nodes = []
        comments = []

        for obj in items:
            if isinstance(obj, ObjectItem):
                objects.append(obj)
            elif isinstance(obj, SpriteItem):
                sprites.append(obj)
            elif isinstance(obj, EntranceItem):
                entrances.append(obj)
            elif isinstance(obj, LocationItem):
                locations.append(obj)
            elif isinstance(obj, PathItem):
                path_nodes.append(obj)
            elif isinstance(obj, CommentItem):
                comments.append(obj)

        return ReggieClip.encode_reggie_clip(objects, sprites, entrances, locations, path_nodes, comments)

    @staticmethod
    def encode_reggie_clip(
        objects: list[ObjectItem],
        sprites: list[SpriteItem],
        entrances: list[EntranceItem],
        locations: list[LocationItem],
        path_nodes: list[PathItem],
        comments: list[CommentItem],
    ) -> str:
        """
        Encode sets of level items into a ReggieClip string
        """
        output = ['ReggieClip']

        # Objects
        objects.sort(key=lambda x: x.zValue())

        for obj in objects:
            output.append(f'0:{obj.tileset}:{obj.object_num}:{obj.layer}:{obj.objx}:{obj.objy}:{obj.width}:{obj.height}')

        # Sprites
        for spr in sprites:
            data = spr.spritedata
            output.append(f'1:{spr.sprite_num}:{spr.objx}:{spr.objy}:{data[0]}:{data[1]}:{data[2]}:{data[3]}:{data[4]}:{data[5]}:{data[7]}')

        # Entrances
        for item in entrances:
            output.append(f'2:{item.objx}:{item.objy}:{item.entid}:{item.destarea}:{item.destentrance}:{item.enttype}:{item.entzone}:'
                          f'{item.entsettings}:{item.entlayer}:{item.entpath}:{int(item.leave_level)}:{item.cpdirection}')

        # Locations
        for loc in locations:
            output.append(f'3:{loc.id}:{loc.objx}:{loc.objy}:{loc.width}:{loc.height}')

        # Path Nodes
        path_nodes.sort(key=lambda x: (x.pathid, x.nodeid))
        curr_path_id = 0

        for item in path_nodes:
            # Get parent path
            path: Path | None = None
            for p in globals_.Area.paths:
                if item.pathid == p._id:
                    path = p
                    break

            # Append a path object
            if path is not None:
                if curr_path_id != item.pathid: # Check if we should append a new Path
                    output.append(f'4:{path._id}:{int(path._loops)}')
                    curr_path_id = item.pathid

                x, y, speed, accel, delay = path.get_node_data(item.nodeid)
                output.append(f'5:{item.pathid}:{item.nodeid}:{x}:{y}:{speed}:{accel}:{delay}')

        # Comments
        for com in comments:
            raw_text = com.text.encode().hex()
            output.append(f'6:{com.objx}:{com.objy}:{raw_text}')

        output.append('%')
        return '|'.join(output)

    @staticmethod
    def paste_reggie_clip(
        reggie_clip: str,
        select: bool = True,
        xOverride: int | None = None,
        yOverride: int | None = None,
    ) -> list[LevelEditorItem]:
        """
        Decode and place a set of items
        """
        if globals_.mainWindow is None:
            return []

        globals_.mainWindow.SelectionUpdateFlag = True
        globals_.mainWindow.scene.clearSelection()
        added: list[LevelEditorItem] = []

        # Remove leading and trailing whitespace
        reggie_clip = reggie_clip.strip()

        if not (reggie_clip.startswith('ReggieClip|') and reggie_clip.endswith('|%')):
            globals_.mainWindow.SelectionUpdateFlag = False
            return added

        clip = reggie_clip.split('|')

        if len(clip) > 300 + 2:
            result = QtWidgets.QMessageBox.warning(globals_.mainWindow, globals_.trans.string('MainWindow', 8), globals_.trans.string('MainWindow', 1),
                                                    QtWidgets.QMessageBox.StandardButton.Yes, QtWidgets.QMessageBox.StandardButton.No)
            if result == QtWidgets.QMessageBox.StandardButton.No:
                globals_.mainWindow.SelectionUpdateFlag = False
                return added

        globals_.OverrideSnapping = True

        layers, sprites, entrances, locations, paths, path_nodes, comments = ReggieClip.decode_reggie_clip(reggie_clip)

        # Find the bounding box of all created objects
        bounding = QtCore.QRectF()

        for spr in sprites:
            bounding |= spr.LevelRect

        for layer in layers:
            for obj in layer:
                bounding |= obj.LevelRect

        for ent in entrances:
            bounding |= ent.LevelRect

        for loc in locations:
            bounding |= loc.LevelRect

        for node in path_nodes:
            bounding |= node.LevelRect

        for com in comments:
            bounding |= com.LevelRect

        x1, y1, width, height = bounding.getRect()
        if x1 is None or y1 is None or width is None or height is None:
            return []

        # Now center everything
        zoomscaler = globals_.mainWindow.ZoomLevel / 100
        viewportx = (globals_.mainWindow.view.XScrollBar.value() / zoomscaler) / 24
        viewporty = (globals_.mainWindow.view.YScrollBar.value() / zoomscaler) / 24
        viewportwidth = (globals_.mainWindow.view.width() / zoomscaler) / 24
        viewportheight = (globals_.mainWindow.view.height() / zoomscaler) / 24

        # Tiles
        if xOverride is None:
            xoffset = int(0 - x1 + viewportx + ((viewportwidth / 2) - (width / 2)))
            xpixeloffset = xoffset * 16
        else:
            xoffset = int(0 - x1 + (xOverride / 16) - (width / 2))
            xpixeloffset = xoffset * 16
        if yOverride is None:
            yoffset = int(0 - y1 + viewporty + ((viewportheight / 2) - (height / 2)))
            ypixeloffset = yoffset * 16
        else:
            yoffset = int(0 - y1 + (yOverride / 16) - (height / 2))
            ypixeloffset = yoffset * 16

        # Center and select everything
        for item in sprites:
            item.setNewObjPos(item.objx + xpixeloffset, item.objy + ypixeloffset)
            item.UpdateRects()
            item.setSelected(select)

        for layer in layers:
            for item in layer:
                item.setPos((item.objx + xoffset) * 24, (item.objy + yoffset) * 24)
                item.UpdateRects()
                item.setSelected(select)

        for item in entrances:
            item.setPos((item.objx + xpixeloffset) * 1.5, (item.objy + ypixeloffset) * 1.5)
            item.UpdateRects()
            item.setSelected(select)

        for item in locations:
            item.setPos((item.objx + xpixeloffset) * 1.5, (item.objy + ypixeloffset) * 1.5)
            item.UpdateRects()
            item.setSelected(select)

        for item in path_nodes:
            item.setPos((item.objx + xpixeloffset) * 1.5, (item.objy + ypixeloffset) * 1.5)
            item.setSelected(select)

        for item in comments:
            item.setPos((item.objx + xpixeloffset) * 1.5, (item.objy + ypixeloffset) * 1.5)
            item.setSelected(select)

        globals_.OverrideSnapping = False

        globals_.mainWindow.level_overview.update()
        SetDirty()
        globals_.mainWindow.SelectionUpdateFlag = False
        globals_.mainWindow.ChangeSelectionHandler()

        # Combine the sprites and layers
        added.extend(sprites)
        added.extend(entrances)
        added.extend(locations)
        added.extend(paths)
        added.extend(path_nodes)
        added.extend(comments)
        for layer in layers:
            added.extend(layer)

        return added

    @staticmethod
    def decode_reggie_clip(reggie_clip: str, add_to_scene: bool = True) -> tuple[tuple[list[ObjectItem], list[ObjectItem], list[ObjectItem]], list[SpriteItem], list[EntranceItem], list[LocationItem], list[Path], list[PathItem], list[CommentItem]]:
        """
        Decode the objects from a ReggieClip
        """
        layers = ([], [], [])
        sprites = []
        entrances = []
        locations = []
        paths = []
        path_nodes = []
        comments = []

        if globals_.mainWindow is None:
            return layers, sprites, entrances, locations, paths, path_nodes, comments

        if not (reggie_clip.startswith('ReggieClip|') and reggie_clip.endswith('|%')):
            return layers, sprites, entrances, locations, paths, path_nodes, comments

        clip = reggie_clip[11:-2].split('|')

        globals_.mainWindow.palette_dock.sprite_tab.sprite_list.prepareBatchAdd()
        globals_.mainWindow.palette_dock.sprite_tab.sprite_order_list.prepareBatchAdd()

        for item in clip:
            try:
                # Check to see the item type
                # and add it to the correct stack
                split = item.split(':')

                # Object
                if split[0] == '0':
                    if len(split) != 8:
                        continue

                    tileset = int(split[1])
                    type = int(split[2])
                    layer = int(split[3])
                    objx = int(split[4])
                    objy = int(split[5])
                    width = int(split[6])
                    height = int(split[7])

                    # basic sanity checks
                    if tileset < 0 or tileset > 3:
                        continue
                    if type < 0 or type > 255:
                        continue
                    if layer < 0 or layer > 2:
                        continue
                    if objx < 0 or objx > 1023:
                        continue
                    if objy < 0 or objy > 511:
                        continue
                    if width < 1 or width > 1023:
                        continue
                    if height < 1 or height > 511:
                        continue

                    newitem = ObjectItem.CreateObject(tileset, type, layer, objx, objy, width, height, add_to_scene)
                    layers[layer].append(newitem)

                # Sprite
                elif split[0] == '1':
                    if len(split) != 11:
                        continue

                    objx = int(split[2])
                    objy = int(split[3])
                    type = int(split[1])
                    data = bytes(map(int, [split[4], split[5], split[6], split[7], split[8], split[9], '0', split[10]]))

                    newitem = SpriteItem.CreateSprite(objx, objy, type, data, add_to_scene)
                    sprites.append(newitem)

                # Entrance
                elif split[0] == '2':
                    if len(split) != 13:
                        continue

                    objx = int(split[1])
                    objy = int(split[2])
                    entID = int(split[3])
                    destArea = int(split[4])
                    destEnt = int(split[5])
                    entType = int(split[6])
                    zone = int(split[7])
                    settings = int(split[8])
                    layer = int(split[9])
                    path = int(split[10])
                    exitLvl = int(split[11])
                    cPipeDir = int(split[12])

                    # Sanity check data
                    if destArea < 0 or destArea > 4:
                        continue
                    if destEnt < 0 or destEnt > 255:
                        continue
                    if entType < 0 or entType >= len(globals_.EntranceTypeNames):
                        continue
                    if layer < 0 or layer > 2:
                        continue
                    if path < 0 or path > 255:
                        continue
                    if cPipeDir < 0 or cPipeDir > 3:
                        continue

                    newitem = EntranceItem.CreateEntrance(objx, objy, entID, add_to_scene, True)
                    if newitem is None:
                        continue

                    # Set entrance data
                    newitem.destarea = destArea
                    newitem.destentrance = destEnt
                    newitem.enttype = entType
                    newitem.entzone = zone
                    newitem.entsettings = settings
                    newitem.entlayer = layer
                    newitem.entpath = path
                    newitem.leave_level = exitLvl != 0
                    newitem.cpdirection = cPipeDir

                    # Update it
                    newitem.TypeChange()
                    newitem.UpdateTooltip()
                    newitem.UpdateListItem(True)

                    entrances.append(newitem)

                # Location
                elif split[0] == '3':
                    if len(split) != 6:
                        continue

                    locID = int(split[1])
                    objx = int(split[2])
                    objy = int(split[3])
                    width = int(split[4])
                    height = int(split[5])

                    newitem = LocationItem.CreateLocation(objx, objy, width, height, locID, add_to_scene)
                    locations.append(newitem)

                # Path
                elif split[0] == '4':
                    if len(split) != 3:
                        continue

                    pathID = int(split[1])
                    loops = int(split[2]) == 1

                    if globals_.mainWindow is not None:
                        path = Path(pathID, globals_.mainWindow.scene, loops)
                        globals_.Area.paths.append(path)
                        paths.append(path)

                # Path Node
                elif split[0] == '5':
                    if len(split) != 8:
                        continue

                    pathID = int(split[1])
                    nodeID = int(split[2])
                    objx = int(split[3])
                    objy = int(split[4])
                    speed = float(split[5])
                    accel = float(split[6])
                    delay = int(split[7])

                    # Make sure the clip has the parent path
                    if paths is not None:
                        path = paths[0]
                        for p in paths:
                            if pathID == p._id:
                                path = p
                                break

                        node = path.add_node(objx, objy, speed, accel, delay, nodeID, add_to_scene, add_to_scene)
                        path_nodes.append(node)

                elif split[0] == '6':
                    if len(split) != 4:
                        continue

                    objx = int(split[1])
                    objy = int(split[2])
                    raw_text = str(split[3])
                    text = bytes.fromhex(raw_text).decode()

                    new_item = CommentItem.CreateComment(objx, objy, text, add_to_scene)
                    comments.append(new_item)

            except ValueError:
                # an int() probably failed somewhere
                pass

        globals_.mainWindow.palette_dock.sprite_tab.sprite_list.endBatchAdd()
        globals_.mainWindow.palette_dock.sprite_tab.sprite_order_list.endBatchAdd()

        return layers, sprites, entrances, locations, paths, path_nodes, comments
