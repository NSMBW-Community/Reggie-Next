from enum import IntEnum
from PyQt6 import QtWidgets, QtGui

import globals_

from dirty import SetDirty
import spritelib as SLib
from levelitems import SpriteItem, ZoneItem, EntranceItem
from ui import GetIcon

class DiagnosticToolDialog(QtWidgets.QDialog):
    """
    Dialog which checks for errors within the level
    """
    class Result(IntEnum):
        """
        Diagnostic check results
        """
        NO_ERROR = 0
        WARNING = 1
        CRITICAL = 2

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(globals_.trans.string('Diag', 0))
        self.setWindowIcon(GetIcon('diagnostics'))

        # check_functions: (icon, description, function, is_critical)
        self.check_functions = (
            ('objects',   globals_.trans.string('Diag', 2),  self.check_invalid_obj,        True),
            ('sprites',   globals_.trans.string('Diag', 3),  self.check_crash_sprite,       False),
            ('sprites',   globals_.trans.string('Diag', 4),  self.check_sprite_param,       True),
            ('sprites',   globals_.trans.string('Diag', 5),  self.check_sprite_max,         False),
            ('entrances', globals_.trans.string('Diag', 6),  self.check_duplicate_entrance, True),
            ('entrances', globals_.trans.string('Diag', 7),  self.check_start_entrance,     True),
            ('entrances', globals_.trans.string('Diag', 8),  self.check_entrance_near_edge, False),
            ('entrances', globals_.trans.string('Diag', 9),  self.check_entrance_out_zone,  False),
            ('zones',     globals_.trans.string('Diag', 10), self.check_zone_max,           True),
            ('zones',     globals_.trans.string('Diag', 11), self.check_no_zone_exist,      True),
            ('zones',     globals_.trans.string('Diag', 12), self.check_zone_proximity,     True),
            ('zones',     globals_.trans.string('Diag', 13), self.check_zone_on_area_edge,  True),
            ('zones',     globals_.trans.string('Diag', 14), self.check_no_bias,            False),
            ('zones',     globals_.trans.string('Diag', 15), self.check_zone_max_size,      True),
            # Possible things to implement checks for:
            # Non-location liquid in zone bigger than 8192 pixels (crest stops rendering)
        )

        error_box = QtWidgets.QGroupBox(globals_.trans.string('Diag', 17))
        self.error_layout = QtWidgets.QVBoxLayout()
        result, numErrors = self.populate_list()
        error_box.setLayout(self.error_layout)

        self.update_header(result)
        header_widget = QtWidgets.QWidget()
        header_widget.setLayout(self.header)

        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Close)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.addWidget(header_widget)
        self.main_layout.addWidget(error_box)
        self.main_layout.addWidget(self.button_box)
        self.setLayout(self.main_layout)

    def update_header(self, result: Result, not_first_run=False):
        """
        Creates/updates the header
        """
        self.header = QtWidgets.QGridLayout()
        self.header.addWidget(QtWidgets.QLabel(globals_.trans.string('Diag', 18)), 0, 0, 1, 3)

        point_size = 14
        icon_names = ['check', 'warning', 'delete']
        widths = [64, 128, 72]
        string_ids = [(19, 20), (21, 22), (23, 24)]
        colors = [
            QtGui.QColor(0, 200, 0),
            QtGui.QColor(210, 210, 0),
            QtGui.QColor(255, 0, 0)
        ]

        icon_label = QtWidgets.QLabel()
        icon_label.setPixmap(GetIcon(icon_names[result], True).pixmap(64, 64))
        self.header.addWidget(icon_label, 1, 0)

        if result == self.Result.WARNING:
            pixmap = QtGui.QPixmap(widths[result], int(point_size * 3 / 2))
        else:
            pixmap = QtGui.QPixmap(widths[result], point_size)
        pixmap.fill(QtGui.QColor(0, 0, 0, 0))
        painter = QtGui.QPainter(pixmap)

        font = painter.font()
        font.setPointSize(point_size)
        painter.setFont(font)
        painter.setPen(colors[result])
        painter.drawText(0, point_size, globals_.trans.string('Diag', string_ids[result][0]))

        del painter

        pix_label = QtWidgets.QLabel()
        pix_label.setPixmap(pixmap)
        self.header.addWidget(pix_label, 1, 1)

        self.header.addWidget(QtWidgets.QLabel(globals_.trans.string('Diag', string_ids[result][1])), 1, 2)

        if not_first_run:
            widget = QtWidgets.QWidget()
            widget.setLayout(self.header)

            item = self.main_layout.takeAt(0)
            if item is not None:
                item_widget = item.widget()
                if item_widget is not None:
                    item_widget.hide()

            self.main_layout.insertWidget(0, widget)

    def populate_list(self) -> tuple[Result, int]:
        """
        Runs the check functions and adds items to the list if needed
        """
        self.button_handlers = []

        self.error_list = QtWidgets.QListWidget()
        self.error_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)

        has_error = False
        is_critical = False

        for icon, description, func, critical in self.check_functions:
            if func('c'):
                has_error = True
                if critical:
                    is_critical = True

                item = QtWidgets.QListWidgetItem()
                item.setText(description)
                if critical:
                    item.setForeground(QtGui.QColor(255, 0, 0))
                else:
                    item.setForeground(QtGui.QColor(172, 172, 0))
                item.setIcon(GetIcon(icon))
                # Not sure how to fix the typing here...
                item.fix = func

                self.error_list.addItem(item)

        self.fix_button = QtWidgets.QPushButton(globals_.trans.string('Diag', 25))
        self.fix_button.setToolTip(globals_.trans.string('Diag', 26))
        self.fix_button.clicked.connect(self.fix_selected)
        if not has_error:
            self.fix_button.setEnabled(False)

        self.error_layout.addWidget(self.error_list)
        self.error_layout.addWidget(self.fix_button)

        # Automatically select first item since its "focused" by default, which makes it
        # look selected, and it can be super confusing
        if self.error_list.count() != 0:
            item = self.error_list.item(0)
            if item is not None:
                item.setSelected(True)

        if is_critical:
            return self.Result.CRITICAL, len(self.button_handlers)
        elif has_error:
            return self.Result.WARNING, len(self.button_handlers)

        return self.Result.NO_ERROR, len(self.button_handlers)

    def fix_selected(self):
        """
        Fixes the selected items
        """

        # Ask the user to make sure
        btn = QtWidgets.QMessageBox.warning(None, globals_.trans.string('Diag', 27), globals_.trans.string('Diag', 28),
                                            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        if btn != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        # Show the 'Fixing...' box while fixing
        fix_progress = QtWidgets.QProgressDialog()
        fix_progress.setLabelText(globals_.trans.string('Diag', 29))  # Fixing...
        fix_progress.setMinimum(0)
        fix_progress.setMaximum(100)
        fix_progress.setAutoClose(True)
        fix_progress.open()
        fix_progress.show()
        fix_progress.setValue(0)

        # Fix them
        for index, item in enumerate(self.error_list.selectedIndexes()[:]):
            listItem = self.error_list.itemFromIndex(item)
            try:
                listItem.fix()
                SetDirty()
            except Exception:
                pass  # Fail silently

            self.error_list.takeItem(item.row())

            total = len(self.error_list.selectedIndexes())
            if total != 0: fix_progress.setValue(int(index / total * 100))

        # Remove the 'Fixing...' box
        fix_progress.setValue(100)
        del fix_progress

        # Gray out the Fix button if there are no more problems
        if self.error_list.count() == 0:
            self.fix_button.setEnabled(False)


    # Check functions begin here
    def check_invalid_obj(self, mode='f'):
        """
        Checks for any objects which cannot be found in the tilesets
        """
        deletions = []
        for layer in globals_.Area.layers:
            for obj in layer:
                if globals_.ObjectDefinitions[obj.tileset] is None:
                    deletions.append(obj)
                elif globals_.ObjectDefinitions[obj.tileset][obj.type] is None:
                    deletions.append(obj)

        has_problem = bool(deletions)
        if mode == 'c':
            return has_problem

        if not has_problem:
            return

        if globals_.mainWindow is not None:
            for obj in deletions:
                obj.delete()
                obj.setSelected(False)
                globals_.mainWindow.scene.removeItem(obj)

            globals_.mainWindow.levelOverview.update()

    def check_crash_sprite(self, mode='f'):
        """
        Checks if there are any sprites which are known to crash or cause problems often
        """
        # TODO: Fill out this list, add support for sprites that only crash in Newer
        problems = [121] # Collision Switcher

        crash_sprites = []
        for sprite in globals_.Area.sprites:
            if sprite.type in problems:
                crash_sprites.append(sprite)

        if mode == 'c':
            return bool(crash_sprites)
        else:
            sprite: SpriteItem
            for sprite in crash_sprites:
                sprite.delete()
                sprite.setSelected(False)
                if globals_.mainWindow is not None:
                    globals_.mainWindow.scene.removeItem(sprite)
                    globals_.mainWindow.levelOverview.update()

    # TODO: Split 'missing resource' checks into their own function (153 needs it too)
    def check_sprite_param(self, mode='f'):
        """
        Checks for sprite settings which are known to cause major glitches and crashes
        """
        check_list = []
        problem = False

        sprite: SpriteItem
        for sprite in globals_.Area.sprites:
            # Snake Block, end-of-path behavior is above 3
            if sprite.type == 166 and ((sprite.spritedata[2] & 0xF0) >> 4) > 3:
                problem = True

            # Also double-check nyb10, then add it to the fixers
            # Mushroom in Bubble, spawns player
            if sprite.type == 171 and sprite.spritedata[4] & 0xF != 1:
                problem = True

            # Chest, check if we need a Toad
            if sprite.type == 203 and sprite.spritedata[4] & 0xF == 1:
                if [454, 432] not in check_list:
                    check_list.append([454, 432])

            # Cheep Cheep Formation, shape is 'Filled Arrow'
            # TODO: Investigate, this doesn't crash the game?
            if sprite.type == 247 and sprite.spritedata[5] & 0xF == 1:
                problem = True

            # Boo circle
            if sprite.type == 323:
                # Expand behavior
                if sprite.spritedata[4] & 0xF == 4:
                    problem = True

                # Greater Radius < Lesser Radius
                if sprite.spritedata[2] & 0xF < (sprite.spritedata[3] & 0xF0) >> 4:
                    problem = True

            # Bowser Fireball Spawner, position mod 1 can sometimes freeze the game
            if sprite.type == 449 and (sprite.spritedata[5] & 0xF0) >> 4 == 1:
                problem = True

            # Giant Bowser Switch, has Multi-Use enabled
            if sprite.type == 479 and sprite.spritedata[4] & 0xF != 0:
                problem = True

            # Rubble Block
            if sprite.type == 481:
                # Invalid size
                if sprite.spritedata[5] & 0xF > 1:
                    problem = True

                # Check for resource
                if [419] not in check_list:
                    check_list.append([419])

        # Check for sprites which depend on others' resources
        new = list(check_list)
        for item in check_list:
            for sprite in globals_.Area.sprites:
                if sprite.type in item:
                    try:
                        new.remove(item)
                    except Exception:
                        pass
        check_list = new

        if check_list:
            problem = True

        if mode == 'c':
            return problem

        elif problem:
            add_sprites = []
            for sprite in globals_.Area.sprites:
                if sprite.type == 166 and (sprite.spritedata[2] & 0xF0) >> 4 > 3:
                    sprite.spritedata = sprite.spritedata[0:2] + ' ' + sprite.spritedata[3:]

                if sprite.type == 171 and sprite.spritedata[4] & 0xF != 1:
                    sprite.spritedata = sprite.spritedata[0:4] + chr(1) + sprite.spritedata[5:]

                if sprite.type == 203 and sprite.spritedata[4] & 0xF == 1:
                    if [454, 432] in check_list:
                        add_sprites.append((454, sprite.objx - 128, sprite.objy - 128))

                if sprite.type == 247 and sprite.spritedata[5] & 0xF == 1:
                    sprite.spritedata = sprite.spritedata[0:5] + chr(0) + sprite.spritedata[6:]

                if sprite.type == 323:
                    if sprite.spritedata[4] & 0xF == 4:
                        sprite.spritedata = sprite.spritedata[0:4] + chr(1) + sprite.spritedata[5:]

                    if sprite.spritedata[2] & 0xF < (sprite.spritedata[3] & 0xF0) >> 4:
                        sprite.spritedata = sprite.spritedata[0:2] + chr((sprite.spritedata[3] & 0xF0) >> 4) + sprite.spritedata[3:]

                if sprite.type == 449 and (sprite.spritedata[5] & 0xF0) >> 4 == 1:
                    sprite.spritedata = sprite.spritedata[0:5] + chr(0) + sprite.spritedata[6:]

                if sprite.type == 479 and sprite.spritedata[4] & 0xF == 1:
                    if (sprite.spritedata[4] & 0xF0) >> 4 == 1:
                        sprite.spritedata = sprite.spritedata[0:4] + chr(0x10) + sprite.spritedata[5:]
                    else:
                        sprite.spritedata = sprite.spritedata[0:4] + chr(0) + sprite.spritedata[5:]

                if sprite.type == 481:
                    if sprite.spritedata[5] & 0xF > 2:
                        sprite.spritedata = sprite.spritedata[0:5] + chr(2) + sprite.spritedata[6:]

                    add_sprites.append((419, sprite.objx - 128, sprite.objy - 128))

            if globals_.mainWindow is not None:
                for id_, x, y in add_sprites:
                    globals_.mainWindow.CreateSprite(x, y, id_, bytes(8))

                globals_.mainWindow.scene.update()

    def check_sprite_max(self, mode='f'):
        """
        Determines if the number of sprites in the current area is > 1000
        """
        max_sprite_num = 1000

        problem = len(globals_.Area.sprites) > max_sprite_num

        if mode == 'c':
            return problem

        if not problem:
            return None

        if globals_.mainWindow is not None:
            sprite: SpriteItem
            for sprite in globals_.Area.sprites[max_sprite_num:]:
                sprite.delete()
                sprite.setSelected(False)
                globals_.mainWindow.scene.removeItem(sprite)

            globals_.Area.sprites = globals_.Area.sprites[:max_sprite_num]
            globals_.mainWindow.scene.update()
            globals_.mainWindow.levelOverview.update()

    def check_duplicate_entrance(self, mode='f'):
        """
        Checks for entrances with duplicate IDs
        """
        ids = []

        ent: EntranceItem
        for ent in globals_.Area.entrances:
            if ent.entid in ids:
                if mode == 'c':
                    return True

                # Find the lowest available ID
                getids = [False for _ in range(256)]
                for check in globals_.Area.entrances:
                    getids[check.entid] = True

                minimumID = getids.index(False)

                ent.entid = minimumID
                ent.UpdateTooltip()
                ent.UpdateListItem()

            ids.append(ent.entid)

        return False

    def check_start_entrance(self, mode='f'):
        """
        Determines if there is a start entrance or not
        """
        # Only applies to Area 1
        if globals_.Area.areanum != 1:
            return False

        start: EntranceItem | None = None
        end: EntranceItem
        for ent in globals_.Area.entrances:
            if ent.entid == globals_.Area.startEntrance:
                start = ent
            else:
                problem = False

        problem = start is None

        if mode == 'c':
            return problem
        elif problem:
            if globals_.mainWindow is not None:
                # TODO: Maybe place it 6 blocks right, 3 blocks up from Zone 1's bottom-left corner?
                globals_.mainWindow.CreateEntrance(1024, 512, globals_.Area.startEntrance)

    def check_entrance_near_edge(self, mode='f'):
        """
        Checks if the start entrance is too close to the left zone edge
        """
        if not globals_.Area.zones:
            return False

        # If the entrance isn't even in a zone, return
        if self.check_entrance_out_zone('c'):
            return False

        start: EntranceItem | None = None
        ent: EntranceItem
        for ent in globals_.Area.entrances:
            if ent.entid == globals_.Area.startEntrance:
                start = ent

        if start is None:
            return False

        first_zone_idx = SLib.MapPositionToZoneID(globals_.Area.zones, start.objx, start.objy)
        if first_zone_idx == -1:
            return False

        first_zone: ZoneItem = globals_.Area.zones[first_zone_idx]
        offset = 24 * 8  # 8 blocks from left edge

        problem = start.objx < first_zone.objx + offset
        if mode == 'c':
            return problem
        elif problem:
            start.setPos((first_zone.objx + offset) * 1.5, start.objy * 1.5)

    def check_entrance_out_zone(self, mode='f'):
        """
        Checks if any entrances are not inside of a zone
        """
        if not globals_.Area.zones:
            return False

        left_offset = 24 * 8  # 8 blocks away from the left zone edge
        ent: EntranceItem
        for ent in globals_.Area.entrances:
            x = ent.objx
            y = ent.objy
            zone_idx = SLib.MapPositionToZoneID(globals_.Area.zones, x, y)
            if zone_idx == -1:
                return False

            zone: ZoneItem = globals_.Area.zones[zone_idx]

            if x < zone.objx:
                problem = True
            elif x > zone.objx + zone.width:
                problem = True
            elif y < zone.objy - 64:
                problem = True
            elif y > zone.objy + zone.height + 192:
                problem = True
            else:
                problem = False

            if problem and mode == 'c':
                return True
            elif problem:
                if x < zone.objx:
                    newx = zone.objx + left_offset
                elif x > zone.objx + zone.width:
                    newx = zone.objx + zone.width - 16
                else:
                    newx = ent.objx

                # Entrances can be placed a few blocks above the top zone border
                if y < (zone.objy - 64):
                    newy = zone.objy - 64
                elif y > zone.objy + zone.height:
                    newy = zone.objy + zone.height - 32
                else:
                    newy = ent.objy
    
                ent.objx = newx
                ent.objy = newy
                ent.setPos(int(newx * 1.5), int(newy * 1.5))

                if globals_.mainWindow is not None:
                    globals_.mainWindow.scene.update()

        return False

    def check_zone_max(self, mode='f'):
        """
        Checks if there are too many zones in this area
        """

        problem = len(globals_.Area.zones) > 6

        if mode == 'c':
            return problem
        elif problem:
            globals_.Area.zones = globals_.Area.zones[:6]

            if globals_.mainWindow is not None:
                globals_.mainWindow.scene.update()
                globals_.mainWindow.levelOverview.update()

    def check_no_zone_exist(self, mode='f'):
        """
        Checks if there are no zones in this area
        """
        problem = not globals_.Area.zones
        if mode == 'c':
            return problem

        if not problem:
            return

        # Make a default zone
        if globals_.mainWindow is not None:
            globals_.mainWindow.CreateZone(16, 16)

    def check_zone_proximity(self, mode='f'):
        """
        Checks for any zones which are too close together or are overlapping
        """
        padding = 4 # Minimum blocks between zones
        check: ZoneItem
        against: ZoneItem

        # Reversed because generally Zone 1 is most important, 1 is less, 2 is lesser, etc.
        for check in reversed(globals_.Area.zones):
            chk_rect = check.ZoneRect
            for against in globals_.Area.zones:
                if check is against:
                    continue

                against_rect = against.ZoneRect.adjusted(-16 * padding, -16 * padding, 16 * padding, 16 * padding)
                if chk_rect.intersects(against_rect):
                    if mode == 'c':
                        return True
                    else:
                        center = chk_rect.center()

                        # Figure out what to adjust
                        if against_rect.contains(chk_rect) or chk_rect.contains(against_rect):
                            # One inside the other
                            axes = [None, 'both']
                        elif abs(center.x() - against_rect.center().x()) > abs(center.y() - against_rect.center().y()):
                            # Horizontally positioned
                            if against_rect.center().x() > center.x():
                                # Shrink the right
                                axes = [None, 'w']
                            else:
                                # Shrink the left
                                axes = ['x', 'w']
                        else:
                            # Vertically positioned
                            if against_rect.center().y() < center.y():
                                # Shrink the top
                                axes = ['y', 'h']
                            else:
                                # Shrink the bottom
                                axes = [None, 'h']

                        # Make the actual adjustments
                        if globals_.mainWindow is not None:
                            checkzone = check.ZoneRect
                            oldCoords = checkzone.getCoords()
                            while checkzone.intersects(against_rect):
                                if axes[0] is None:
                                    pass
                                elif axes[0] == 'x':
                                    check.objx += 1
                                else:
                                    check.objy += 1

                                if axes[1] == 'both':
                                    check.objx += 1
                                    check.objy += 1
                                elif axes[1] == 'w':
                                    check.width -= 1
                                else:
                                    check.height -= 1

                                check.width = max(check.width, 204)
                                check.height = max(check.height, 112)

                                check.UpdateRects()
                                check.setPos(int(check.objx * 1.5), int(check.objy * 1.5))
                                globals_.mainWindow.scene.update()
                                checkzone = check.ZoneRect

                                if oldCoords == checkzone.getCoords():
                                    break

                                oldCoords = checkzone.getCoords()

                            globals_.mainWindow.scene.update()

        return False

    def check_zone_on_area_edge(self, mode='f'):
        """
        Checks for any zones which are too close to the area edges, and moves them
        """
        area_width = 16384
        area_height = 8192

        zone: ZoneItem
        for zone in globals_.Area.zones:
            if (zone.objx < 16) or (zone.objy < 16) or (zone.objx + zone.width > area_width - 16) or (zone.objy + zone.height > area_height - 16):
                if mode == 'c':
                    return False
                else:
                    zone.objx = max(zone.objx, 16)
                    zone.objy = max(zone.objx, 16)

                    if zone.objx + zone.width > area_width - 16:
                        zone.width = area_width - zone.objx - 16

                    if zone.objy + zone.height > area_height - 16:
                        zone.height = area_height - zone.objy - 16
                    zone.UpdateRects()

                    if globals_.mainWindow is not None:
                        globals_.mainWindow.scene.update()

        return False

    # TODO: What is this??? Needs more research
    def check_no_bias(self, mode='f'):
        """
        Checks for any zones which do not have bias enabled
        """
        fix = {'0 0': (0, 1),
               '0 7': (0, 6),
               '0 11': (0, 4),
               '3 2': (0, 3),
               '3 7': (3, 3),  # This doesn't always appear
               '6 0': (6, 2),  # to work due to inconsistencies
               '6 7': (6, 6),  # in the editor, but I'm pretty
               '6 11': (6, 4),  # sure it's written correctly.
               '1 0': (1, 1),
               '1 7': (1, 10),
               '1 11': (1, 4),
               '4 2': (1, 3),
               '4 7': (4, 3)}

        zone: ZoneItem
        for zone in globals_.Area.zones:
            check = str(zone.cammode) + ' ' + str(zone.camzoom)
            if check in fix:
                if mode == 'c':
                    return False
                else:
                    zone.cammode = fix[check][0]
                    zone.camzoom = fix[check][1]

        return False

    # TODO: Fix this? Also make it actually useful
    def check_zone_max_size(self, mode='f'):
        """
        Checks for any zones which may be too large
        """
        max_area = 16384 # Blocks (approximated value)

        zone: ZoneItem
        for zone in globals_.Area.zones:
            if int((zone.width / 32) * (zone.height / 32)) > max_area * 8:
                if mode == 'c':
                    return False
                else:
                    # Shrink it by the larger dimension
                    if zone.width > zone.height:
                        zone.width = int(256 * max_area / zone.height)
                    else:
                        zone.height = int(256 * max_area / zone.width)
                    zone.UpdateRects()

                    if globals_.mainWindow is not None:
                        globals_.mainWindow.scene.update()

        return False
