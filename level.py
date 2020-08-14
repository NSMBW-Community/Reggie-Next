import struct
import pickle
from PyQt5 import QtWidgets

import globals_
import spritelib as SLib
import archive

from tiles import CreateTilesets, LoadTileset
from levelitems import EntranceItem, SpriteItem, ZoneItem, LocationItem, ObjectItem, PathItem, CommentItem

class AbstractLevel:
    """
    Class for an abstract level from any game. Defines the API.
    """

    def __init__(self):
        """
        Initializes the level with default settings
        """
        self.filepath = None
        self.name = 'untitled'

        self.areas = []

    def load(self, data, areaNum):
        """
        Loads a level from bytes data. You MUST reimplement this in subclasses!
        """
        pass

    def save(self):
        """
        Returns the level as a bytes object. You MUST reimplement this in subclasses!
        """
        return b''

    def deleteArea(self, number):
        """
        Removes the area specified. Number is a 1-based value, not 0-based;
        so you would pass a 1 if you wanted to delete the first area.
        """
        del self.areas[number - 1]
        return True


class Level_NSMBW(AbstractLevel):
    """
    Class for a level from New Super Mario Bros. Wii
    """

    def __init__(self):
        """
        Initializes the level with default settings
        """
        super().__init__()
        self.areas.append(Area_NSMBW())

        globals_.Area = self.areas[0]

    def new(self):
        """
        Creates a completely new level
        """
        # global Area

        # Create area objects
        self.areas = []
        newarea = Area_NSMBW()
        globals_.Area = newarea
        SLib.Area = globals_.Area
        self.areas.append(newarea)

    def load(self, data, areaToLoad):
        """
        Loads a NSMBW level from bytes data.
        """
        super().load(data, areaToLoad)

        # global Area

        arc = archive.U8.load(data)

        try:
            arc['course']
        except KeyError:
            return False

        # Sort the area data
        areaData = {}
        for name, val in arc.files:
            if val is None: continue
            name = name.replace('\\', '/').split('/')[-1]

            if not name.startswith('course'): continue
            if not name.endswith('.bin'): continue
            if '_bgdatL' in name:
                # It's a layer file
                if len(name) != 19: continue
                try:
                    thisArea = int(name[6])
                    laynum = int(name[14])
                except ValueError:
                    continue
                if not (0 < thisArea < 5): continue

                if thisArea not in areaData: areaData[thisArea] = [None] * 4
                areaData[thisArea][laynum + 1] = val
            else:
                # It's the course file
                if len(name) != 11: continue
                try:
                    thisArea = int(name[6])
                except ValueError:
                    continue
                if not (0 < thisArea < 5): continue

                if thisArea not in areaData: areaData[thisArea] = [None] * 4
                areaData[thisArea][0] = val

        # Create area objects
        self.areas = []
        thisArea = 1
        while thisArea in areaData:
            course = areaData[thisArea][0]
            L0 = areaData[thisArea][1]
            L1 = areaData[thisArea][2]
            L2 = areaData[thisArea][3]

            if thisArea == areaToLoad:
                newarea = Area_NSMBW()
                globals_.Area = newarea
                SLib.Area = globals_.Area
            else:
                newarea = AbstractArea()

            newarea.areanum = thisArea
            newarea.load(course, L0, L1, L2)
            self.areas.append(newarea)

            thisArea += 1

        return True

    def save(self):
        """
        Save the level back to a file
        """

        # Make a new archive
        newArchive = archive.U8()

        # Create a folder within the archive
        newArchive['course'] = None

        # Go through the areas, save them and add them back to the archive
        for areanum, area in enumerate(self.areas):
            course, L0, L1, L2 = area.save()

            if course is not None:
                newArchive['course/course%d.bin' % (areanum + 1)] = course
            if L0 is not None:
                newArchive['course/course%d_bgdatL0.bin' % (areanum + 1)] = L0
            if L1 is not None:
                newArchive['course/course%d_bgdatL1.bin' % (areanum + 1)] = L1
            if L2 is not None:
                newArchive['course/course%d_bgdatL2.bin' % (areanum + 1)] = L2

        # return the U8 archive data
        return newArchive._dump()

    def saveNewArea(self, course_new, L0_new, L1_new, L2_new):
        """
        Save the level back to a file
        """

        # Make a new archive
        newArchive = archive.U8()

        # Create a folder within the archive
        newArchive['course'] = None

        # Go through the areas, save them and add them back to the archive
        for areanum, area in enumerate(self.areas):
            course, L0, L1, L2 = area.save()

            if course is not None:
                newArchive['course/course%d.bin' % (areanum + 1)] = course
            if L0 is not None:
                newArchive['course/course%d_bgdatL0.bin' % (areanum + 1)] = L0
            if L1 is not None:
                newArchive['course/course%d_bgdatL1.bin' % (areanum + 1)] = L1
            if L2 is not None:
                newArchive['course/course%d_bgdatL2.bin' % (areanum + 1)] = L2

        if course_new is not None:
            newArchive['course/course%d.bin' % (len(self.areas) + 1)] = course_new
        if L0_new is not None:
            newArchive['course/course%d_bgdatL0.bin' % (len(self.areas) + 1)] = L0_new
        if L1_new is not None:
            newArchive['course/course%d_bgdatL1.bin' % (len(self.areas) + 1)] = L1_new
        if L2_new is not None:
            newArchive['course/course%d_bgdatL2.bin' % (len(self.areas) + 1)] = L2_new

        # return the U8 archive data
        return newArchive._dump()


class AbstractArea:
    """
    An extremely basic abstract area. Implements the basic function API.
    """

    def __init__(self):
        self.areanum = 1
        self.course = None
        self.L0 = None
        self.L1 = None
        self.L2 = None

    def load(self, course, L0, L1, L2):
        self.course = course
        self.L0 = L0
        self.L1 = L1
        self.L2 = L2

    def save(self):
        return (self.course, self.L0, self.L1, self.L2)


class AbstractParsedArea(AbstractArea):
    """
    An area that is parsed to load sprites, entrances, etc. Still abstracted among games.
    Don't instantiate this! It could blow up becuase many of the functions are only defined
    within subclasses. If you want an area object, use a game-specific subclass.
    """

    def __init__(self):
        """
        Creates a completely new area
        """

        # Default area number
        self.areanum = 1

        # Settings
        self.defEvents = 0
        self.wrapFlag = 0
        self.timeLimit = 200
        self.unk1 = 0
        self.startEntrance = 0
        self.unk2 = 0
        self.unk3 = 0

        # Lists of things
        self.entrances = []
        self.sprites = []
        self.zones = []
        self.locations = []
        self.pathdata = []
        self.paths = []
        self.comments = []
        self.layers = [[], [], []]

        # Metadata
        self.LoadReggieInfo(None)

        # Load tilesets
        CreateTilesets()
        LoadTileset(0, self.tileset0)
        LoadTileset(1, self.tileset1)

    def load(self, course, L0, L1, L2):
        """
        Loads an area from the archive files
        """

        # Load in the course file and blocks
        self.LoadBlocks(course)

        # Load stuff from individual blocks
        self.LoadTilesetNames()  # block 1
        self.LoadOptions()  # block 2
        self.LoadEntrances()  # block 7
        self.LoadZones()  # block 10 (also blocks 3, 5, and 6)
        self.LoadLocations()  # block 11
        self.LoadPaths()  # block 12 and 13
        # Load the editor metadata
        if self.block1pos[0] != 0x70:
            rddata = course[0x70:self.block1pos[0]]
            self.LoadReggieInfo(rddata)
        else:
            self.LoadReggieInfo(None)
        del self.block1pos

        # Now, load the comments
        self.LoadComments()

        if not globals_.firstLoad:
            # Load the object layers
            CreateTilesets()
            if self.tileset0 != '': LoadTileset(0, self.tileset0)
            if self.tileset1 != '': LoadTileset(1, self.tileset1)
            if self.tileset2 != '': LoadTileset(2, self.tileset2)
            if self.tileset3 != '': LoadTileset(3, self.tileset3)
        else:
            # Load the object layers
            globals_.firstLoad = False

        self.LoadSprites()  # block 8

        self.layers = [[], [], []]

        if L0 is not None:
            self.LoadLayer(0, L0)
        if L1 is not None:
            self.LoadLayer(1, L1)
        if L2 is not None:
            self.LoadLayer(2, L2)

        # Delete self.blocks
        # del self.blocks

        return True

    def save(self):
        """
        Save the area back to a file
        """
        # prepare this because otherwise the game refuses to load some sprites
        self.SortSpritesByZone()

        # save each block first
        self.SaveTilesetNames()  # block 1
        self.SaveOptions()  # block 2
        self.SaveEntrances()  # block 7
        self.SaveSprites()  # block 8
        self.SaveLoadedSprites()  # block 9
        self.SaveZones()  # block 10 (and 3, 5 and 6)
        self.SaveLocations()  # block 11
        self.SavePaths()

        rdata = bytearray(self.Metadata.save())
        if len(rdata) % 4 != 0:
            rdata += bytes(4 - (len(rdata) % 4))

        rdata = bytes(rdata)

        # Save the main course file
        # We'll be passing over the blocks array two times.
        # Using bytearray here because it offers mutable bytes
        # and works directly with struct.pack_into(), so it's a
        # win-win situation
        FileLength = (14 * 8) + len(rdata)
        for block in self.blocks:
            FileLength += len(block)

        course = bytearray(FileLength)
        saveblock = struct.Struct('>II')

        HeaderOffset = 0
        FileOffset = (14 * 8) + len(rdata)
        struct.pack_into('%ds' % len(rdata), course, 0x70, rdata)

        for block in self.blocks:
            blocksize = len(block)
            saveblock.pack_into(course, HeaderOffset, FileOffset, blocksize)
            if blocksize > 0:
                course[FileOffset:FileOffset + blocksize] = block
            HeaderOffset += 8
            FileOffset += blocksize

        # return stuff
        return (
            bytes(course),
            self.SaveLayer(0),
            self.SaveLayer(1),
            self.SaveLayer(2),
        )

    def RemoveFromLayer(self, obj):
        """
        Removes a specific object from the level and updates Z-indices accordingly
        """
        layer = self.layers[obj.layer]
        idx = layer.index(obj)
        del layer[idx]

        for upd in layer[idx:]:
            upd.setZValue(upd.zValue() - 1)

    def SortSpritesByZone(self):
        """
        Sorts the sprite list by zone ID so it will work in-game
        """

        split = {}
        zones = []

        f_MapPositionToZoneID = SLib.MapPositionToZoneID
        zonelist = self.zones

        for sprite in self.sprites:
            zone = f_MapPositionToZoneID(zonelist, sprite.objx, sprite.objy)
            sprite.zoneID = zone
            if not zone in split:
                split[zone] = []
                zones.append(zone)
            split[zone].append(sprite)

        newlist = []
        zones.sort()
        for z in zones:
            newlist += split[z]

        self.sprites = newlist

    def LoadReggieInfo(self, data):
        if (data is None) or (len(data) == 0):
            self.Metadata = Metadata()
            return

        try:
            self.Metadata = Metadata(data)
        except Exception:
            self.Metadata = Metadata()  # fallback


class Area_NSMBW(AbstractParsedArea):
    """
    Class for a parsed NSMBW level area
    """

    def __init__(self):
        """
        Creates a completely new NSMBW area
        """
        # Default tileset names for NSMBW
        self.tileset0 = 'Pa0_jyotyu'
        self.tileset1 = ''
        self.tileset2 = ''
        self.tileset3 = ''

        self.blocks = [b''] * 14
        self.blocks[0] = b'Pa0_jyotyu' + bytes(128 - len('Pa0_jyotyu'))
        self.blocks[1] = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc8\x00\x00\x00\x00\x00\x00\x00\x00'
        self.blocks[3] = bytes(8)
        self.blocks[7] = b'\xff\xff\xff\xff'

        self.defEvents = 0
        self.timeLimit = 200
        self.creditsFlag = False
        self.startEntrance = 0
        self.ambushFlag = False
        self.toadHouseType = 0
        self.wrapFlag = False
        self.unkFlag1 = False
        self.unkFlag2 = False

        self.unkVal1 = 0
        self.unkVal2 = 0

        self.entrances = []
        self.sprites = []
        self.bounding = []
        self.bgA = []
        self.bgB = []
        self.zones = []
        self.locations = []
        self.pathdata = []
        self.paths = []
        self.comments = []

        super().__init__()

    def LoadBlocks(self, course):
        """
        Loads self.blocks from the course file
        """
        self.blocks = [None] * 14
        getblock = struct.Struct('>II')
        for i in range(14):
            start, length = getblock.unpack_from(course, i * 8)
            self.blocks[i] = course[start:start + length]

        self.block1pos = getblock.unpack_from(course, 0)

    def LoadTilesetNames(self):
        """
        Loads block 1, the tileset names
        """
        data = struct.unpack('>32s32s32s32s', self.blocks[0])
        self.tileset0 = data[0].strip(b'\0').decode('latin-1')
        self.tileset1 = data[1].strip(b'\0').decode('latin-1')
        self.tileset2 = data[2].strip(b'\0').decode('latin-1')
        self.tileset3 = data[3].strip(b'\0').decode('latin-1')

    def LoadOptions(self):
        """
        Loads block 2, the general options
        """
        data = struct.unpack('>IIHh?BxxB?Bx', self.blocks[1])
        defEventsA, defEventsB, wrapByte, self.timeLimit, self.creditsFlag, unkVal, self.startEntrance, self.ambushFlag, self.toadHouseType = data

        self.wrapFlag = bool(wrapByte & 1)
        self.unkFlag1 = bool(wrapByte >> 3)
        self.unkFlag2 = unkVal == 100
        self.defEvents = defEventsA | defEventsB << 32

        """
        Loads block 4, the unknown maybe-more-general-options block
        """
        optdata2 = self.blocks[3]
        optdata2struct = struct.Struct('>xxHHxx')
        data = optdata2struct.unpack(optdata2)
        self.unkVal1, self.unkVal2 = data

    def LoadEntrances(self):
        """
        Loads block 7, the entrances
        """
        entdata = self.blocks[6]
        entstruct = struct.Struct('>HHxxxxBBBBxBBBHxB')

        entrances = []
        for offset in range(0, len(entdata), 20):
            data = entstruct.unpack_from(entdata, offset)
            entrances.append(EntranceItem(*data))

        self.entrances = entrances

    def LoadSprites(self):
        """
        Loads block 8, the sprites
        """
        spritedata = self.blocks[7]
        sprstruct = struct.Struct('>HHH8sxx')
        sprites = []

        unpack = sprstruct.unpack_from
        append = sprites.append
        obj = SpriteItem

        # Ignore the last 4 bytes because they are always 0xFFFFFFFF
        for offset in range(0, len(spritedata) - 4, 16):
            data = unpack(spritedata, offset)
            append(obj(*data))

        self.sprites = sprites

    def LoadZones(self):
        """
        Loads block 3, the bounding preferences
        """
        bdngdata = self.blocks[2]
        bdngstruct = struct.Struct('>llllxBxBxxxx')
        bounding = []

        for offset in range(0, len(bdngdata), 24):
            data = bdngstruct.unpack_from(bdngdata, offset)
            bounding.append(data)

        self.bounding = bounding

        """
        Loads block 5, the top level background values
        """
        bgAdata = self.blocks[4]
        bgAstruct = struct.Struct('>xBhhhhHHHxxxBxxxx')
        bgA = []

        for offset in range(0, len(bgAdata), 24):
            data = bgAstruct.unpack_from(bgAdata, offset)
            bgA.append(data)

        self.bgA = bgA

        """
        Loads block 6, the bottom level background values
        """
        bgBdata = self.blocks[5]
        bgBstruct = struct.Struct('>xBhhhhHHHxxxBxxxx')
        bgB = []

        for offset in range(0, len(bgBdata), 24):
            data = bgBstruct.unpack_from(bgBdata, offset)
            bgB.append(data)

        self.bgB = bgB

        """
        Loads block 10, the zone data
        """
        zonedata = self.blocks[9]
        zonestruct = struct.Struct('>HHHHHHBBBBxBBBBxBB')
        zones = []

        for offset in range(0, len(zonedata), 24):
            dataz = zonestruct.unpack_from(zonedata, offset)

            # Find the proper bounding
            boundObj = None
            id = dataz[7]
            for checkb in self.bounding:
                if checkb[4] == id:
                    boundObj = checkb

            zones.append(ZoneItem(*dataz, boundObj, bgA, bgB, offset // 24))

        self.zones = zones

    def LoadLocations(self):
        """
        Loads block 11, the locations
        """
        locdata = self.blocks[10]
        locstruct = struct.Struct('>HHHHBxxx')
        locations = []

        for offset in range(0, len(locdata), 12):
            data = locstruct.unpack_from(locdata, offset)
            locations.append(LocationItem(*data))

        self.locations = locations

    def LoadLayer(self, idx, layerdata):
        """
        Loads a specific object layer from a string
        """
        objstruct = struct.Struct('>HHHHH')
        z = (2 - idx) * 8192

        append = self.layers[idx].append
        obj = ObjectItem
        unpack = objstruct.unpack_from

        # Ignore the last 2 bytes, because they are always 0xFFFF.
        for offset in range(0, len(layerdata) - 2, 10):
            data = unpack(layerdata, offset)
            append(obj(data[0] >> 12, data[0] & 4095, idx, *data[1:], z))
            z += 1

    def LoadPaths(self):
        """
        Loads block 12, the paths
        """
        pathdata = self.blocks[12]
        pathstruct = struct.Struct('>BxHHH')
        unpack = pathstruct.unpack_from
        pathinfo = []
        paths = []

        for offset in range(0, len(pathdata), 8):
            data = unpack(pathdata, offset)
            nodes = self.LoadPathNodes(data[1], data[2])

            pathinfo.append({
                'id': int(data[0]),
                'nodes': nodes,
                'loops': data[3] == 2
            })

        for xpi in pathinfo:
            for xpj in xpi['nodes']:
                paths.append(PathItem(xpj['x'], xpj['y'], xpi, xpj))

        self.pathdata = pathinfo
        self.paths = paths

    def LoadPathNodes(self, startindex, count):
        """
        Loads block 13, the path nodes
        """
        nodes = []
        nodedata = self.blocks[13]
        nodestruct = struct.Struct('>HHffhxx')
        unpack = nodestruct.unpack_from

        for offset in range(startindex * 16, count * 16, 16):
            data = unpack(nodedata, offset)

            nodes.append({
                'x': int(data[0]),
                'y': int(data[1]),
                'speed': float(data[2]),
                'accel': float(data[3]),
                'delay': int(data[4])
            })

        return nodes

    def LoadComments(self):
        """
        Loads the comments from self.Metadata
        """
        self.comments = []
        data = self.Metadata.binData('InLevelComments_A%d' % self.areanum)
        if data is None:
            return

        idx = 0
        while idx < len(data):
            xpos = data[idx] << 24
            xpos |= data[idx + 1] << 16
            xpos |= data[idx + 2] << 8
            xpos |= data[idx + 3]
            idx += 4
            ypos = data[idx] << 24
            ypos |= data[idx + 1] << 16
            ypos |= data[idx + 2] << 8
            ypos |= data[idx + 3]
            idx += 4
            tlen = data[idx] << 24
            tlen |= data[idx + 1] << 16
            tlen |= data[idx + 2] << 8
            tlen |= data[idx + 3]
            idx += 4
            text = ''
            for char in range(tlen):
                text += chr(data[idx])
                idx += 1

            com = CommentItem(xpos, ypos, text)
            com.listitem = QtWidgets.QListWidgetItem()

            self.comments.append(com)

            com.UpdateListItem()

    def SaveTilesetNames(self):
        """
        Saves the tileset names back to block 1
        """
        self.blocks[0] = ''.join(
            [self.tileset0.ljust(32, '\0'), self.tileset1.ljust(32, '\0'), self.tileset2.ljust(32, '\0'),
             self.tileset3.ljust(32, '\0')]).encode('latin-1')

    def SaveOptions(self):
        """
        Saves block 2, the general options
        """
        wrapByte = 1 if self.wrapFlag else 0
        if self.unkFlag1: wrapByte |= 8
        unkVal = 100 if self.unkFlag2 else 0

        self.blocks[1] = struct.pack('>IIHh?BBBB?Bx',
            self.defEvents & 0xFFFFFFFF, self.defEvents >> 32, wrapByte,
            self.timeLimit, self.creditsFlag, unkVal, unkVal, unkVal,
            self.startEntrance, self.ambushFlag, self.toadHouseType
        )

        """
        Saves block 4, the unknown maybe-more-general-options block
        """
        self.blocks[3] = struct.pack('>xxHHxx', self.unkVal1, self.unkVal2)

    def SaveLayer(self, idx):
        """
        Saves an object layer to a string
        """
        layer = self.layers[idx]
        offset = 0
        objstruct = struct.Struct('>HHHHH')
        buffer = bytearray((len(layer) * 10) + 2)
        f_int = int
        for obj in layer:
            objstruct.pack_into(buffer,
                                offset,
                                f_int((obj.tileset << 12) | obj.type),
                                f_int(obj.objx),
                                f_int(obj.objy),
                                f_int(obj.width),
                                f_int(obj.height))
            offset += 10
        buffer[offset] = 0xFF
        buffer[offset + 1] = 0xFF
        return bytes(buffer)

    def SaveEntrances(self):
        """
        Saves the entrances back to block 7
        """
        offset = 0
        entstruct = struct.Struct('>HHxxxxBBBBxBBBHxB')
        buffer = bytearray(len(self.entrances) * 20)
        zonelist = self.zones
        for entrance in self.entrances:
            zoneID = SLib.MapPositionToZoneID(zonelist, entrance.objx, entrance.objy)
            entstruct.pack_into(buffer, offset, int(entrance.objx), int(entrance.objy),
                                int(entrance.entid), int(entrance.destarea), int(entrance.destentrance),
                                int(entrance.enttype), zoneID, int(entrance.entlayer), int(entrance.entpath),
                                int(entrance.entsettings), int(entrance.cpdirection))
            offset += 20
        self.blocks[6] = bytes(buffer)

    def SavePaths(self):
        """
        Saves the paths back to block 13
        """
        pathstruct = struct.Struct('>BxHHH')
        nodecount = sum(len(path['nodes']) for path in self.pathdata)
        nodebuffer = bytearray(nodecount * 16)
        nodeoffset = 0
        nodeindex = 0
        offset = 0
        buffer = bytearray(len(self.pathdata) * 8)

        for path in self.pathdata:
            if len(path['nodes']) == 0:
                continue

            self.WritePathNodes(nodebuffer, nodeoffset, path['nodes'])

            pathstruct.pack_into(buffer, offset, int(path['id']), int(nodeindex), int(len(path['nodes'])),
                                 2 if path['loops'] else 0)
            offset += 8
            nodeoffset += len(path['nodes']) * 16
            nodeindex += len(path['nodes'])

        self.blocks[12] = bytes(buffer)
        self.blocks[13] = bytes(nodebuffer)

    def WritePathNodes(self, buffer, offst, nodes):
        """
        Writes the path node data to the block 14 bytearray
        """
        offset = int(offst)
        nodestruct = struct.Struct('>HHffhxx')

        for node in nodes:
            nodestruct.pack_into(buffer, offset, int(node['x']), int(node['y']), float(node['speed']),
                                 float(node['accel']), int(node['delay']))
            offset += 16

    def SaveSprites(self):
        """
        Saves the sprites back to block 8
        """
        offset = 0
        sprstruct = struct.Struct('>HHH6sBcxx')
        buffer = bytearray((len(self.sprites) * 16) + 4)
        f_int = int
        for sprite in self.sprites:
            try:
                sprstruct.pack_into(buffer, offset, f_int(sprite.type), f_int(sprite.objx), f_int(sprite.objy),
                                    sprite.spritedata[:6], sprite.zoneID, bytes([sprite.spritedata[7]]))
            except:
                # Hopefully this will solve the mysterious bug, and will
                # soon no longer be necessary.
                raise ValueError('SaveSprites struct.error. Current sprite data dump:\n' + \
                                 str(offset) + '\n' + \
                                 str(sprite.type) + '\n' + \
                                 str(sprite.objx) + '\n' + \
                                 str(sprite.objy) + '\n' + \
                                 str(sprite.spritedata[:6]) + '\n' + \
                                 str(sprite.zoneID) + '\n' + \
                                 str(bytes([sprite.spritedata[7]])) + '\n',
                                 )
            offset += 16
        buffer[offset] = 0xFF
        buffer[offset + 1] = 0xFF
        buffer[offset + 2] = 0xFF
        buffer[offset + 3] = 0xFF
        self.blocks[7] = bytes(buffer)

    def SaveLoadedSprites(self):
        """
        Saves the list of loaded sprites back to block 9
        """
        ls = sorted(set(sprite.type for sprite in self.sprites))

        offset = 0
        sprstruct = struct.Struct('>Hxx')
        buffer = bytearray(len(ls) * 4)
        for s in ls:
            sprstruct.pack_into(buffer, offset, int(s))
            offset += 4

        self.blocks[8] = bytes(buffer)

    def SaveZones(self):
        """
        Saves blocks 10, 3, 5 and 6, the zone data, boundings, bgA and bgB data respectively
        """
        bdngstruct = struct.Struct('>llllxBxBxxxx')
        bgAstruct = struct.Struct('>xBhhhhHHHxxxBxxxx')
        bgBstruct = struct.Struct('>xBhhhhHHHxxxBxxxx')
        zonestruct = struct.Struct('>HHHHHHBBBBxBBBBxBB')

        zcount = len(globals_.Area.zones)
        buffer2 = bytearray(24 * zcount)
        buffer4 = bytearray(24 * zcount)
        buffer5 = bytearray(24 * zcount)
        buffer9 = bytearray(24 * zcount)

        for i, z in enumerate(globals_.Area.zones):
            offset = i * 24

            bdngstruct.pack_into(buffer2, offset, z.yupperbound, z.ylowerbound, z.yupperbound2, z.ylowerbound2, i, 0xF)
            bgAstruct.pack_into(buffer4, offset, i, z.XscrollA, z.YscrollA, z.YpositionA, z.XpositionA, z.bg1A, z.bg2A,
                                z.bg3A, z.ZoomA)
            bgBstruct.pack_into(buffer5, offset, i, z.XscrollB, z.YscrollB, z.YpositionB, z.XpositionB, z.bg1B, z.bg2B,
                                z.bg3B, z.ZoomB)
            zonestruct.pack_into(buffer9, offset, z.objx, z.objy, z.width, z.height, z.modeldark, z.terraindark, i, i,
                                 z.cammode, z.camzoom, z.visibility, i, i, z.camtrack, z.music, z.sfxmod)

        self.blocks[2] = bytes(buffer2)
        self.blocks[4] = bytes(buffer4)
        self.blocks[5] = bytes(buffer5)
        self.blocks[9] = bytes(buffer9)

    def SaveLocations(self):
        """
        Saves block 11, the location data
        """
        locstruct = struct.Struct('>HHHHBxxx')
        buffer = bytearray(12 * len(globals_.Area.locations))

        for i, l in enumerate(globals_.Area.locations):
            locstruct.pack_into(buffer, i * 12, int(l.objx), int(l.objy), int(l.width), int(l.height), int(l.id))

        self.blocks[10] = bytes(buffer)

    def RemoveFromLayer(self, obj):
        """
        Removes a specific object from the level and updates Z indices accordingly
        """
        layer = self.layers[obj.layer]
        idx = layer.index(obj)
        del layer[idx]

        for upd in layer[idx:]:
            upd.setZValue(upd.zValue() - 1)

    def SortSpritesByZone(self):
        """
        Sorts the sprite list by zone ID so it will work in-game
        """

        split = {}
        zones = []

        f_MapPositionToZoneID = SLib.MapPositionToZoneID
        zonelist = self.zones

        for sprite in self.sprites:
            zone = f_MapPositionToZoneID(zonelist, sprite.objx, sprite.objy)
            sprite.zoneID = zone
            if not zone in split:
                split[zone] = []
                zones.append(zone)
            split[zone].append(sprite)

        newlist = []
        zones.sort()
        for z in zones:
            newlist += split[z]

        self.sprites = newlist

    def LoadReggieInfo(self, data):
        if (data is None) or (len(data) == 0):
            self.Metadata = Metadata()
            return

        try:
            self.Metadata = Metadata(data)
        except Exception:
            self.Metadata = Metadata()  # fallback


class AbstractBackground:
    """
    A class that represents an abstract background for a zone (both bgA and bgB)
    """

    def __init__(self, xScroll=1, yScroll=1, xPos=1, yPos=1):
        self.xScroll = xScroll
        self.yScroll = yScroll
        self.xPos = xPos
        self.yPos = yPos

    def save(self, idnum=0):
        return b''


class Background_NSMBW(AbstractBackground):
    """
    A class that represents a background from New Super Mario Bros. Wii
    """
    pass  # not yet implemented


class Metadata:
    """
    Class for the new level metadata system
    """

    # This new system is much more useful and flexible than the old
    # system, but is incompatible with older versions of Reggie.
    # They will fail to understand the data, and skip it like it
    # doesn't exist. The new system is written with forward-compatibility
    # in mind. Thus, when newer versions of Reggie are created
    # with new metadata values, they will be easily able to add to
    # the existing ones. In addition, the metadata system is lossless,
    # so unrecognized values will be preserved when you open and save.

    # Type values:
    # 0 = binary
    # 1 = string
    # 2+ = undefined as of now - future Reggies can use them
    # Theoretical limit to type values is 4,294,967,296

    def __init__(self, data=None):
        """
        Creates a metadata object with the data given
        """
        self.DataDict = {}
        if data is None: return

        if data[0:4] != b'MD2_':
            # This is old-style metadata - convert it
            try:
                strdata = ''
                for d in data: strdata += chr(d)
                level_info = pickle.loads(strdata)
                for k, v in level_info.iteritems():
                    self.setStrData(k, v)
            except Exception:
                pass
            if ('Website' not in self.DataDict) and ('Webpage' in self.DataDict):
                self.DataDict['Website'] = self.DataDict['Webpage']
            return

        # Iterate through the data
        idx = 4
        while idx < len(data) - 4:

            # Read the next (first) four bytes - the key length
            rawKeyLen = data[idx:idx + 4]
            idx += 4

            keyLen = (rawKeyLen[0] << 24) | (rawKeyLen[1] << 16) | (rawKeyLen[2] << 8) | rawKeyLen[3]

            # Read the next (key length) bytes - the key (as a str)
            rawKey = data[idx:idx + keyLen]
            idx += keyLen

            key = ''
            for b in rawKey: key += chr(b)

            # Read the next four bytes - the number of type entries
            rawTypeEntries = data[idx:idx + 4]
            idx += 4

            typeEntries = (rawTypeEntries[0] << 24) | (rawTypeEntries[1] << 16) | (rawTypeEntries[2] << 8) | \
                          rawTypeEntries[3]

            # Iterate through each type entry
            for entry in range(typeEntries):
                # Read the next four bytes - the type
                rawType = data[idx:idx + 4]
                idx += 4

                type = (rawType[0] << 24) | (rawType[1] << 16) | (rawType[2] << 8) | rawType[3]

                # Read the next four bytes - the data length
                rawDataLen = data[idx:idx + 4]
                idx += 4

                dataLen = (rawDataLen[0] << 24) | (rawDataLen[1] << 16) | (rawDataLen[2] << 8) | rawDataLen[3]

                # Read the next (data length) bytes - the data (as bytes)
                entryData = data[idx:idx + dataLen]
                idx += dataLen

                # Add it to typeData
                self.setOtherData(key, type, entryData)

    def binData(self, key):
        """
        Returns the binary data associated with key
        """
        return self.otherData(key, 0)

    def strData(self, key):
        """
        Returns the string data associated with key
        """
        data = self.otherData(key, 1)
        if data is None: return
        s = ''
        for d in data: s += chr(d)
        return s

    def otherData(self, key, type):
        """
        Returns unknown data, with the given type value, associated with key (as binary data)
        """
        if key not in self.DataDict: return
        if type not in self.DataDict[key]: return
        return self.DataDict[key][type]

    def setBinData(self, key, value):
        """
        Sets binary data, overwriting any existing binary data with that key
        """
        self.setOtherData(key, 0, value)

    def setStrData(self, key, value):
        """
        Sets string data, overwriting any existing string data with that key
        """
        data = []
        for char in value: data.append(ord(char))
        self.setOtherData(key, 1, data)

    def setOtherData(self, key, type, value):
        """
        Sets other (binary) data, overwriting any existing data with that key and type
        """
        if key not in self.DataDict: self.DataDict[key] = {}
        self.DataDict[key][type] = value

    def save(self):
        """
        Returns a bytes object that can later be loaded from
        """

        # Sort self.DataDict
        dataDictSorted = []
        for dataKey in self.DataDict: dataDictSorted.append((dataKey, self.DataDict[dataKey]))
        dataDictSorted.sort(key=lambda entry: entry[0])

        data = []

        # Add 'MD2_'
        data.append(ord('M'))
        data.append(ord('D'))
        data.append(ord('2'))
        data.append(ord('_'))

        # Iterate through self.DataDict
        for dataKey, types in dataDictSorted:

            # Add the key length (4 bytes)
            keyLen = len(dataKey)
            data.append(keyLen >> 24)
            data.append((keyLen >> 16) & 0xFF)
            data.append((keyLen >> 8) & 0xFF)
            data.append(keyLen & 0xFF)

            # Add the key (key length bytes)
            for char in dataKey: data.append(ord(char))

            # Sort the types
            typesSorted = []
            for type in types: typesSorted.append((type, types[type]))
            typesSorted.sort(key=lambda entry: entry[0])

            # Add the number of types (4 bytes)
            typeNum = len(typesSorted)
            data.append(typeNum >> 24)
            data.append((typeNum >> 16) & 0xFF)
            data.append((typeNum >> 8) & 0xFF)
            data.append(typeNum & 0xFF)

            # Iterate through typesSorted
            for type, typeData in typesSorted:

                # Add the type (4 bytes)
                data.append(type >> 24)
                data.append((type >> 16) & 0xFF)
                data.append((type >> 8) & 0xFF)
                data.append(type & 0xFF)

                # Add the data length (4 bytes)
                dataLen = len(typeData)
                data.append(dataLen >> 24)
                data.append((dataLen >> 16) & 0xFF)
                data.append((dataLen >> 8) & 0xFF)
                data.append(dataLen & 0xFF)

                # Add the data (data length bytes)
                for d in typeData: data.append(d)

        return data
