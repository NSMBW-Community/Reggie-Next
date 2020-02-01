import os
import random

from PyQt5 import QtGui, QtCore, QtWidgets
import globals_
from ui import GetIcon
# from levelitems import ObjectItem  # cyclic import

class ObjectItem:
    ...

class QuickPaintOperations:
    """
    All of the actions/functions/operations/whatever programmed for the quick paint tool are stored in here.
    """
    color_shift = 0
    color_shift_mouseGridPosition = None
    object_optimize_database = []
    object_search_database = {}

    @staticmethod
    def _getMaxSize(qp_data):
        """
        Gets the maximum size of all the objects in the quick paint configuration widget.
        """
        res = 1
        for type in qp_data:
            res = max(res, qp_data[type]['ow'], qp_data[type]['oh'])

        return res

    @staticmethod
    def optimizeObjects(FromQPWidget=False):
        """
        This function merges all touching objects of the same type. We don't want huge files for level data.
        Nor do we want an island to be completely made up of 1x1 objects. And we most definately don't want
        objects more than 1x1 to repeat only the first tile in them.
        """
        optimize_memory = []

        if FromQPWidget: lr = [-1]
        else: lr = range(len(globals_.Area.layers))

        for ln in lr:
            objects_inside_optimize_boxes = []
            InfiniteLoopStopper = [-1, 0]

            while len(list(filter(lambda i: i.layer == ln, QuickPaintOperations.object_optimize_database))) > 0:
                from math import sqrt

                obj = min(list(filter(lambda i: i.layer == ln, QuickPaintOperations.object_optimize_database)),
                          key=lambda i: sqrt(i.objx ** 2 + i.objy ** 2))
                w = 1024
                cobj = obj
                calculated_dimensions = []
                atd_archive = []

                for y in range(512):
                    if w != 1024:
                        calculated_dimensions.append((w, y))
                    cobj = QuickPaintOperations.searchObj(obj.layer, obj.objx, obj.objy + y)

                    if cobj is None:
                        break

                    for x in range(w):
                        cobj = QuickPaintOperations.searchObj(obj.layer, obj.objx + x, obj.objy + y)
                        atd_archive.append((
                            x, y, None if not hasattr(cobj, 'modifiedForSize') else cobj.modifiedForSize,
                            None if not hasattr(cobj, 'autoTileType') else cobj.autoTileType))

                        if (not cobj or cobj in objects_inside_optimize_boxes
                            or cobj.tileset != obj.tileset or cobj.type != obj.type):
                            w = x
                            break

                # This somewhat helps remove the bug when painting over slopes.
                calculated_dimensions = list(filter(lambda i: i[0] != 0 and i[1] != 0, calculated_dimensions))
                if True in map(lambda i: i[1] > 1, calculated_dimensions):
                    calculated_dimensions = list(filter(lambda i: i[1] > 1, calculated_dimensions))

                if len(calculated_dimensions) > 0:
                    lets_use_these_dimensions = max(calculated_dimensions, key=lambda i: i[0] * i[1])

                else:
                    lets_use_these_dimensions = [0, 0, []]

                if lets_use_these_dimensions[0] * lets_use_these_dimensions[1] == 0:
                    QuickPaintOperations.object_optimize_database.remove(obj)
                    continue

                calculated_rectangle = (
                    obj.objx, obj.objy, lets_use_these_dimensions[0], lets_use_these_dimensions[1], obj,
                    list(set(atd_archive)))
                optimize_memory.append(calculated_rectangle)

                for y in range(calculated_rectangle[1], calculated_rectangle[1] + calculated_rectangle[3]):
                    for x in range(calculated_rectangle[0], calculated_rectangle[0] + calculated_rectangle[2]):
                        cobj = QuickPaintOperations.searchObj(ln, x, y)

                        if cobj in QuickPaintOperations.object_optimize_database:
                            QuickPaintOperations.object_optimize_database.remove(cobj)
                            objects_inside_optimize_boxes.append(cobj)

                if InfiniteLoopStopper[0] == len(list(filter(lambda i: i.layer == ln, QuickPaintOperations.object_optimize_database))):
                    InfiniteLoopStopper[1] += 1

                    if InfiniteLoopStopper[1] >= 20:
                        break

                else:
                    InfiniteLoopStopper[1] = 0

                InfiniteLoopStopper[0] = len(list(filter(lambda i: i.layer == ln, QuickPaintOperations.object_optimize_database)))

            for obj in objects_inside_optimize_boxes:
                if obj not in map(lambda i: i[4], optimize_memory):
                    if FromQPWidget:
                        if obj in globals_.mainWindow.quickPaint.scene.display_objects:
                            obj.RemoveFromSearchDatabase()
                            globals_.mainWindow.quickPaint.scene.display_objects.remove(obj)

                    else:
                        obj.delete()
                        obj.setSelected(False)
                        globals_.mainWindow.scene.removeItem(obj)

            for rect in optimize_memory:
                if rect is not None:
                    obj = rect[4]
                    obj.atd_archive = rect[5]
                    obj.objx = rect[0]
                    obj.objy = rect[1]
                    obj.width = rect[2]
                    obj.height = rect[3]
                    obj.updateObjCache()
                    obj.UpdateRects()
                    obj.UpdateTooltip()

        QuickPaintOperations.object_optimize_database = []

    @staticmethod
    def prePaintObject(ln, layer, x, y, z):
        """
        Schedules an object to be added by adding the coordinates to the list of pre-painted objects.
        """
        if not hasattr(QuickPaintOperations, 'prePaintedObjects'):
            QuickPaintOperations.prePaintedObjects = {}

        if not ('%i_%i' % (x, y) in QuickPaintOperations.prePaintedObjects):
            QuickPaintOperations.prePaintedObjects['%i_%i' % (x, y)] = {'ln': ln, 'layer': layer, 'x': x, 'y': y,
                                                                        'z': z, 'r': int(random.random() * 127) + 128,
                                                                        'g': int(random.random() * 127) + 128,
                                                                        'b': int(random.random() * 127) + 128}
        globals_.mainWindow.scene.invalidate()

    @staticmethod
    def PaintFromPrePaintedObjects():
        """
        Creates and adds all the objects scheduled from the list of pre-painted objects to the level.
        """
        QuickPaintOperations.sliceObjRange(QuickPaintOperations.prePaintedObjects)
        if hasattr(QuickPaintOperations, 'prePaintedObjects'):
            for ppobj in QuickPaintOperations.prePaintedObjects:
                # We do this action twice to make sure there is no trailing.
                QuickPaintOperations.AddObj(QuickPaintOperations.prePaintedObjects[ppobj]['ln'],
                                            QuickPaintOperations.prePaintedObjects[ppobj]['layer'],
                                            QuickPaintOperations.prePaintedObjects[ppobj]['x'],
                                            QuickPaintOperations.prePaintedObjects[ppobj]['y'],
                                            QuickPaintOperations.prePaintedObjects[ppobj]['z'])
                QuickPaintOperations.AddObj(QuickPaintOperations.prePaintedObjects[ppobj]['ln'],
                                            QuickPaintOperations.prePaintedObjects[ppobj]['layer'],
                                            QuickPaintOperations.prePaintedObjects[ppobj]['x'],
                                            QuickPaintOperations.prePaintedObjects[ppobj]['y'],
                                            QuickPaintOperations.prePaintedObjects[ppobj]['z'])

        QuickPaintOperations.prePaintedObjects.clear()
        globals_.mainWindow.scene.invalidate()

    @staticmethod
    def preEraseObject(ln, layer, x, y):
        """
        Schedules an object to be removed by adding the coordinates to the list of pre-painted objects.
        """
        if not hasattr(QuickPaintOperations, 'prePaintedObjects'):
            QuickPaintOperations.prePaintedObjects = {}

        if not ('%i_%i' % (x, y) in QuickPaintOperations.prePaintedObjects):
            QuickPaintOperations.prePaintedObjects['%i_%i' % (x, y)] = {'ln': ln, 'layer': layer, 'x': x, 'y': y,
                                                                        'z': 0, 'r': int(random.random() * 127),
                                                                        'g': int(random.random() * 127), 'b': int(random.random() * 127)}

    @staticmethod
    def EraseFromPreErasedObjects():
        """
        For every coordinate from the list of pre-painted objects, an object is removed from the level.
        """
        QuickPaintOperations.sliceObjRange(QuickPaintOperations.prePaintedObjects)
        if hasattr(QuickPaintOperations, 'prePaintedObjects'):
            for ppobj in QuickPaintOperations.prePaintedObjects:
                # We do this action twice to make sure there is no trailing.
                QuickPaintOperations.EraseObj(QuickPaintOperations.prePaintedObjects[ppobj]['ln'],
                                              QuickPaintOperations.prePaintedObjects[ppobj]['layer'],
                                              QuickPaintOperations.prePaintedObjects[ppobj]['x'],
                                              QuickPaintOperations.prePaintedObjects[ppobj]['y'])
                QuickPaintOperations.EraseObj(QuickPaintOperations.prePaintedObjects[ppobj]['ln'],
                                              QuickPaintOperations.prePaintedObjects[ppobj]['layer'],
                                              QuickPaintOperations.prePaintedObjects[ppobj]['x'],
                                              QuickPaintOperations.prePaintedObjects[ppobj]['y'])

        QuickPaintOperations.prePaintedObjects.clear()
        globals_.mainWindow.scene.invalidate()

    @staticmethod
    def AddObj(ln, layer, x, y, z):
        """
        Adds an object to the level and automatically fixes the tiles of islands it may be touching.
        """
        if globals_.mainWindow.quickPaint is not None and globals_.mainWindow.quickPaint.scene is not None:
            qpscn = globals_.mainWindow.quickPaint.scene
            qp_data = qpscn.object_database

            if qp_data['base']['i'] is not None and qp_data['base']['ts'] is not None and qp_data['base'][
                't'] is not None:
                mw = globals_.mainWindow
                objBehindThisOne = QuickPaintOperations.searchObj(ln, x, y)

                while objBehindThisOne is not None:
                    objBehindThisOne.delete()

                    if objBehindThisOne in QuickPaintOperations.object_optimize_database:
                        QuickPaintOperations.object_optimize_database.remove(objBehindThisOne)

                    objBehindThisOne.setSelected(False)
                    mw.scene.removeItem(objBehindThisOne)
                    objBehindThisOne = QuickPaintOperations.searchObj(ln, x, y)

                obj = globals_.mainWindow.CreateObject(qp_data['base']['ts'], qp_data['base']['t'], ln, x, y)

                if obj not in QuickPaintOperations.object_optimize_database:
                    QuickPaintOperations.object_optimize_database.append(obj)

                # This next function has to repeated multiple times at multiple places in and around this object.
                # Otherwise, you will leave artifacts when painting with bigger objects.
                QuickPaintOperations.autoTileObj(ln, obj)
                for r in range(QuickPaintOperations._getMaxSize(qp_data) + 2):
                    for a in range(-r, r):
                        sobj = QuickPaintOperations.searchObj(ln, obj.objx + a, obj.objy - r)

                        if sobj is not None:
                            QuickPaintOperations.autoTileObj(ln, sobj)

                    for a in range(-r, r):
                        sobj = QuickPaintOperations.searchObj(ln, obj.objx + r, obj.objy + a)

                        if sobj is not None:
                            QuickPaintOperations.autoTileObj(ln, sobj)

                    for a in range(-r, r):
                        sobj = QuickPaintOperations.searchObj(ln, obj.objx - a, obj.objy + r)

                        if sobj is not None:
                            QuickPaintOperations.autoTileObj(ln, sobj)

                    for a in range(-r, r):
                        sobj = QuickPaintOperations.searchObj(ln, obj.objx - r, obj.objy - a)

                        if sobj is not None:
                            QuickPaintOperations.autoTileObj(ln, sobj)

    @staticmethod
    def EraseObj(ln, layer, x, y):
        """
        Removes an object from the level and automatically fixes the tiles of islands it may have been touching.
        """
        if globals_.mainWindow.quickPaint is not None and globals_.mainWindow.quickPaint.scene is not None:
            qpscn = globals_.mainWindow.quickPaint.scene
            qp_data = qpscn.object_database

            if qp_data['base']['i'] is not None and qp_data['base']['ts'] is not None and qp_data['base'][
                't'] is not None:
                mw = globals_.mainWindow
                obj = QuickPaintOperations.searchObj(ln, x, y)

                if obj is not None:
                    obj.delete()
                    obj.setSelected(False)

                    if obj in QuickPaintOperations.object_optimize_database:
                        QuickPaintOperations.object_optimize_database.remove(obj)

                    mw.scene.removeItem(obj)

                    for r in range(QuickPaintOperations._getMaxSize(qp_data) + 2):
                        for a in range(-r, r):
                            sobj = QuickPaintOperations.searchObj(ln, obj.objx + a, obj.objy - r)

                            if sobj is not None:
                                QuickPaintOperations.autoTileObj(ln, sobj)

                        for a in range(-r, r):
                            sobj = QuickPaintOperations.searchObj(ln, obj.objx + r, obj.objy + a)

                            if sobj is not None:
                                QuickPaintOperations.autoTileObj(ln, sobj)

                        for a in range(-r, r):
                            sobj = QuickPaintOperations.searchObj(ln, obj.objx - a, obj.objy + r)

                            if sobj is not None:
                                QuickPaintOperations.autoTileObj(ln, sobj)

                        for a in range(-r, r):
                            sobj = QuickPaintOperations.searchObj(ln, obj.objx - r, obj.objy - a)

                            if sobj is not None:
                                QuickPaintOperations.autoTileObj(ln, sobj)

    @staticmethod
    def searchObj(layer, x, y):
        """
        Quickly searches for an object at the specified position.
        """
        if not QuickPaintOperations.object_search_database.get((x, y, layer)):
            return None

        if len(QuickPaintOperations.object_search_database[(x, y, layer)]) <= 0:
            return None

        return QuickPaintOperations.object_search_database[(x, y, layer)][0]

    @staticmethod
    def sliceObjRange(posList):
        """
        For every object and objects touching that object, they will slice into 1x1 objects.
        """
        connected_objects = []
        objlist = []
        for pos in map(lambda i: (posList[i]['x'], posList[i]['y'], posList[i]['ln']), posList):
            qpscn = globals_.mainWindow.quickPaint.scene
            qp_data = qpscn.object_database
            # pronounced [BOB-JAY] lol
            # Way to go Robert!
            # Actually Bobj stands for base object, because these are the objects we start with as they lie
            # on the positions where the user has painted over on the widget.
            # - John10v10
            bobj = QuickPaintOperations.searchObj(pos[2], pos[0], pos[1])

            if bobj is not None and bobj not in connected_objects:
                connected_objects.append(bobj)
                objlist.append(bobj)

            for r in range(QuickPaintOperations._getMaxSize(qp_data) + 2):
                for a in range(-r, r):
                    bobj = QuickPaintOperations.searchObj(pos[2], pos[0] + a, pos[1] - r)

                    if bobj is not None and bobj not in connected_objects:
                        connected_objects.append(bobj)
                        objlist.append(bobj)

                for a in range(-r, r):
                    bobj = QuickPaintOperations.searchObj(pos[2], pos[0] + r, pos[1] + a)

                    if bobj is not None and bobj not in connected_objects:
                        connected_objects.append(bobj)
                        objlist.append(bobj)

                for a in range(-r, r):
                    bobj = QuickPaintOperations.searchObj(pos[2], pos[0] - a, pos[1] + r)

                    if bobj is not None and bobj not in connected_objects:
                        connected_objects.append(bobj)
                        objlist.append(bobj)

                for a in range(-r, r):
                    bobj = QuickPaintOperations.searchObj(pos[2], pos[0] - r, pos[1] - a)

                    if bobj is not None and bobj not in connected_objects:
                        connected_objects.append(bobj)
                        objlist.append(bobj)

        no_more_found = False
        while not no_more_found:
            preobjlist = []
            for obj in objlist:
                for x in range(obj.objx - 1, obj.objx + obj.width + 1):
                    for y in range(obj.objy - 1, obj.objy + obj.height + 1):
                        sobj = QuickPaintOperations.searchObj(obj.layer, x, y)

                        if sobj is not None and sobj is not obj and sobj not in connected_objects:
                            still_append = True

                            for pos in map(lambda i: (posList[i]['x'], posList[i]['y']), posList):
                                if abs(x - pos[0]) > r or abs(y - pos[1]) > r:
                                    still_append = False

                            if still_append:
                                preobjlist.append(sobj)
                                connected_objects.append(sobj)

            if len(preobjlist) <= 0:
                no_more_found = True

            else:
                objlist = preobjlist

        connected_objects = list(filter(lambda i: i is not None, list(set(connected_objects))))
        for robj in connected_objects:
            QuickPaintOperations.sliceObj(robj)

    @staticmethod
    def sliceObj(obj, px=None, py=None):
        """
        Slices this object into 1x1 objects.
        """
        if not obj or (obj.width == 1 and obj.height == 1):
            if obj not in QuickPaintOperations.object_optimize_database and obj:
                QuickPaintOperations.object_optimize_database.append(obj)

            return obj

        out_obj = None
        mw = globals_.mainWindow
        objx = obj.objx
        objy = obj.objy
        w = obj.width
        h = obj.height
        l = obj.layer
        ts = obj.tileset
        t = obj.original_type
        atd_archive = []

        if hasattr(obj, 'atd_archive') and obj.atd_archive:
            atd_archive = obj.atd_archive

        skip = []
        x = 0
        y = 0
        if obj.objdata:
            for row in obj.objdata:
                x = 0

                for tile in row:
                    if tile == -1:
                        skip.append((x, y))

                    x += 1

                y += 1

        if obj in globals_.Area.layers[obj.layer]:
            obj.delete()
            obj.setSelected(False)
            mw.scene.removeItem(obj)

        if obj in QuickPaintOperations.object_optimize_database:
            QuickPaintOperations.object_optimize_database.remove(obj)

        ln = 0
        for y in range(h):
            for x in range(w):
                if (x, y) in skip: continue

                objBehindThisOne = QuickPaintOperations.sliceObj(QuickPaintOperations.searchObj(ln, x + objx, y + objy),
                                                                 x + objx, y + objy)
                if objBehindThisOne is not None:
                    objBehindThisOne.delete()
                    objBehindThisOne.setSelected(False)

                    if objBehindThisOne in QuickPaintOperations.object_optimize_database:
                        QuickPaintOperations.object_optimize_database.remove(objBehindThisOne)

                    mw.scene.removeItem(objBehindThisOne)

                sobj = globals_.mainWindow.CreateObject(
                    ts, t, l, x + objx, y + objy
                )

                atd = list(filter(lambda i: i[0] == x and i[1] == y, atd_archive))

                if atd is not None and len(atd) > 0:
                    sobj.modifiedForSize = atd[0][2]
                    sobj.autoTileType = atd[0][3]

                if sobj not in QuickPaintOperations.object_optimize_database:
                    QuickPaintOperations.object_optimize_database.append(sobj)

                if sobj.objx == px and sobj.objy == py:
                    out_obj = sobj

        return out_obj

    @staticmethod
    def isObjectInQPwidget(obj):
        """
        Checks if object is in the quick paint configuration widget.
        """
        if obj is None: return False

        qpscn = globals_.mainWindow.quickPaint.scene
        qp_data = qpscn.object_database

        for t in qp_data:
            if qp_data[t] is not None and qp_data[t]['ts'] == obj.tileset and qp_data[t]['t'] == obj.original_type:
                return True

        return False

    @staticmethod
    def countUpLeft(layer, obj, maxX, maxY):
        """
        Checks if object is inside the top-left corner within a given boundary.
        """
        for x in range(maxX + 1):
            for y in range(maxY + 1):
                if QuickPaintOperations.searchObj(layer, obj.objx - x, obj.objy - y) is None: return True

        return False

    @staticmethod
    def countUpRight(layer, obj, maxX, maxY):
        """
        Checks if object is inside the top-right corner within a given boundary.
        """
        for x in range(maxX + 1):
            for y in range(maxY + 1):
                if QuickPaintOperations.searchObj(layer, obj.objx + x, obj.objy - y) is None: return True

        return False

    @staticmethod
    def countDownLeft(layer, obj, maxX, maxY):
        """
        Checks if object is inside the down-left corner within a given boundary.
        """
        for x in range(maxX + 1):
            for y in range(maxY + 1):
                if QuickPaintOperations.searchObj(layer, obj.objx - x, obj.objy + y) is None: return True

        return False

    @staticmethod
    def countDownRight(layer, obj, maxX, maxY):
        """
        Checks if object is inside the down-right corner within a given boundary.
        """
        for x in range(maxX + 1):
            for y in range(maxY + 1):
                if QuickPaintOperations.searchObj(layer, obj.objx + x, obj.objy + y) is None: return True

        return False

    @staticmethod
    def countUp(layer, obj, maxY):
        """
        Checks if object is not too far underneath the ground within a given boundary.
        """
        for y in range(maxY + 1):
            if QuickPaintOperations.searchObj(layer, obj.objx, obj.objy - y) is None: return True

        return False

    @staticmethod
    def countDown(layer, obj, maxY):
        """
        Checks if object is not too far above the bottom within a given boundary.
        """
        for y in range(maxY + 1):
            if QuickPaintOperations.searchObj(layer, obj.objx, obj.objy + y) is None: return True

        return False

    @staticmethod
    def countLeft(layer, obj, maxX):
        """
        Checks if object is not too far to the right of the left wall within a given boundary.
        """
        for x in range(maxX + 1):
            if QuickPaintOperations.searchObj(layer, obj.objx - x, obj.objy) is None: return True

        return False

    @staticmethod
    def countRight(layer, obj, maxX):
        """
        Checks if object is not too far to the left of the right wall within a given boundary.
        """
        for x in range(maxX + 1):
            if QuickPaintOperations.searchObj(layer, obj.objx + x, obj.objy) is None: return True

        return False

    @staticmethod
    def autoTileObj(layer, obj):
        """
        Automatically picks the tile that best fits its position.
        It's a big process, but I hope it works well enough for Reggie users.
        """
        if globals_.mainWindow.quickPaint and globals_.mainWindow.quickPaint.scene and obj:
            qpscn = globals_.mainWindow.quickPaint.scene
            qp_data = qpscn.object_database
            surrounding_objects = {
                'TopLeft': QuickPaintOperations.searchObj(layer, obj.objx - 1, obj.objy - 1),
                'Top': QuickPaintOperations.searchObj(layer, obj.objx, obj.objy - 1),
                'TopRight': QuickPaintOperations.searchObj(layer, obj.objx + 1, obj.objy - 1),
                'Left': QuickPaintOperations.searchObj(layer, obj.objx - 1, obj.objy),
                'Right': QuickPaintOperations.searchObj(layer, obj.objx + 1, obj.objy),
                'BottomLeft': QuickPaintOperations.searchObj(layer, obj.objx - 1, obj.objy + 1),
                'Bottom': QuickPaintOperations.searchObj(layer, obj.objx, obj.objy + 1),
                'BottomRight': QuickPaintOperations.searchObj(layer, obj.objx + 1, obj.objy + 1),
            }

            if QuickPaintOperations.isObjectInQPwidget(obj):
                flag = 0x0
                if QuickPaintOperations.isObjectInQPwidget(surrounding_objects['TopLeft']): flag |= 0x1
                if QuickPaintOperations.isObjectInQPwidget(surrounding_objects['Top']): flag |= 0x2
                if QuickPaintOperations.isObjectInQPwidget(surrounding_objects['TopRight']): flag |= 0x4
                if QuickPaintOperations.isObjectInQPwidget(surrounding_objects['Left']): flag |= 0x8
                if QuickPaintOperations.isObjectInQPwidget(surrounding_objects['Right']): flag |= 0x10
                if QuickPaintOperations.isObjectInQPwidget(surrounding_objects['BottomLeft']): flag |= 0x20
                if QuickPaintOperations.isObjectInQPwidget(surrounding_objects['Bottom']): flag |= 0x40
                if QuickPaintOperations.isObjectInQPwidget(surrounding_objects['BottomRight']): flag |= 0x80

                typeToTile = 'base'
                if flag & 0xdb == 0xB:
                    typeToTile = qpscn.pickObject('bottomRight')
                if flag & 0x7e == 0x16:
                    typeToTile = qpscn.pickObject('bottomLeft')
                if flag & 0xdb == 0xd0:
                    typeToTile = qpscn.pickObject('topLeft')
                if flag & 0x7e == 0x68:
                    typeToTile = qpscn.pickObject('topRight')
                if flag & 0x5a == 0x1a:
                    typeToTile = qpscn.pickObject('bottom')
                if flag & 0x5a == 0x58:
                    typeToTile = qpscn.pickObject('top')
                if flag & 0x5a == 0x52:
                    typeToTile = qpscn.pickObject('left')
                if flag & 0x5a == 0x4a:
                    typeToTile = qpscn.pickObject('right')
                if flag & 0xdb == 0x5b:
                    typeToTile = qpscn.pickObject('topLeftCorner')
                if flag & 0xdb == 0xda:
                    typeToTile = qpscn.pickObject('bottomRightCorner')
                if flag & 0x7e == 0x5e:
                    typeToTile = qpscn.pickObject('topRightCorner')
                if flag & 0x7e == 0x7a:
                    typeToTile = qpscn.pickObject('bottomLeftCorner')

                obj.modifiedForSize = 0x00
                obj.autoTileType = typeToTile
                if typeToTile is not None and qp_data.get(typeToTile) is not None and qp_data[typeToTile][
                    'i'] is not None:
                    obj.tileset = qp_data[typeToTile]['ts']
                    obj.type = qp_data[typeToTile]['t']
                    obj.original_type = qp_data[typeToTile]['t']
                    if qp_data['topLeftCorner']['i'] is not None:
                        for y in range(qp_data['topLeftCorner']['oh']):
                            for x in range(qp_data['topLeftCorner']['ow']):
                                if x > 0 or y > 0:
                                    sobj = QuickPaintOperations.searchObj(layer, obj.objx + x, obj.objy + y)

                                    if (sobj and sobj.width == 1 and sobj.height == 1
                                        and (hasattr(sobj, 'autoTileType') and sobj.autoTileType == 'topLeftCorner')
                                        and not (hasattr(sobj, 'modifiedForSize')
                                                 and sobj.modifiedForSize & 0x100 == 0x100)):
                                        obj.tileset = sobj.tileset
                                        obj.type = sobj.original_type
                                        obj.original_type = sobj.original_type
                                        obj.modifiedForSize |= 0x100

                    if qp_data['topRightCorner']['i'] is not None:
                        for y in range(qp_data['topRightCorner']['oh']):
                            for x in range(qp_data['topRightCorner']['ow']):
                                if x > 0 or y > 0:
                                    sobj = QuickPaintOperations.searchObj(layer, obj.objx - x, obj.objy + y)

                                    if (sobj and sobj.width == 1 and sobj.height == 1
                                        and (hasattr(sobj, 'autoTileType') and sobj.autoTileType == 'topRightCorner')
                                        and not (hasattr(sobj, 'modifiedForSize')
                                                 and sobj.modifiedForSize & 0x200 == 0x200)):
                                        obj.tileset = sobj.tileset
                                        obj.type = sobj.original_type
                                        obj.original_type = sobj.original_type
                                        obj.modifiedForSize |= 0x200

                    if qp_data['bottomLeftCorner']['i'] is not None:
                        for y in range(qp_data['bottomLeftCorner']['oh']):
                            for x in range(qp_data['bottomLeftCorner']['ow']):
                                if x > 0 or y > 0:
                                    sobj = QuickPaintOperations.searchObj(layer, obj.objx + x, obj.objy - y)

                                    if (sobj and sobj.width == 1 and sobj.height == 1
                                        and (hasattr(sobj, 'autoTileType') and sobj.autoTileType == 'bottomLeftCorner')
                                        and not (hasattr(sobj, 'modifiedForSize')
                                                 and sobj.modifiedForSize & 0x400 == 0x400)):
                                        obj.tileset = sobj.tileset
                                        obj.type = sobj.original_type
                                        obj.original_type = sobj.original_type
                                        obj.modifiedForSize |= 0x400

                    if qp_data['bottomRightCorner']['i'] is not None:
                        for y in range(qp_data['bottomRightCorner']['oh']):
                            for x in range(qp_data['bottomRightCorner']['ow']):
                                if x > 0 or y > 0:
                                    sobj = QuickPaintOperations.searchObj(layer, obj.objx - x, obj.objy - y)

                                    if (sobj and sobj.width == 1 and sobj.height == 1
                                        and (hasattr(sobj, 'autoTileType') and sobj.autoTileType == 'bottomRightCorner')
                                        and not (hasattr(sobj, 'modifiedForSize')
                                                 and sobj.modifiedForSize & 0x800 == 0x800)):
                                        obj.tileset = sobj.tileset
                                        obj.type = sobj.original_type
                                        obj.original_type = sobj.original_type
                                        obj.modifiedForSize |= 0x800

                    if qp_data['topLeft']['i'] is not None and QuickPaintOperations.countUpLeft(layer, obj,
                                                                                                qp_data['topLeft'][
                                                                                                    'ow'],
                                                                                                qp_data['topLeft'][
                                                                                                    'oh']):
                        for y in range(qp_data['topLeft']['oh']):
                            for x in range(qp_data['topLeft']['ow']):
                                if x > 0 or y > 0:
                                    sobj = QuickPaintOperations.searchObj(layer, obj.objx - x, obj.objy - y)

                                    if sobj is not None and sobj.width == 1 and sobj.height == 1 and (
                                                hasattr(sobj,
                                                        'autoTileType') and sobj.autoTileType == 'topLeft') and not (
                                                hasattr(sobj,
                                                        'modifiedForSize') and sobj.modifiedForSize & 0x01 == 0x1):
                                        obj.tileset = sobj.tileset
                                        obj.type = sobj.original_type
                                        obj.original_type = sobj.original_type
                                        obj.modifiedForSize |= 0x01

                    if qp_data['topRight']['i'] is not None and QuickPaintOperations.countUpRight(layer, obj,
                                                                                                  qp_data['topRight'][
                                                                                                      'ow'],
                                                                                                  qp_data['topRight'][
                                                                                                      'oh']):
                        for y in range(qp_data['topRight']['oh']):
                            for x in range(qp_data['topRight']['ow']):
                                if x > 0 or y > 0:
                                    sobj = QuickPaintOperations.searchObj(layer, obj.objx + x, obj.objy - y)

                                    if sobj is not None and sobj.width == 1 and sobj.height == 1 and (
                                                hasattr(sobj,
                                                        'autoTileType') and sobj.autoTileType == 'topRight') and not (
                                                hasattr(sobj,
                                                        'modifiedForSize') and sobj.modifiedForSize & 0x02 == 0x2):
                                        obj.tileset = sobj.tileset
                                        obj.type = sobj.original_type
                                        obj.original_type = sobj.original_type
                                        obj.modifiedForSize |= 0x02

                    if qp_data['bottomLeft']['i'] is not None and QuickPaintOperations.countDownLeft(layer, obj,
                                                                                                     qp_data[
                                                                                                         'bottomLeft'][
                                                                                                         'ow'], qp_data[
                                                                                                         'bottomLeft'][
                                                                                                         'oh']):
                        for y in range(qp_data['bottomLeft']['oh']):
                            for x in range(qp_data['bottomLeft']['ow']):
                                if x > 0 or y > 0:
                                    sobj = QuickPaintOperations.searchObj(layer, obj.objx - x, obj.objy + y)

                                    if sobj is not None and sobj.width == 1 and sobj.height == 1 and (
                                                hasattr(sobj,
                                                        'autoTileType') and sobj.autoTileType == 'bottomLeft') and not (
                                                hasattr(sobj,
                                                        'modifiedForSize') and sobj.modifiedForSize & 0x04 == 0x4):
                                        obj.tileset = sobj.tileset
                                        obj.type = sobj.original_type
                                        obj.original_type = sobj.original_type
                                        obj.modifiedForSize |= 0x04

                    if qp_data['bottomRight']['i'] and QuickPaintOperations.countDownRight(layer, obj,
                                                                                           qp_data[
                                                                                               'bottomRight'][
                                                                                               'ow'],
                                                                                           qp_data[
                                                                                               'bottomRight'][
                                                                                               'oh']):
                        for y in range(qp_data['bottomRight']['oh']):
                            for x in range(qp_data['bottomRight']['ow']):
                                if x > 0 or y > 0:
                                    sobj = QuickPaintOperations.searchObj(layer, obj.objx + x, obj.objy + y)

                                    if (sobj is not None and sobj.width == 1 and sobj.height == 1
                                        and (hasattr(sobj, 'autoTileType') and sobj.autoTileType == 'bottomRight')
                                        and not (hasattr(sobj, 'modifiedForSize')
                                                 and sobj.modifiedForSize & 0x08 == 0x8)):
                                        obj.tileset = sobj.tileset
                                        obj.type = sobj.original_type
                                        obj.original_type = sobj.original_type
                                        obj.modifiedForSize |= 0x08

                    if qp_data['top']['i'] is not None and QuickPaintOperations.countUp(layer, obj,
                                                                                        qp_data['top']['oh']):
                        for y in range(qp_data['top']['oh']):
                            if y > 0:
                                sobj = QuickPaintOperations.searchObj(layer, obj.objx, obj.objy - y)

                                if sobj is not None and sobj.width == 1 and sobj.height == 1 and (
                                            hasattr(sobj, 'autoTileType') and sobj.autoTileType == 'top') and not (
                                            hasattr(sobj, 'modifiedForSize') and sobj.modifiedForSize & 0x10 == 0x10):
                                    obj.tileset = sobj.tileset
                                    obj.type = sobj.original_type
                                    obj.original_type = sobj.original_type
                                    obj.modifiedForSize |= 0x10

                    if qp_data['bottom']['i'] is not None and QuickPaintOperations.countDown(layer, obj,
                                                                                             qp_data['bottom']['oh']):
                        for y in range(qp_data['bottom']['oh']):
                            if y > 0:
                                sobj = QuickPaintOperations.searchObj(layer, obj.objx, obj.objy + y)

                                if sobj is not None and sobj.width == 1 and sobj.height == 1 and (
                                            hasattr(sobj, 'autoTileType') and sobj.autoTileType == 'bottom') and not (
                                            hasattr(sobj, 'modifiedForSize') and sobj.modifiedForSize & 0x20 == 0x20):
                                    obj.tileset = sobj.tileset
                                    obj.type = sobj.original_type
                                    obj.original_type = sobj.original_type
                                    obj.modifiedForSize |= 0x20

                    if qp_data['left']['i'] is not None and QuickPaintOperations.countLeft(layer, obj,
                                                                                           qp_data['left']['ow']):
                        for x in range(qp_data['left']['ow']):
                            if x > 0:
                                sobj = QuickPaintOperations.searchObj(layer, obj.objx - x, obj.objy)

                                if sobj is not None and sobj.width == 1 and sobj.height == 1 and (
                                            hasattr(sobj, 'autoTileType') and sobj.autoTileType == 'left') and not (
                                            hasattr(sobj, 'modifiedForSize') and sobj.modifiedForSize & 0x40 == 0x40):
                                    obj.tileset = sobj.tileset
                                    obj.type = sobj.original_type
                                    obj.original_type = sobj.original_type
                                    obj.modifiedForSize |= 0x40

                    if qp_data['right']['i'] is not None and QuickPaintOperations.countRight(layer, obj,
                                                                                             qp_data['right']['ow']):
                        for x in range(qp_data['right']['ow']):
                            if x > 0:
                                sobj = QuickPaintOperations.searchObj(layer, obj.objx + x, obj.objy)

                                if sobj is not None and sobj.width == 1 and sobj.height == 1 and (
                                            hasattr(sobj, 'autoTileType') and sobj.autoTileType == 'right') and not (
                                            hasattr(sobj, 'modifiedForSize') and sobj.modifiedForSize & 0x80 == 0x80):
                                    obj.tileset = sobj.tileset
                                    obj.type = sobj.original_type
                                    obj.original_type = sobj.original_type
                                    obj.modifiedForSize |= 0x80

                    obj.updateObjCache()
                    obj.UpdateTooltip()


class QuickPaintConfigWidget(QtWidgets.QWidget):
    """
    Widget that allows the user to configure tiles and objects for quick paint.
    """
    moveIt = QtCore.pyqtSignal(int, int)

    def __init__(self):
        """
        Constructor for the quick paint confirmation widget
        """

        QtWidgets.QWidget.__init__(self)
        self.setSizePolicy(
            QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding))
        self.QuickPaintMode = None
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.PaintModeCheck = QtWidgets.QPushButton(self)
        self.PaintModeCheck.setMinimumSize(QtCore.QSize(0, 40))
        self.PaintModeCheck.clicked.connect(self.SetPaintMode)
        self.PaintModeCheck.setCheckable(True)
        self.PaintModeCheck.setObjectName("PaintModeCheck")
        self.horizontalLayout_2.addWidget(self.PaintModeCheck)
        self.EraseModeCheck = QtWidgets.QPushButton(self)
        self.EraseModeCheck.setMinimumSize(QtCore.QSize(0, 40))
        self.EraseModeCheck.clicked.connect(self.SetEraseMode)
        self.EraseModeCheck.setCheckable(True)
        self.EraseModeCheck.setObjectName("EraseModeCheck")
        self.horizontalLayout_2.addWidget(self.EraseModeCheck)
        self.gridLayout.addLayout(self.horizontalLayout_2, 4, 0, 1, 1)
        self.horizontalScrollBar = QtWidgets.QScrollBar(self)
        self.horizontalScrollBar.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalScrollBar.setValue(50)
        self.horizontalScrollBar.valueChanged.connect(self.horizontalScrollBar_changed)
        self.horizontalScrollBar.setObjectName("horizontalScrollBar")
        self.gridLayout.addWidget(self.horizontalScrollBar, 2, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(5)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_4 = QtWidgets.QLabel(self)
        self.label_4.setMaximumSize(QtCore.QSize(60, 30))
        self.label_4.setObjectName("label_4")
        self.horizontalLayout.addWidget(self.label_4)
        self.comboBox_4 = QtWidgets.QComboBox(self)
        self.comboBox_4.activated.connect(self.currentPresetIndexChanged)
        self.comboBox_4.setObjectName("comboBox_4")
        self.horizontalLayout.addWidget(self.comboBox_4)
        self.SaveToPresetButton = QtWidgets.QPushButton(self)
        self.SaveToPresetButton.setMaximumSize(QtCore.QSize(60, 30))
        self.SaveToPresetButton.setBaseSize(QtCore.QSize(0, 0))
        self.SaveToPresetButton.setCheckable(False)
        self.SaveToPresetButton.clicked.connect(self.saveToCurrentPresetConfirm)
        self.SaveToPresetButton.setEnabled(False)
        self.SaveToPresetButton.setObjectName("SaveToPresetButton")
        self.horizontalLayout.addWidget(self.SaveToPresetButton)
        self.AddPresetButton = QtWidgets.QPushButton(self)
        self.AddPresetButton.setMaximumSize(QtCore.QSize(60, 30))
        self.AddPresetButton.setBaseSize(QtCore.QSize(0, 0))
        self.AddPresetButton.clicked.connect(self.openTextForm)
        self.AddPresetButton.setObjectName("AddPresetButton")
        self.horizontalLayout.addWidget(self.AddPresetButton)
        self.RemovePresetButton = QtWidgets.QPushButton(self)
        self.RemovePresetButton.setMaximumSize(QtCore.QSize(60, 30))
        self.RemovePresetButton.clicked.connect(self.removeCurrentPresetConfirm)
        self.RemovePresetButton.setObjectName("RemovePresetButton")
        self.horizontalLayout.addWidget(self.RemovePresetButton)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.graphicsView = self.QuickPaintView(None, self)
        self.graphicsView.setObjectName("graphicsView")
        self.reset()
        self.gridLayout.addWidget(self.graphicsView, 1, 0, 1, 1)
        self.verticalScrollBar = QtWidgets.QScrollBar(self)
        self.verticalScrollBar.setOrientation(QtCore.Qt.Vertical)
        self.verticalScrollBar.valueChanged.connect(self.verticalScrollBar_changed)
        self.verticalScrollBar.setValue(50)
        self.verticalScrollBar.setObjectName("verticalScrollBar")
        self.gridLayout.addWidget(self.verticalScrollBar, 1, 1, 1, 1)
        self.ZoomButton = QtWidgets.QPushButton(self)
        self.ZoomButton.setMinimumSize(QtCore.QSize(30, 30))
        self.ZoomButton.setMaximumSize(QtCore.QSize(30, 30))
        self.ZoomButton.setObjectName("ZoomButton")
        self.ZoomButton.clicked.connect(self.zoom)
        self.gridLayout.addWidget(self.ZoomButton, 0, 1, 1, 1)
        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)
        self.setTabOrder(self.AddPresetButton, self.comboBox_4)
        self.setTabOrder(self.comboBox_4, self.RemovePresetButton)
        self.show_badObjWarning = False

    def SetPaintMode(self):
        """
        Sets the Quick-Paint Mode to paint or turn off.
        """
        #        self.SlopeModeCheck.setChecked(False)
        self.EraseModeCheck.setChecked(False)

        if self.PaintModeCheck.isChecked():
            self.QuickPaintMode = 'PAINT'

        else:
            self.QuickPaintMode = None

        globals_.mainWindow.scene.update()

    # I don't know if slopes will be supported in the future or not. But for now this function is useless.
    """
    def SetSlopeMode(self):
        self.PaintModeCheck.setChecked(False)
        self.EraseModeCheck.setChecked(False)
        if self.SlopeModeCheck.isChecked():
            self.QuickPaintMode = 'SLOPE'
        else:
            self.QuickPaintMode = None
    """

    def SetEraseMode(self):
        """
        Sets the Quick-Paint Mode to erase or turn off.
        """
        self.PaintModeCheck.setChecked(False)
        # self.SlopeModeCheck.setChecked(False)

        if self.EraseModeCheck.isChecked():
            self.QuickPaintMode = 'ERASE'

        else:
            self.QuickPaintMode = None

        globals_.mainWindow.scene.update()

    def reset(self):
        setoffsets = False

        if hasattr(self, 'scene'):
            panoffsets = (self.scene.xoffset,self.scene.yoffset)
            del self.scene
            setoffsets = True

        self.scene = self.QuickPaintScene(self)

        if setoffsets:
            self.scene.xoffset = panoffsets[0]
            self.scene.yoffset = panoffsets[1]

        self.graphicsView.setScene(self.scene)
        self.comboBox_4.setCurrentIndex(-1)

    def currentPresetIndexChanged(self, index):
        """
        Handles the change of index of the saved presets context menu and loads the preset.
        """
        self.SaveToPresetButton.setEnabled(index != -1)
        name = self.comboBox_4.currentText()
        no = False

        try:
            f = open("reggiedata/qpsp/" + name + ".qpp", 'r')

        except:
            no = True

        if not no and globals_.ObjectDefinitions is not None:
            try:
                for line in f.readlines():
                    elements = line.split('\t')

                    if line != '\n':
                        self.scene.object_database[elements[0]]['x'] = int(elements[1])
                        self.scene.object_database[elements[0]]['y'] = int(elements[2])
                        self.scene.object_database[elements[0]]['w'] = int(elements[3])
                        self.scene.object_database[elements[0]]['h'] = int(elements[4])
                        self.scene.object_database[elements[0]]['ow'] = int(elements[3])
                        self.scene.object_database[elements[0]]['oh'] = int(elements[4])

                        if elements[5] == '\n':
                            self.scene.object_database[elements[0]]['i'] = None

                        else:
                            ln = globals_.CurrentLayer
                            layer = globals_.Area.layers[globals_.CurrentLayer]
                            if len(layer) == 0:
                                z = (2 - ln) * 8192
                            else:
                                z = layer[-1].zValue() + 1

                            self.scene.object_database[elements[0]]['ts'] = int(elements[5])
                            self.scene.object_database[elements[0]]['t'] = int(elements[6])
                            self.scene.object_database[elements[0]]['i'] = ObjectItem(int(elements[5]),
                                                                                      int(elements[6]), -1,
                                                                                      self.scene.object_database[
                                                                                          elements[0]]['x'],
                                                                                      self.scene.object_database[
                                                                                          elements[0]]['y'],
                                                                                      int(elements[3]),
                                                                                      int(elements[4]), z)

            except:
                print("Preset parse failed.")

            f.close()

        self.scene.fixAndUpdateObjects()
        self.scene.invalidate()

    def zoom(self):
        """
        Zoom the view to half/full. Half is best for view when it's in a small region.
        """
        if self.scene.zoom == 2:
            self.scene.zoom = 1
            self.ZoomButton.setIcon(GetIcon("zoomin", True))

        else:
            self.scene.zoom = 2
            self.ZoomButton.setIcon(GetIcon("zoomout", True))

        self.scene.invalidate()

    def verticalScrollBar_changed(self):
        """
        Handles vertical scroll movement, moving the view up and down.
        """
        self.scene.setYoffset((50 - self.verticalScrollBar.value()) * 16)

    def horizontalScrollBar_changed(self):
        """
        Handles horizontal scroll movement, moving the view left and right.
        """
        self.scene.setXoffset((50 - self.horizontalScrollBar.value()) * 16)

    def retranslateUi(self):
        """
        More UI construction.
        """
        self.setWindowTitle(globals_.trans.string('QuickPaint', 3))
        self.PaintModeCheck.setText(globals_.trans.string('QuickPaint', 4))
        #        self.SlopeModeCheck.setText(_translate("self", "Slope"))
        self.EraseModeCheck.setText(globals_.trans.string('QuickPaint', 5))
        self.label_4.setText(globals_.trans.string('QuickPaint', 6))

        for fname in os.listdir("reggiedata/qpsp/"):
            if fname.endswith(".qpp"):
                self.comboBox_4.addItem(fname[:-4])

        self.comboBox_4.setCurrentIndex(-1)
        self.SaveToPresetButton.setText(globals_.trans.string('QuickPaint', 7))
        self.AddPresetButton.setText(globals_.trans.string('QuickPaint', 8))
        self.RemovePresetButton.setText(globals_.trans.string('QuickPaint', 9))
        self.ZoomButton.setIcon(GetIcon("zoomin", True))

    def ShowBadObjectWarning(self):
        if self.show_badObjWarning:
            QtWidgets.QMessageBox().warning(self,
                                            globals_.trans.string('QuickPaint', 1),
                                            globals_.trans.string('QuickPaint', 2))

            self.show_badObjWarning = False

    class ConfirmRemovePresetDialog(object):
        """
        Dialog that asks the user for confirmation before removing a preset. We want to make sure the user didn't press the remove preset button by mistake.
        """

        def __init__(self, Dialog):
            """
            Dialog construction.
            """
            Dialog.setObjectName("Dialog")
            Dialog.resize(650, 109)
            Dialog.setMinimumSize(QtCore.QSize(650, 109))
            Dialog.setMaximumSize(QtCore.QSize(650, 109))
            self.gridLayout = QtWidgets.QGridLayout(Dialog)
            self.gridLayout.setObjectName("gridLayout")
            self.label = QtWidgets.QLabel(Dialog)
            self.label.setObjectName("label")
            self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
            self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
            self.buttonBox.setLayoutDirection(QtCore.Qt.LeftToRight)
            self.buttonBox.setAutoFillBackground(False)
            self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
            self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.No | QtWidgets.QDialogButtonBox.Yes)
            self.buttonBox.setCenterButtons(True)
            self.buttonBox.setObjectName("buttonBox")
            self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)
            self.retranslateUi(Dialog)
            self.buttonBox.accepted.connect(Dialog.accept)
            self.buttonBox.rejected.connect(Dialog.reject)
            QtCore.QMetaObject.connectSlotsByName(Dialog)

        def retranslateUi(self, Dialog):
            """
            More dialog UI construction.
            """
            Dialog.setWindowTitle(globals_.trans.string('QuickPaint', 10))
            self.label.setText(globals_.trans.string('QuickPaint', 11))

    class ConfirmOverwritePresetDialog(object):
        """
        Dialog that asks the user for confirmation before overiting a preset. We want to make sure the user didn't press the save preset button by mistake.
        """

        def __init__(self, Dialog):
            """
            Dialog construction.
            """
            Dialog.setObjectName("Dialog")
            Dialog.resize(360, 109)
            Dialog.setMinimumSize(QtCore.QSize(360, 109))
            Dialog.setMaximumSize(QtCore.QSize(360, 109))
            self.gridLayout = QtWidgets.QGridLayout(Dialog)
            self.gridLayout.setObjectName("gridLayout")
            self.label = QtWidgets.QLabel(Dialog)
            self.label.setObjectName("label")
            self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
            self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
            self.buttonBox.setLayoutDirection(QtCore.Qt.LeftToRight)
            self.buttonBox.setAutoFillBackground(False)
            self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
            self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.No | QtWidgets.QDialogButtonBox.Yes)
            self.buttonBox.setCenterButtons(True)
            self.buttonBox.setObjectName("buttonBox")
            self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)
            self.retranslateUi(Dialog)
            self.buttonBox.accepted.connect(Dialog.accept)
            self.buttonBox.rejected.connect(Dialog.reject)
            QtCore.QMetaObject.connectSlotsByName(Dialog)

        def retranslateUi(self, Dialog):
            """
            More dialog UI construction.
            """
            Dialog.setWindowTitle(globals_.trans.string('QuickPaint', 10))
            self.label.setText(globals_.trans.string('QuickPaint', 12))

    class TextDialog(object):
        """
        Dialog that asks for the name of the new preset and confirms the action.
        """

        def __init__(self, Dialog, parent):
            """
            Dialog construction.
            """
            Dialog.setObjectName("Dialog")
            Dialog.resize(380, 109)
            Dialog.setMinimumSize(QtCore.QSize(380, 109))
            Dialog.setMaximumSize(QtCore.QSize(380, 109))
            self.gridLayout = QtWidgets.QGridLayout(Dialog)
            self.gridLayout.setObjectName("gridLayout")
            self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
            self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
            self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
            self.buttonBox.setObjectName("buttonBox")
            self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)
            self.lineEdit = QtWidgets.QLineEdit(Dialog)
            self.lineEdit.setFrame(True)
            self.lineEdit.setClearButtonEnabled(False)
            self.lineEdit.setObjectName("lineEdit")
            self.gridLayout.addWidget(self.lineEdit, 0, 0, 1, 1)

            self.retranslateUi(Dialog)
            self.buttonBox.accepted.connect(self.Accepted)
            self.buttonBox.rejected.connect(Dialog.reject)
            QtCore.QMetaObject.connectSlotsByName(Dialog)
            self.Dialog = Dialog
            self.parent = parent

        def Accepted(self):
            """
            Yeah, I wrote the action in here because this was my first attempt to program a dialog in PyQt.
            """
            if self.lineEdit.text() != "" and self.lineEdit.text() != self.parent.comboBox_4.currentText():
                self.parent.saveCurrentPreset(self.lineEdit.text())
                self.parent.comboBox_4.insertItem(0, self.lineEdit.text())
                self.parent.comboBox_4.setCurrentIndex(0)
                self.Dialog.accept()

        def retranslateUi(self, Dialog):
            """
            More dialog UI construction.
            """
            Dialog.setWindowTitle(globals_.trans.string('QuickPaint', 13))

    class QuickPaintView(QtWidgets.QGraphicsView):
        """
        Here we view the graphics that display the objects that will be arranged inside the user's quick paint strokes.
        """

        def __init__(self, scene, parent):
            """
            Constructs the quick paint view.
            """
            QtWidgets.QGraphicsView.__init__(self, scene, parent)
            self.parent = parent

        def mousePressEvent(self, event):
            """
            Handles mouse pressing events over the widget
            """
            obj = self.parent.scene.HitObject(event.x(), event.y(), self.width(), self.height())
            if obj is not None:
                if event.button() == QtCore.Qt.LeftButton:
                    if globals_.CurrentObject != -1 and globals_.CurrentObject != -1:
                        odef = globals_.ObjectDefinitions[globals_.CurrentObject][globals_.CurrentObject]
                        self.parent.scene.object_database[obj]['w'] = odef.width
                        self.parent.scene.object_database[obj]['h'] = odef.height
                        self.parent.scene.object_database[obj]['ow'] = odef.width
                        self.parent.scene.object_database[obj]['oh'] = odef.height
                        self.parent.scene.object_database[obj]['i'] = ObjectItem(globals_.CurrentObject,
                                                                                 globals_.CurrentObject, -1,
                                                                                 self.parent.scene.object_database[obj][
                                                                                     'x'],
                                                                                 self.parent.scene.object_database[obj][
                                                                                     'y'], odef.width, odef.height, 0)
                        self.parent.scene.object_database[obj]['ts'] = globals_.CurrentObject
                        self.parent.scene.object_database[obj]['t'] = globals_.CurrentObject
                        self.parent.scene.invalidate()

                elif event.button() == QtCore.Qt.RightButton:
                    self.parent.scene.object_database[obj]['w'] = 1
                    self.parent.scene.object_database[obj]['h'] = 1
                    self.parent.scene.object_database[obj]['ow'] = 1
                    self.parent.scene.object_database[obj]['oh'] = 1
                    self.parent.scene.object_database[obj]['i'] = None
                    self.parent.scene.invalidate()

                self.parent.scene.fixAndUpdateObjects()

    class QuickPaintScene(QtWidgets.QGraphicsScene):
        """
        This is the scene that contains the objects that will be arranged inside the user's quick paint strokes.
        """

        def __init__(self, parent, *args):
            """
            Constructs the quick paint scene.
            """
            bgcolor = globals_.theme.color('bg')
            bghsv = bgcolor.getHsv()
            self.xoffset = 0
            self.yoffset = 0
            self.zoom = 1
            self.object_database = {
                'base': {'x': 0, 'y': 0, 'w': 1, 'h': 1, 'ow': 1, 'oh': 1, 'ts': -1, 't': -1, 'i': None},
                'top': {'x': 0, 'y': -1, 'w': 1, 'h': 1, 'ow': 1, 'oh': 1, 'ts': -1, 't': -1, 'p': 'base', 'i': None},
                'topRight': {'x': 1, 'y': -1, 'w': 1, 'h': 1, 'ow': 1, 'oh': 1, 'ts': -1, 't': -1, 'p': 'base',
                             'i': None},
                'topRightCorner': {'x': 4, 'y': 0, 'w': 1, 'h': 1, 'ow': 1, 'oh': 1, 'ts': -1, 't': -1, 'p': 'base',
                                   'i': None},
                'right': {'x': 1, 'y': 0, 'w': 1, 'h': 1, 'ow': 1, 'oh': 1, 'ts': -1, 't': -1, 'p': 'base', 'i': None},
                'bottomRight': {'x': 1, 'y': 1, 'w': 1, 'h': 1, 'ow': 1, 'oh': 1, 'ts': -1, 't': -1, 'p': 'base',
                                'i': None},
                'bottomRightCorner': {'x': 4, 'y': 0, 'w': 1, 'h': 1, 'ow': 1, 'oh': 1, 'ts': -1, 't': -1, 'p': 'base',
                                      'i': None},
                'bottom': {'x': 0, 'y': 1, 'w': 1, 'h': 1, 'ow': 1, 'oh': 1, 'ts': -1, 't': -1, 'p': 'base', 'i': None},
                'bottomLeft': {'x': -1, 'y': 1, 'w': 1, 'h': 1, 'ow': 1, 'oh': 1, 'ts': -1, 't': -1, 'p': 'base',
                               'i': None},
                'bottomLeftCorner': {'x': 4, 'y': 0, 'w': 1, 'h': 1, 'ow': 1, 'oh': 1, 'ts': -1, 't': -1, 'p': 'base',
                                     'i': None},
                'left': {'x': -1, 'y': 0, 'w': 1, 'h': 1, 'ow': 1, 'oh': 1, 'ts': -1, 't': -1, 'p': 'base', 'i': None},
                'topLeft': {'x': -1, 'y': -1, 'w': 1, 'h': 1, 'ow': 1, 'oh': 1, 'ts': -1, 't': -1, 'p': 'base',
                            'i': None},
                'topLeftCorner': {'x': 4, 'y': 0, 'w': 1, 'h': 1, 'ow': 1, 'oh': 1, 'ts': -1, 't': -1, 'p': 'base',
                                  'i': None}
            }
            self.display_objects = []
            self.BadObjectWarning = False
            bgcolor.setHsv(bghsv[0], min(int(bghsv[1] * 1.5), 255), int(bghsv[2] / 1.5), bghsv[3])
            self.bgbrush = QtGui.QBrush(bgcolor)
            QtWidgets.QGraphicsScene.__init__(self, *args)
            self.parent = parent

        def setXoffset(self, value):
            """
            Sets the X view position.
            """
            self.xoffset = value
            self.invalidate()

        def setYoffset(self, value):
            """
            Sets the Y view position.
            """
            self.yoffset = value
            self.invalidate()

        def HitObject(self, x, y, w, h):
            """
            Looks to see if there is an object at this position.
            """
            hitPoint = ((x - w / 2 - self.xoffset) / self.zoom, (y - h / 2 - self.yoffset) / self.zoom)
            for obj in self.object_database:
                if (self.object_database[obj] and
                        not (self.object_database[obj].get('p') is not None and self.object_database.get(
                            self.object_database[obj]['p']) is not None and
                                     self.object_database[self.object_database[obj]['p']]['i'] is None) and
                                self.object_database[obj]['x'] * 24 <= hitPoint[0] and
                                self.object_database[obj]['y'] * 24 <= hitPoint[1] and
                                    self.object_database[obj]['x'] * 24 + self.object_database[obj][
                                'w'] * 24 > hitPoint[0] and
                                    self.object_database[obj]['y'] * 24 + self.object_database[obj][
                                'h'] * 24 > hitPoint[1]):

                    return obj

            return None

        def ArrangeMainIsland(self, maxbasewidth, maxleftwidth, maxrightwidth, maxbaseheight, maxtopheight,
                              maxbottomheight):
            """
            Places the objects forming the main island correctly (or at least it should).
            """
            self.object_database['top']['w'] = maxbasewidth
            self.object_database['base']['w'] = maxbasewidth
            self.object_database['bottom']['w'] = maxbasewidth
            self.object_database['topLeft']['w'] = maxleftwidth
            self.object_database['left']['w'] = maxleftwidth
            self.object_database['bottomLeft']['w'] = maxleftwidth
            self.object_database['top']['x'] = maxleftwidth - 1
            self.object_database['base']['x'] = maxleftwidth - 1
            self.object_database['bottom']['x'] = maxleftwidth - 1
            self.object_database['topRight']['w'] = maxrightwidth
            self.object_database['right']['w'] = maxrightwidth
            self.object_database['bottomRight']['w'] = maxrightwidth
            self.object_database['topRight']['x'] = maxbasewidth + maxleftwidth - 1
            self.object_database['right']['x'] = maxbasewidth + maxleftwidth - 1
            self.object_database['bottomRight']['x'] = maxbasewidth + maxleftwidth - 1
            self.object_database['right']['h'] = maxbaseheight
            self.object_database['base']['h'] = maxbaseheight
            self.object_database['left']['h'] = maxbaseheight
            self.object_database['topLeft']['h'] = maxtopheight
            self.object_database['top']['h'] = maxtopheight
            self.object_database['topRight']['h'] = maxtopheight
            self.object_database['right']['y'] = maxtopheight - 1
            self.object_database['base']['y'] = maxtopheight - 1
            self.object_database['left']['y'] = maxtopheight - 1
            self.object_database['bottomLeft']['h'] = maxbottomheight
            self.object_database['bottom']['h'] = maxbottomheight
            self.object_database['bottomRight']['h'] = maxbottomheight
            self.object_database['bottomLeft']['y'] = maxbaseheight + maxtopheight - 1
            self.object_database['bottom']['y'] = maxbaseheight + maxtopheight - 1
            self.object_database['bottomRight']['y'] = maxbaseheight + maxtopheight - 1

            displayObjects = []
            for y in range(self.object_database['top']['h']):
                for x in range(self.object_database['top']['w']):
                    displayObjects.append((self.AddDisplayObject('base', self.object_database['top']['x'] + x + 20, self.object_database['top']['y'] + 20 + y, 1,1), self.object_database['top']['i'] is None))

            for y in range(self.object_database['base']['h']):
                for x in range(self.object_database['base']['w']):
                    displayObjects.append((self.AddDisplayObject('base', self.object_database['base']['x'] + x + 20, self.object_database['base']['y'] + 20 + y, 1,1), self.object_database['base']['i'] is None))

            for y in range(self.object_database['bottom']['h']):
                for x in range(self.object_database['bottom']['w']):
                    displayObjects.append((self.AddDisplayObject('base', self.object_database['bottom']['x'] + x + 20, self.object_database['bottom']['y'] + 20 + y, 1,1), self.object_database['bottom']['i'] is None))

            for y in range(self.object_database['topLeft']['h']):
                for x in range(self.object_database['topLeft']['w']):
                    displayObjects.append((self.AddDisplayObject('base', self.object_database['topLeft']['x'] + x + 20, self.object_database['topLeft']['y'] + 20 + y, 1,1), self.object_database['topLeft']['i'] is None))

            for y in range(self.object_database['left']['h']):
                for x in range(self.object_database['left']['w']):
                    displayObjects.append((self.AddDisplayObject('base', self.object_database['left']['x'] + x + 20, self.object_database['left']['y'] + 20 + y, 1,1), self.object_database['left']['i'] is None))

            for y in range(self.object_database['bottomLeft']['h']):
                for x in range(self.object_database['bottomLeft']['w']):
                    displayObjects.append((self.AddDisplayObject('base', self.object_database['bottomLeft']['x'] + x + 20, self.object_database['bottomLeft']['y'] + 20 + y, 1,1), self.object_database['bottomLeft']['i'] is None))

            for y in range(self.object_database['topRight']['h']):
                for x in range(self.object_database['topRight']['w']):
                    displayObjects.append((self.AddDisplayObject('base', self.object_database['topRight']['x'] + x + 20, self.object_database['topRight']['y'] + 20 + y, 1,1), self.object_database['topRight']['i'] is None))

            for y in range(self.object_database['bottomRight']['h']):
                for x in range(self.object_database['bottomRight']['w']):
                    displayObjects.append((self.AddDisplayObject('base', self.object_database['bottomRight']['x'] + x + 20, self.object_database['bottomRight']['y'] + 20 + y, 1,1), self.object_database['bottomRight']['i'] is None))

            for y in range(self.object_database['right']['h']):
                for x in range(self.object_database['right']['w']):
                    displayObjects.append((self.AddDisplayObject('base', self.object_database['right']['x'] + x + 20, self.object_database['right']['y'] + 20 + y, 1,1), self.object_database['right']['i'] is None))

            for obj in displayObjects:
                if obj[0] is not None:
                    QuickPaintOperations.autoTileObj(-1, obj[0])

            for obj in displayObjects:
                if obj[0] is not None:
                    QuickPaintOperations.autoTileObj(-1, obj[0])

            for obj in displayObjects:
                if obj[1] and obj[0] in self.display_objects:
                    self.display_objects.remove(obj[0])
                    obj[0].RemoveFromSearchDatabase()
                    if obj[0] in QuickPaintOperations.object_optimize_database: QuickPaintOperations.object_optimize_database.remove(obj[0])

        def ArrangeCornerSetterIsland(self, offsetX, maxbasewidth, maxleftwidth, maxrightwidth, maxbaseheight,
                                      maxtopheight, maxbottomheight):
            """
            Places the objects forming the corner setter island (the square doughnut-shaped island) correctly (or at least it should).
            """
            displayObjects = []
            for y in range(maxtopheight):
                for x in range(maxleftwidth):
                    displayObjects.append((self.AddDisplayObject('base', maxbasewidth + maxleftwidth - 1 + maxrightwidth + offsetX + 20 + x, -3 + 20 + y,
                                       1, 1), False))
            tx = 0

            for i in range(3 + maxrightwidth + maxleftwidth):
                for y in range(maxtopheight):
                    displayObjects.append((self.AddDisplayObject('base',
                                           maxbasewidth + maxleftwidth - 1 + maxrightwidth + i + offsetX + maxleftwidth + 20,
                                           -3 + 20 + y, 1, 1), False))
                tx += 1
            for y in range(maxtopheight):
                for x in range(self.object_database['topRight']['w']):
                    displayObjects.append((self.AddDisplayObject('base',
                                       maxbasewidth + maxleftwidth - 1 + maxrightwidth + offsetX + maxleftwidth + tx + 20 + x,
                                       -3 + 20 + y, 1,1), False))
                    ty1 = 0
                    ty2 = 0

            for i in range(3 + maxtopheight + maxbottomheight):
                for x in range(maxleftwidth):
                    displayObjects.append((self.AddDisplayObject('base', maxbasewidth + maxleftwidth - 1 + maxrightwidth + offsetX + 20 + x,
                                           -3 + i + maxtopheight + 20, 1, 1), False))
                ty1 += 1

            for i in range(3 + maxtopheight + maxbottomheight):
                for x in range(maxrightwidth):
                    displayObjects.append((self.AddDisplayObject('base',
                                           maxbasewidth + maxleftwidth - 1 + maxrightwidth + offsetX + maxleftwidth + tx + 20 + x,
                                           -3 + i + maxtopheight + 20, 1, 1), False))
                ty2 += 1
            ty = max(ty1, ty2)
            for y in range(maxbottomheight):
                for x in range(maxleftwidth):
                    displayObjects.append((self.AddDisplayObject('base', maxbasewidth + maxleftwidth - 1 + maxrightwidth + offsetX + 20 + x,
                                       -3 + ty + maxtopheight + 20 + y, 1, 1), False))

            for i in range(3 + maxrightwidth + maxleftwidth):
                for y in range(maxbottomheight):
                    displayObjects.append((self.AddDisplayObject('base',
                                           maxbasewidth + maxleftwidth - 1 + maxrightwidth + i + offsetX + maxleftwidth + 20,
                                           -3 + ty + maxtopheight + 20 + y, 1, 1), False))
            for y in range(maxbottomheight):
                for x in range(self.object_database['bottomRight']['w']):
                    displayObjects.append((self.AddDisplayObject('base',
                                       maxbasewidth + maxleftwidth - 1 + maxrightwidth + offsetX + maxleftwidth + tx + 20 + x,
                                       -3 + ty + maxtopheight + 20 + y, 1,
                                       1), False))

            for i in range(3):
                for y in range(maxtopheight):
                    displayObjects.append((self.AddDisplayObject('base',
                                           maxbasewidth + maxleftwidth - 1 + maxrightwidth + offsetX + maxleftwidth + maxrightwidth + i + 20,
                                           -3 + ty + 20 + y, 1, 1), False))
            for i in range(3):
                for y in range(maxbottomheight):
                    displayObjects.append((self.AddDisplayObject('base',
                                           maxbasewidth + maxleftwidth - 1 + maxrightwidth + offsetX + maxleftwidth + maxrightwidth + i + 20,
                                           -3 + maxtopheight + 20 + y, 1, 1), False))

            for i in range(3):
                for x in range(maxrightwidth):
                    displayObjects.append((self.AddDisplayObject('base',
                                            maxbasewidth + maxleftwidth - 1 + maxrightwidth + offsetX + maxleftwidth + 20 + x,
                                            -3 + maxtopheight + i + maxbottomheight + 20, 1, 1), False))

            for i in range(3):
                for x in range(maxleftwidth):
                    displayObjects.append((self.AddDisplayObject('base',
                                            maxbasewidth + maxleftwidth - 1 + maxrightwidth + offsetX + maxleftwidth + maxrightwidth + 3 + 20 + x,
                                            -3 + maxtopheight + i + maxbottomheight + 20, 1, 1), False))

            already_created_corner = False
            for ix in range(maxrightwidth):
                for iy in range(maxbottomheight):
                    if ix <= maxrightwidth - self.object_database['topLeftCorner']['w'] - 1 or iy <= maxbottomheight - \
                            self.object_database['topLeftCorner']['h'] - 1:
                        displayObjects.append((self.AddDisplayObject('base',
                                                    maxbasewidth + maxleftwidth - 1 + maxrightwidth + offsetX + maxleftwidth + ix + 20,
                                                    -3 + iy + maxtopheight + 20, 1, 1), False))

                    else:
                        if not already_created_corner:
                            self.object_database['topLeftCorner'][
                                'x'] = maxbasewidth + maxleftwidth - 1 + maxrightwidth + offsetX + maxleftwidth + ix
                            self.object_database['topLeftCorner']['y'] = -3 + iy + maxtopheight
                            already_created_corner = True
                        displayObjects.append((self.AddDisplayObject('base',
                                                    maxbasewidth + maxleftwidth - 1 + maxrightwidth + offsetX + maxleftwidth + ix + 20,
                                                    -3 + iy + maxtopheight + 20, 1, 1), self.object_database['topLeftCorner']['i'] is None))

            already_created_corner = False
            for ix in range(maxleftwidth):
                for iy in range(maxbottomheight):
                    if ix >= self.object_database['topRightCorner']['w'] or iy <= maxbottomheight - \
                            self.object_database['topRightCorner']['h'] - 1:
                        displayObjects.append((self.AddDisplayObject('base',
                                                    maxbasewidth + maxleftwidth - 1 + maxrightwidth + offsetX + maxleftwidth + maxrightwidth + 3 + ix + 20,
                                                    -3 + iy + maxtopheight + 20, 1, 1), False))

                    else:
                        if not already_created_corner:
                            self.object_database['topRightCorner'][
                                'x'] = maxbasewidth + maxleftwidth - 1 + maxrightwidth + offsetX + maxleftwidth + maxrightwidth + 3 + ix
                            self.object_database['topRightCorner']['y'] = -3 + iy + maxtopheight
                            already_created_corner = True
                        displayObjects.append((self.AddDisplayObject('base',
                                                    maxbasewidth + maxleftwidth - 1 + maxrightwidth + offsetX + maxleftwidth + maxrightwidth + 3 + ix + 20,
                                                    -3 + iy + maxtopheight + 20, 1, 1), self.object_database['topRightCorner']['i'] is None))
            already_created_corner = False
            for ix in range(maxrightwidth):
                for iy in range(maxtopheight):
                    if ix <= maxrightwidth - self.object_database['bottomLeftCorner']['w'] - 1 or iy >= \
                            self.object_database['bottomLeftCorner']['h']:
                        displayObjects.append((self.AddDisplayObject('base',
                                                    maxbasewidth + maxleftwidth - 1 + maxrightwidth + offsetX + maxleftwidth + ix + 20,
                                                    -3 + iy + maxtopheight + 3 + maxbottomheight + 20, 1, 1), False))

                    else:
                        if not already_created_corner:
                            self.object_database['bottomLeftCorner'][
                                'x'] = maxbasewidth + maxleftwidth - 1 + maxrightwidth + offsetX + maxleftwidth + ix
                            self.object_database['bottomLeftCorner']['y'] = -3 + iy + maxtopheight + 3 + maxbottomheight
                            already_created_corner = True
                        displayObjects.append((self.AddDisplayObject('base',
                                                    maxbasewidth + maxleftwidth - 1 + maxrightwidth + offsetX + maxleftwidth + ix + 20,
                                                     -3 + iy + maxtopheight + 3 + maxbottomheight + 20, 1, 1), self.object_database['bottomLeftCorner']['i'] is None))

            already_created_corner = False
            for ix in range(maxleftwidth):
                for iy in range(maxtopheight):
                    if ix >= self.object_database['bottomRightCorner']['w'] or iy >= \
                            self.object_database['bottomRightCorner']['h']:
                        displayObjects.append((self.AddDisplayObject('base',
                                                    maxbasewidth + maxleftwidth - 1 + maxrightwidth + offsetX + maxleftwidth + maxrightwidth + 3 + ix + 20,
                                                    -3 + iy + maxtopheight + 3 + maxbottomheight + 20, 1, 1), False))

                    else:
                        if not already_created_corner:
                            self.object_database['bottomRightCorner'][
                                'x'] = maxbasewidth + maxleftwidth - 1 + maxrightwidth + offsetX + maxleftwidth + maxrightwidth + 3 + ix
                            self.object_database['bottomRightCorner'][
                                'y'] = -3 + iy + maxtopheight + 3 + maxbottomheight
                            already_created_corner = True
                        displayObjects.append((self.AddDisplayObject('base',
                                                    maxbasewidth + maxleftwidth - 1 + maxrightwidth + offsetX + maxleftwidth + maxrightwidth + 3 + ix + 20,
                                                    -3 + iy + maxtopheight + 3 + maxbottomheight + 20, 1, 1), self.object_database['bottomRightCorner']['i'] is None))

            for obj in displayObjects:
                if obj[0] is not None:
                    QuickPaintOperations.autoTileObj(-1, obj[0])

            for obj in displayObjects:
                if obj[0] is not None:
                    QuickPaintOperations.autoTileObj(-1, obj[0])

            for obj in displayObjects:
                if obj[1] and obj[0] in self.display_objects:
                    self.display_objects.remove(obj[0])
                    obj[0].RemoveFromSearchDatabase()
                    if obj[0] in QuickPaintOperations.object_optimize_database: QuickPaintOperations.object_optimize_database.remove(obj[0])

        def calculateBoundaries(self):
            """
            Gets the maximum boundaries for all objects.
            """
            # Fix Widths
            maxbasewidth = max(
                1 if self.object_database['top']['i'] is None else self.object_database['top']['i'].width,
                1 if self.object_database['base']['i'] is None else self.object_database['base']['i'].width,
                1 if self.object_database['bottom']['i'] is None else self.object_database['bottom']['i'].width) if \
                self.object_database['base']['i'] is not None else 1
            maxleftwidth = max(
                1 if self.object_database['topLeft']['i'] is None else self.object_database['topLeft']['i'].width,
                1 if self.object_database['bottomRightCorner']['i'] is None else
                self.object_database['bottomRightCorner']['i'].width,
                1 if self.object_database['left']['i'] is None else self.object_database['left']['i'].width,
                1 if self.object_database['bottomLeft']['i'] is None else self.object_database['bottomLeft']['i'].width,
                1 if self.object_database['topRightCorner']['i'] is None else self.object_database['topRightCorner'][
                    'i'].width) if self.object_database['base']['i'] is not None else 1
            maxrightwidth = max(
                1 if self.object_database['topRight']['i'] is None else self.object_database['topRight']['i'].width,
                1 if self.object_database['bottomLeftCorner']['i'] is None else
                self.object_database['bottomLeftCorner']['i'].width,
                1 if self.object_database['right']['i'] is None else self.object_database['right']['i'].width,
                1 if self.object_database['bottomRight']['i'] is None else self.object_database['bottomRight'][
                    'i'].width,
                1 if self.object_database['topLeftCorner']['i'] is None else self.object_database['topLeftCorner'][
                    'i'].width) if self.object_database['base']['i'] is not None else 1
            # Fix Heights
            maxbaseheight = max(
                1 if self.object_database['right']['i'] is None else self.object_database['right']['i'].height,
                1 if self.object_database['base']['i'] is None else self.object_database['base']['i'].height,
                1 if self.object_database['left']['i'] is None else self.object_database['left']['i'].height) if \
                self.object_database['base']['i'] is not None else 1
            maxtopheight = max(
                1 if self.object_database['topLeft']['i'] is None else self.object_database['topLeft']['i'].height,
                1 if self.object_database['bottomRightCorner']['i'] is None else
                self.object_database['bottomRightCorner']['i'].height,
                1 if self.object_database['top']['i'] is None else self.object_database['top']['i'].height,
                1 if self.object_database['topRight']['i'] is None else self.object_database['topRight']['i'].height,
                1 if self.object_database['bottomLeftCorner']['i'] is None else
                self.object_database['bottomLeftCorner']['i'].height) if self.object_database['base'][
                                                                             'i'] is not None else 1
            maxbottomheight = max(
                1 if self.object_database['bottomLeft']['i'] is None else self.object_database['bottomLeft'][
                    'i'].height,
                1 if self.object_database['topRightCorner']['i'] is None else self.object_database['topRightCorner'][
                    'i'].height,
                1 if self.object_database['bottom']['i'] is None else self.object_database['bottom']['i'].height,
                1 if self.object_database['bottomRight']['i'] is None else self.object_database['bottomRight'][
                    'i'].height,
                1 if self.object_database['topLeftCorner']['i'] is None else self.object_database['topLeftCorner'][
                    'i'].height) if self.object_database['base']['i'] is not None else 1
            return maxbasewidth, maxleftwidth, maxrightwidth, maxbaseheight, maxtopheight, maxbottomheight

        def fixAndUpdateObjects(self):
            """
            Main function for arranging/positioning the objects in the scene.
            """
            # Get those boundaries
            maxbasewidth, maxleftwidth, maxrightwidth, maxbaseheight, maxtopheight, maxbottomheight = self.calculateBoundaries()

            for obj in self.display_objects:
                obj.RemoveFromSearchDatabase()

            self.display_objects.clear()

            # Arrange Main Island...
            self.ArrangeMainIsland(maxbasewidth, maxleftwidth, maxrightwidth, maxbaseheight, maxtopheight,
                                   maxbottomheight)

            if len(QuickPaintOperations.object_optimize_database) > 0:
                QuickPaintOperations.optimizeObjects(True)

            doas = []  # Means "Display Objects Already Shifted."
            for obj in self.display_objects:
                obj.objx -= 20
                obj.objy -= 20

                doas.append(obj)

            # Set corner setter island...
            self.ArrangeCornerSetterIsland(1, maxbasewidth, maxleftwidth, maxrightwidth, maxbaseheight, maxtopheight,
                                           maxbottomheight)

            if len(QuickPaintOperations.object_optimize_database) > 0:
                QuickPaintOperations.optimizeObjects(True)

            for obj in self.display_objects:
                if obj not in doas:
                    obj.objx -= 20
                    obj.objy -= 20

            # Let's update the sizes of these objects...
            for obj in self.object_database:
                if (self.object_database[obj]['i'] is not None):
                    self.object_database[obj]['i'].updateObjCacheWH(self.object_database[obj]['w'],
                                                                    self.object_database[obj]['h'])

        def AddDisplayObject(self, type, x, y, width, height):
            """
            Adds a display-only object into the scene. No effect when clicked on.
            """
            if self.object_database['base']['i'] is not None:
                this_type = type  # self.pickObject(type)
                this_obj = self.object_database[this_type]

                if this_obj.get('ts') is not None and this_obj.get('t') is not None:
                    ln = globals_.CurrentLayer
                    layer = globals_.Area.layers[globals_.CurrentLayer]
                    if len(layer) == 0:
                        z = (2 - ln) * 8192
                    else:
                        z = layer[-1].zValue() + 1

                    obj = ObjectItem(this_obj['ts'], this_obj['t'], -1, x, y, width, height, z)
                    self.display_objects.append(obj)
                    QuickPaintOperations.object_optimize_database.append(obj)

                    return obj

            return None

        def pickObject(self, type):
            """
            Finds the object that works for the type name passed from the parameter.
            """
            if (self.object_database[type]['i'] is None):
                if type == 'top' or type == 'bottom' or type == 'left' or type == 'right':
                    return 'base'

                elif (type == 'topRight' or type == 'topLeft') and self.object_database['top']['i'] is not None:
                    return 'top'

                elif type == 'topLeft' and self.object_database['left']['i'] is not None:
                    return 'left'

                elif type == 'topRight' and self.object_database['right']['i'] is not None:
                    return 'right'

                elif (type == 'bottomRight' or type == 'bottomLeft') and self.object_database['bottom'][
                    'i'] is not None:
                    return 'bottom'

                elif type == 'bottomLeft' and self.object_database['left']['i'] is not None:
                    return 'left'

                elif type == 'bottomRight' and self.object_database['right']['i'] is not None:
                    return 'right'

                else:
                    return 'base'

            return type

        def drawObject(self, tiledata, painter, tiles):
            """
            Draws an object.
            """
            item = tiledata['i']
            w = tiledata['w']
            h = tiledata['h']
            _x = tiledata['x']
            _y = tiledata['y']
            self.drawItem(item, painter, tiles, width=w, height=h, x=_x, y=_y)

        def drawItem(self, item, painter, tiles, x=None, y=None, width=None, height=None):
            """
            Draws an object item.
            """
            tmap = []
            i = 0
            if width is None: width = item.width
            if height is None: height = item.height
            if x is None: x = item.objx
            if y is None: y = item.objy

            while i < height:
                tmap.append([None] * width)
                i += 1

            startx = 0
            desty = 0

            exists = True
            if globals_.ObjectDefinitions[item.tileset] is None:
                exists = False
            elif globals_.ObjectDefinitions[item.tileset][item.type] is None:
                exists = False

            for row in item.objdata:
                destrow = tmap[desty]
                destx = startx
                for tile in row:
                    if not exists:
                        destrow[destx] = -1
                        self.BadObjectWarning = True
                    elif tile > 0:
                        destrow[destx] = tile
                    destx += 1
                desty += 1

            painter.save()
            painter.translate(x * 24, y * 24)
            desty = 0
            for row in tmap:
                destx = 0
                for tile in row:
                    pix = None

                    if tile == -1:
                        # Draw unknown tiles
                        pix = globals_.Overrides[globals_.OVERRIDE_UNKNOWN].getCurrentTile()
                    elif tile is not None:
                        pix = tiles[tile].getCurrentTile()

                    if pix is not None:
                        painter.drawPixmap(destx, desty, pix)

                    destx += 24
                desty += 24
            painter.restore()

        def drawEmptyBox(self, filltype, type, painter, fillbrush):
            """
            Draws an empty box.
            """
            self.drawEmptyBoxCoords(filltype, self.object_database[type]['x'], self.object_database[type]['y'],
                                    self.object_database[type]['w'], self.object_database[type]['h'], painter,
                                    fillbrush)

        def drawEmptyBoxCoords(self, filltype, x, y, width, height, painter, fillbrush):
            """
            Draws an empty box with specified position, width, and height.
            """
            if filltype == 'FULL':
                painter.fillRect(x * 24, y * 24, width * 24,
                                 height * 24, fillbrush)

            elif filltype == 'TOP':
                painter.fillRect(x * 24, y * 24 + 6, width * 24,
                                 height * 24 - 6, fillbrush)

            elif filltype == 'RIGHT':
                painter.fillRect(x * 24, y * 24, width * 24 - 6,
                                 height * 24, fillbrush)

            elif filltype == 'BOTTOM':
                painter.fillRect(x * 24, y * 24, width * 24,
                                 height * 24 - 6, fillbrush)

            elif filltype == 'LEFT':
                painter.fillRect(x * 24 + 6, y * 24, width * 24 - 6,
                                 height * 24, fillbrush)

            elif filltype == 'TOPRIGHT':
                painter.fillRect(x * 24, y * 24 + 6, width * 24 - 15,
                                 height * 24 - 6, fillbrush)
                painter.fillRect(x * 24 + width * 24 - 9, y * 24 + 15, 3,
                                 height * 24 - 15, fillbrush)
                painter.fillRect(x * 24 + width * 24 - 15, y * 24 + 9, 6,
                                 height * 24 - 9, fillbrush)

            elif filltype == 'BOTTOMRIGHT':
                painter.fillRect(x * 24, y * 24, width * 24 - 15,
                                 height * 24 - 6, fillbrush)
                painter.fillRect(x * 24 + width * 24 - 9, y * 24, 3,
                                 height * 24 - 15, fillbrush)
                painter.fillRect(x * 24 + width * 24 - 15, y * 24, 6,
                                 height * 24 - 9, fillbrush)

            elif filltype == 'BOTTOMLEFT':
                painter.fillRect(x * 24 + 15, y * 24, width * 24 - 15,
                                 height * 24 - 6, fillbrush)
                painter.fillRect(x * 24 + 9, y * 24, 6, height * 24 - 9,
                                 fillbrush)
                painter.fillRect(x * 24 + 6, y * 24, 3, height * 24 - 15,
                                 fillbrush)

            elif filltype == 'TOPLEFT':
                painter.fillRect(x * 24 + 15, y * 24 + 6, width * 24 - 15,
                                 height * 24 - 6, fillbrush)
                painter.fillRect(x * 24 + 9, y * 24 + 9, 6,
                                 height * 24 - 9, fillbrush)
                painter.fillRect(x * 24 + 6, y * 24 + 15, 3,
                                 height * 24 - 15, fillbrush)

            elif filltype == 'TOPLEFTCORNER':
                painter.fillRect(x * 24, y * 24, width * 24 - 6,
                                 height * 24, fillbrush)
                painter.fillRect(x * 24 + width * 24 - 6, y * 24, 6,
                                 height * 24 - 6, fillbrush)

            elif filltype == 'TOPRIGHTCORNER':
                painter.fillRect(x * 24 + 6, y * 24, width * 24 - 6,
                                 height * 24, fillbrush)
                painter.fillRect(x * 24, y * 24, 6, height * 24 - 6,
                                 fillbrush)

            elif filltype == 'BOTTOMLEFTCORNER':
                painter.fillRect(x * 24, y * 24, width * 24 - 6,
                                 height * 24, fillbrush)
                painter.fillRect(x * 24 + width * 24 - 6, y * 24 + 6, 6,
                                 height * 24 - 6, fillbrush)

            elif filltype == 'BOTTOMRIGHTCORNER':
                painter.fillRect(x * 24 + 6, y * 24, width * 24 - 6,
                                 height * 24, fillbrush)
                painter.fillRect(x * 24, y * 24 + 6, 6, height * 24 - 6,
                                 fillbrush)

            painter.drawRect(x * 24, y * 24, width * 24,
                             height * 24)

        def drawMainIsland(self, painter, tiles, fillbrush):
            """
            Draws the main island.
            """
            Paint_Level2 = False
            if self.object_database['base']['i'] != None:
                # self.drawObject(self.object_database['base'], painter, tiles)
                self.drawEmptyBox('', 'base', painter, fillbrush)
                Paint_Level2 = True

            else:
                self.drawEmptyBox('FULL', 'base', painter, fillbrush)

            if Paint_Level2:
                if self.object_database['top']['i'] != None:
                    # self.drawObject(self.object_database['top'], painter, tiles)
                    self.drawEmptyBox('', 'top', painter, fillbrush)

                else:
                    self.drawEmptyBox('TOP', 'top', painter, fillbrush)

                if self.object_database['right']['i'] != None:
                    # self.drawObject(self.object_database['right'], painter, tiles)
                    self.drawEmptyBox('', 'right', painter, fillbrush)

                else:
                    self.drawEmptyBox('RIGHT', 'right', painter, fillbrush)

                if self.object_database['bottom']['i'] != None:
                    # self.drawObject(self.object_database['bottom'], painter, tiles)
                    self.drawEmptyBox('', 'bottom', painter, fillbrush)

                else:
                    self.drawEmptyBox('BOTTOM', 'bottom', painter, fillbrush)

                if self.object_database['left']['i'] != None:
                    # self.drawObject(self.object_database['left'], painter, tiles)
                    self.drawEmptyBox('', 'left', painter, fillbrush)

                else:
                    self.drawEmptyBox('LEFT', 'left', painter, fillbrush)

                if self.object_database['topRight']['i'] != None:
                    # self.drawObject(self.object_database['topRight'], painter, tiles)
                    self.drawEmptyBox('', 'topRight', painter, fillbrush)

                else:
                    self.drawEmptyBox('TOPRIGHT', 'topRight', painter, fillbrush)

                if self.object_database['bottomRight']['i'] != None:
                    # self.drawObject(self.object_database['bottomRight'], painter, tiles)
                    self.drawEmptyBox('', 'bottomRight', painter, fillbrush)

                else:
                    self.drawEmptyBox('BOTTOMRIGHT', 'bottomRight', painter, fillbrush)

                if self.object_database['bottomLeft']['i'] != None:
                    # self.drawObject(self.object_database['bottomLeft'], painter, tiles)
                    self.drawEmptyBox('', 'bottomLeft', painter, fillbrush)

                else:
                    self.drawEmptyBox('BOTTOMLEFT', 'bottomLeft', painter, fillbrush)

                if self.object_database['topLeft']['i'] != None:
                    # self.drawObject(self.object_database['topLeft'], painter, tiles)
                    self.drawEmptyBox('', 'topLeft', painter, fillbrush)

                else:
                    self.drawEmptyBox('TOPLEFT', 'topLeft', painter, fillbrush)

            return Paint_Level2

        def drawCornerObjects(self, painter, tiles, fillbrush):
            """
            Draws the corner objects.
            """
            if self.object_database['topRightCorner']['i'] != None:
                self.drawObject(self.object_database['topRightCorner'], painter, tiles)
                self.drawEmptyBox('', 'topRightCorner', painter, fillbrush)

            else:
                self.drawEmptyBox('TOPRIGHTCORNER', 'topRightCorner', painter, fillbrush)

            if self.object_database['bottomRightCorner']['i'] != None:
                self.drawObject(self.object_database['bottomRightCorner'], painter, tiles)
                self.drawEmptyBox('', 'bottomRightCorner', painter, fillbrush)

            else:
                self.drawEmptyBox('BOTTOMRIGHTCORNER', 'bottomRightCorner', painter, fillbrush)

            if self.object_database['bottomLeftCorner']['i'] != None:
                self.drawObject(self.object_database['bottomLeftCorner'], painter, tiles)
                self.drawEmptyBox('', 'bottomLeftCorner', painter, fillbrush)

            else:
                self.drawEmptyBox('BOTTOMLEFTCORNER', 'bottomLeftCorner', painter, fillbrush)

            if self.object_database['topLeftCorner']['i'] != None:
                self.drawObject(self.object_database['topLeftCorner'], painter, tiles)
                self.drawEmptyBox('', 'topLeftCorner', painter, fillbrush)
            else:
                self.drawEmptyBox('TOPLEFTCORNER', 'topLeftCorner', painter, fillbrush)

        def drawBackground(self, painter, rect):
            """
            Draws all visible objects
            """
            self.BadObjectWarning = False
            painter.fillRect(rect, self.bgbrush)
            gridpen = QtGui.QPen()
            gridpen.setColor(globals_.theme.color('grid'))
            gridpen.setWidth(4)
            painter.setPen(gridpen)
            painter.translate(self.xoffset, self.yoffset)
            fillbrush = QtGui.QBrush(globals_.theme.color('object_fill_s'))
            painter.scale(self.zoom, self.zoom)
            # Start Painting
            tiles = globals_.Tiles

            for obj in self.display_objects:
                self.drawItem(obj, painter, tiles)

            if self.drawMainIsland(painter, tiles, fillbrush):
                self.drawCornerObjects(painter, tiles, fillbrush)

            if self.BadObjectWarning:
                self.parent.ShowBadObjectWarning()

    def openTextForm(self):
        """
        Opens the dialog that confirms saving a new preset.
        """
        self.Dialog = QtWidgets.QDialog()
        self.ui = self.TextDialog(self.Dialog, self)
        self.Dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        self.Dialog.show()

    def saveToCurrentPresetConfirm(self):
        """
        Opens the dialog that confirms saving the current preset.
        """
        if self.comboBox_4.count() > 0:
            self.Dialog = QtWidgets.QDialog()
            self.ui = self.ConfirmOverwritePresetDialog(self.Dialog)
            self.Dialog.setWindowModality(QtCore.Qt.ApplicationModal)
            self.Dialog.accepted.connect(self.saveCurrentPreset)
            self.Dialog.show()

    def removeCurrentPresetConfirm(self):
        """
        Opens the dialog that confirms removing the current preset.
        """
        if self.comboBox_4.count() > 0:
            self.Dialog = QtWidgets.QDialog()
            self.ui = self.ConfirmRemovePresetDialog(self.Dialog)
            self.Dialog.setWindowModality(QtCore.Qt.ApplicationModal)
            self.Dialog.accepted.connect(self.removeCurrentPreset)
            self.Dialog.show()

    def saveCurrentPreset(self, name=None):
        """
        Saves the current preset to file as a qpp.
        """
        if name is None:
            name = self.comboBox_4.currentText()

        with open("reggiedata/qpsp/" + name + ".qpp", "w") as f:
            for obj in self.scene.object_database:
                f.write(obj + "\t")
                f.write(str(self.scene.object_database[obj]['x']) + "\t")
                f.write(str(self.scene.object_database[obj]['y']) + "\t")
                f.write(str(self.scene.object_database[obj]['ow']) + "\t")
                f.write(str(self.scene.object_database[obj]['oh']) + "\t")

                if self.scene.object_database[obj]['i'] is not None:
                    f.write(str(self.scene.object_database[obj]['i'].tileset) + "\t")
                    f.write(str(self.scene.object_database[obj]['i'].type) + "\t")

                f.write("\n")

    def removeCurrentPreset(self):
        """
        Removes the current preset.
        """
        try:
            os.remove("reggiedata/qpsp/" + self.comboBox_4.currentText() + ".qpp")
        except FileNotFoundError:
            return

        index = self.comboBox_4.currentIndex()
        self.comboBox_4.removeItem(index)
