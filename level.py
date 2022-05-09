import struct
from PyQt5 import QtWidgets

import globals_
import spritelib as SLib
import archive

from tiles import CreateTilesets, LoadTileset
from levelitems import EntranceItem, SpriteItem, ZoneItem, LocationItem, ObjectItem, PathItem, CommentItem
from misc2 import DecodeOldReggieInfo
from spriteeditor import SpriteEditorWidget

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

        # change all later areas to use the correct num
        for i, area in enumerate(self.areas, 1):
            area.set_num(i)

        return True

    def changeArea(self, number):
        """
        Changes the current area to the specified area in the loaded level
        archive. Note that number is 1-based, not 0-based.
        """
        return False


class Level_NSMBW(AbstractLevel):
    """
    Class for a level from New Super Mario Bros. Wii
    """

    def __init__(self):
        """
        Initializes the level with default settings
        """
        super().__init__()
        self.new(False)

    def new(self, load=True):
        """
        Creates a completely new level
        """
        # Create area objects
        self.areas = []

        new_area = Area(1)

        if load:
            new_area.load_defaults()

        globals_.Area = new_area
        SLib.Area = new_area

        self.areas.append(new_area)

    def load(self, data, areaToLoad):
        """
        Loads a NSMBW level from bytes data.
        """
        super().load(data, areaToLoad)

        arc = archive.U8.load(data)

        if "course" not in arc:
            return False

        # Sort the area data
        areaData = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]
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

                areaData[thisArea - 1][laynum + 1] = val
            else:
                # It's the course file
                if len(name) != 11: continue
                try:
                    thisArea = int(name[6])
                except ValueError:
                    continue
                if not (0 < thisArea < 5): continue

                areaData[thisArea - 1][0] = val

        # Create area objects
        self.areas = []
        for i, data in enumerate(areaData, 1):
            course, L0, L1, L2 = data

            if course is None:
                continue

            new_area = Area(i)
            new_area.set_data(course, L0, L1, L2)
            self.areas.append(new_area)

        self.areas[areaToLoad - 1].load()
        globals_.Area = self.areas[areaToLoad - 1]
        SLib.Area = self.areas[areaToLoad - 1]

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
        for i, area in enumerate(self.areas):
            assert area.areanum == i + 1, (area.areanum, i + 1)

            course, L0, L1, L2 = area.save()

            if course is not None:
                newArchive['course/course%d.bin' % area.areanum] = course
            if L0 is not None:
                newArchive['course/course%d_bgdatL0.bin' % area.areanum] = L0
            if L1 is not None:
                newArchive['course/course%d_bgdatL1.bin' % area.areanum] = L1
            if L2 is not None:
                newArchive['course/course%d_bgdatL2.bin' % area.areanum] = L2

        # return the U8 archive data
        return newArchive._dump()

    def appendArea(self, course_new, L0_new, L1_new, L2_new):
        """
        Creates a new area and adds it to the current level.
        """
        # Add new area
        new_area = Area(len(self.areas) + 1)
        new_area.set_data(course_new, L0_new, L1_new, L2_new)
        self.areas.append(new_area)

    def changeArea(self, number):
        """
        Changes the current area to the specified area in the loaded level
        archive. Note that number is 1-based, not 0-based.
        """
        current_num = globals_.Area.areanum

        # self.areas[current_num - 1] should be unloaded.
        self.areas[current_num - 1].unload()

        # Set the globals properly
        globals_.Area = self.areas[number - 1]
        SLib.Area = self.areas[number - 1]

        # self.areas[number - 1] should be loaded.
        self.areas[number - 1].load()

        return True


class Area:
    """
    Class for a parsed NSMBW level area
    """

    def __init__(self, area_num):
        """
        Creates a completely new NSMBW area
        """
        self.areanum = area_num
        self.course = None
        self.L0 = None
        self.L1 = None
        self.L2 = None

        # Default tileset names
        self.tileset0 = 'Pa0_jyotyu'
        self.tileset1 = ''
        self.tileset2 = ''
        self.tileset3 = ''

        self.blocks = [b''] * 14
        self.blocks[0] = b'Pa0_jyotyu' + bytes(128 - len('Pa0_jyotyu'))
        self.blocks[1] = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x2c\x00\x00\x00\x00\x00\x00\x00\x00'
        self.blocks[3] = bytes(8)
        self.blocks[7] = b'\xff\xff\xff\xff'

        self.defEvents = 0
        self.timeLimit = 300
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
        self.camprofiles = []
        self.paths = []
        self.comments = []
        self.layers = [[], [], []]
        self.loaded_sprites = set()
        self.force_loaded_sprites = set()
        self.sprite_idtypes = {}  # {idtype: {id: number of usages of id}}

        self.MetaData = None
        self._is_loaded = False

        CreateTilesets()

    def set_num(self, area_num):
        """
        Changes the area number of this area.
        """
        self.areanum = area_num

    def load_defaults(self):
        """
        Loads default data.
        """
        # Metadata
        self.LoadReggieInfo(None)

        # Load tilesets
        CreateTilesets()
        LoadTileset(0, self.tileset0)
        LoadTileset(1, self.tileset1)
        LoadTileset(2, self.tileset2)
        LoadTileset(3, self.tileset3)

        # Mark the area as loaded
        self._is_loaded = True

    def set_data(self, course, L0, L1, L2):
        """
        Assigns the archive file data to this area.
        """
        self.course = course
        self.L0 = L0
        self.L1 = L1
        self.L2 = L2

    def unload(self):
        """
        Unloads most of an area, except for the raw data
        """
        assert self._is_loaded

        del self.blocks
        del self.layers
        del self.Metadata
        del self.tileset0
        del self.tileset1
        del self.tileset2
        del self.tileset3
        del self.wrapFlag
        del self.unkFlag1
        del self.unkFlag2
        del self.defEvents
        del self.unkVal1
        del self.unkVal2
        del self.entrances
        del self.sprites
        del self.bgA
        del self.bgB
        del self.zones
        del self.locations
        del self.camprofiles
        del self.paths
        del self.comments
        del self.sprite_idtypes

        self._is_loaded = False

    def load(self):
        """
        Loads an area from the archive files
        """
        assert not self._is_loaded

        # Load in the course file and blocks - if the course file is None, we
        # just create a new area with the default settings (as stored in the
        # already initialised self.blocks)
        if self.course is not None:
            self.LoadBlocks(self.course)

        # Load the editor metadata
        if self.course is not None and self.block1pos[0] != 0x70:
            rddata = self.course[0x70:self.block1pos[0]]
            self.LoadReggieInfo(rddata)
        else:
            self.LoadReggieInfo(None)

        if hasattr(self, "block1pos"):
            del self.block1pos

        # Load stuff from individual blocks
        self.LoadTilesetNames()  # block 1
        self.LoadOptions()  # block 2
        self.LoadEntrances()  # block 7
        self.LoadLoadedSprites()  # block 9
        self.LoadZones()  # block 10 (also blocks 3, 5, and 6)
        self.LoadLocations()  # block 11
        self.LoadCamProfiles()  # block 12
        self.LoadPaths()  # block 13 and 14

        # Now, load the comments
        self.LoadComments()

        # Reset the tilesets if this is not the first load
        if not globals_.firstLoad:
            CreateTilesets()
        else:
            globals_.firstLoad = False

        # Load the tilesets
        LoadTileset(0, self.tileset0)
        LoadTileset(1, self.tileset1)
        LoadTileset(2, self.tileset2)
        LoadTileset(3, self.tileset3)

        # Load the object layers
        self.layers = [[], [], []]

        if self.L0 is not None:
            self.LoadLayer(0, self.L0)
        if self.L1 is not None:
            self.LoadLayer(1, self.L1)
        if self.L2 is not None:
            self.LoadLayer(2, self.L2)

        self.LoadSprites()  # block 8

        self.InitialiseIdTypes()

        self._is_loaded = True
        return True

    def save(self):
        """
        Save the area back to a file
        """
        # first handle the case that the area is not loaded
        if not self._is_loaded:
            return (self.course, self.L0, self.L1, self.L2)

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
        self.SaveCamProfiles()  # block 12
        self.SavePaths()  # blocks 13 and 14

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

        self.course = bytes(course)
        self.L0 = self.SaveLayer(0)
        self.L1 = self.SaveLayer(1)
        self.L2 = self.SaveLayer(2)

        return (self.course, self.L0, self.L1, self.L2)

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
        def compKey(zonelist, sprite):
            id_ = SLib.MapPositionToZoneID(zonelist, sprite.objx, sprite.objy)
            sprite.zoneID = zonelist[id_].id if id_ != -1 else -1
            return id_

        self.sprites.sort(key = lambda s: compKey(self.zones, s))

    def LoadReggieInfo(self, data):
        if not data:
            self.Metadata = Metadata()
            return

        try:
            self.Metadata = Metadata(data)
        except Exception:
            self.Metadata = Metadata()  # fallback

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
        entstruct = struct.Struct('>HHxxxxBBBBxBBBHBB')

        entrances = []
        for offset in range(0, len(entdata), 20):
            data = entstruct.unpack_from(entdata, offset)
            entrances.append(EntranceItem(*data))

        self.entrances = entrances

    def LoadSprites(self):
        """
        Loads block 8, the sprites. This needs to be called after
        'LoadLoadedSprites', because this relies on the loaded sprite ids being
        loaded for calculating the sprites that are forced to load.
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
        self.force_loaded_sprites = self.loaded_sprites - set(sprite.type for sprite in sprites)

    def LoadLoadedSprites(self):
        """
        Loads block 9, the loaded sprite resources.
        """
        self.loaded_sprites = set()
        loading_data = self.blocks[8]
        struct_ = struct.Struct('>Hxx')

        for offset in range(0, len(loading_data), 4):
            sprite_id, = struct_.unpack_from(loading_data, offset)
            self.loaded_sprites.add(sprite_id)

    def LoadZones(self):
        """
        Loads block 3, the bounding preferences
        """
        bdngdata = self.blocks[2]
        bdngstruct = struct.Struct('>4lHHhh')
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
            zones.append(ZoneItem(*dataz, bounding, bgA, bgB, offset // 24))

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

    def LoadCamProfiles(self):
        """
        Loads block 12, the camera profiles
        """
        profiledata = self.blocks[11]
        profilestruct = struct.Struct('>xxxxxxxxxxxxBBBBxxBx')
        offset = 0
        camprofiles = []

        for offset in range(0, len(profiledata), 20):
            data = profilestruct.unpack_from(profiledata, offset)

            if offset > 0 or any(data):
                camprofiles.append([data[4], data[1], data[2]])

        self.camprofiles = camprofiles

    def LoadPaths(self):
        """
        Loads blocks 13 and 14, the paths and path nodes
        """
        pathdata = self.blocks[12]
        pathstruct = struct.Struct('>BxHHH')
        unpack = pathstruct.unpack_from
        paths = []

        from levelitems import Path

        for offset in range(0, len(pathdata), 8):
            data = unpack(pathdata, offset)
            nodes = self.LoadPathNodes(data[1], data[2])

            path = Path(int(data[0]), globals_.mainWindow.scene, data[3] == 2)

            for node in nodes:
                path.add_node(node['x'], node['y'], node['speed'], node['accel'], node['delay'], add_to_scene=False)

            paths.append(path)

        self.paths = paths

    def LoadPathNodes(self, startindex, count):
        """
        Loads block 14, the path nodes
        """
        nodes = []
        nodedata = self.blocks[13]
        nodestruct = struct.Struct('>HHffhxx')
        unpack = nodestruct.unpack_from

        for offset in range(startindex * 16, (startindex + count) * 16, 16):
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
            xpos, ypos, tlen_maybe = struct.unpack_from(">3I", data, idx)
            idx += 3 * 4

            if tlen_maybe == 0xFFFF_FFFF:
                # Updated version - the number of code points is stored in the
                # next int.
                tlen, = struct.unpack_from(">I", data, idx)
                text = data[idx + 4: idx + 4 + tlen].decode("utf-8")
                idx += 4 + tlen
            else:
                # Old version provided for compatibility. Also tries to properly
                # load non-ascii comments, but that might not work out...
                tlen = tlen_maybe
                try:
                    text = data[idx: idx + tlen].decode("ascii")
                    idx += tlen
                except UnicodeDecodeError:
                    # You used non-ascii characters... Try to save the comment
                    # The xpos is probably not > 2 ** 24, so the next comment
                    # starts with a null byte. We can use that to find the end
                    # of our string
                    null_idx = data.find(b"\0", idx)
                    if null_idx == -1:
                        # This is probably the last comment...
                        null_idx = len(data)

                    text = data[idx: null_idx].decode("utf-8")[:tlen]
                    idx = null_idx

            com = CommentItem(xpos, ypos, text)
            com.listitem = QtWidgets.QListWidgetItem()

            self.comments.append(com)

            com.UpdateListItem()

    def SaveTilesetNames(self):
        """
        Saves the tileset names back to block 1
        """
        self.blocks[0] = struct.pack('>32s32s32s32s',
            self.tileset0.encode('latin-1'),
            self.tileset1.encode('latin-1'),
            self.tileset2.encode('latin-1'),
            self.tileset3.encode('latin-1')
        )

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
        if not layer:
            # Don't create a layer file for an empty layer.
            return None

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
        entstruct = struct.Struct('>HHxxxxBBBBxBBBHBB')
        buffer = bytearray(len(self.entrances) * 20)
        f_MapPositionToZoneID = SLib.MapPositionToZoneID
        zonelist = self.zones
        for entrance in self.entrances:
            zoneID = f_MapPositionToZoneID(zonelist, entrance.objx, entrance.objy, True)
            if zoneID == -1:
                # No zone was found in the level.
                # Pretend the entrance belongs to zone 0, even though this zone
                # does not exist. The level won't work in-game anyway, because
                # there are no zones. This default allows users to save areas
                # without zones, so it adds greater flexibility.
                zoneID = 0

            entstruct.pack_into(buffer, offset, int(entrance.objx), int(entrance.objy),
                                int(entrance.entid), int(entrance.destarea), int(entrance.destentrance),
                                int(entrance.enttype), zoneID, int(entrance.entlayer), int(entrance.entpath),
                                int(entrance.entsettings), int(entrance.leave_level), int(entrance.cpdirection))
            offset += 20
        self.blocks[6] = bytes(buffer)

    def SavePaths(self):
        """
        Saves the paths back to block 13
        """
        pathstruct = struct.Struct('>BxHHH')
        nodecount = sum(len(path) for path in self.paths)
        nodebuffer = bytearray(nodecount * 16)
        nodeoffset = 0
        nodeindex = 0
        offset = 0
        buffer = bytearray(len(self.paths) * 8)

        for path in self.paths:
            if not len(path):
                continue

            self.WritePathNodes(nodebuffer, nodeoffset, path)

            pathstruct.pack_into(buffer, offset, path._id, nodeindex, len(path), 2 if path._loops else 0)

            offset += 8
            nodeoffset += len(path) * 16
            nodeindex += len(path)

        self.blocks[12] = bytes(buffer[:offset])
        self.blocks[13] = bytes(nodebuffer)

    def WritePathNodes(self, buffer, offset, path):
        """
        Writes the path node data to the block 14 bytearray
        """
        nodestruct = struct.Struct('>HHffhxx')

        for i in range(len(path)):
            nodestruct.pack_into(buffer, offset, *path.get_node_data(i))
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
            if sprite.zoneID == -1:
                # No zone was found in the area.
                # Pretend the sprite belongs to zone 0, even though this zone
                # does not exist. The area won't work in-game anyway, because
                # there are no zones. This default allows users to save areas
                # without zones, so it adds greater flexibility.
                sprite.zoneID = 0

            try:
                sprstruct.pack_into(buffer, offset, f_int(sprite.type) % 0xFFFF, f_int(sprite.objx), f_int(sprite.objy),
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
        ls = sorted(set(sprite.type for sprite in self.sprites) | self.force_loaded_sprites)

        offset = 0
        sprstruct = struct.Struct('>Hxx')
        buffer = bytearray(len(ls) * 4)
        for s in ls:
            sprstruct.pack_into(buffer, offset, s & 0xFFFF)
            offset += 4

        self.blocks[8] = bytes(buffer)

    def SaveZones(self):
        """
        Saves blocks 10, 3, 5 and 6, the zone data, boundings, bgA and bgB data respectively
        """
        bdngstruct = struct.Struct('>4lHHhh')
        bgAstruct = struct.Struct('>xBhhhhHHHxxxBxxxx')
        bgBstruct = struct.Struct('>xBhhhhHHHxxxBxxxx')
        zonestruct = struct.Struct('>HHHHHHBBBBxBBBBxBB')

        zcount = len(self.zones)
        buffer2 = bytearray(24 * zcount)
        buffer4 = bytearray(24 * zcount)
        buffer5 = bytearray(24 * zcount)
        buffer9 = bytearray(24 * zcount)

        for i, z in enumerate(self.zones):
            offset = i * 24

            # HACK: This should really only save block 10, and use a
            # better way of linking the zone data to the bounds and
            # background data.
            new_bound_id = i
            new_bga_id = i
            new_bgb_id = i

            bdngstruct.pack_into(buffer2, offset,
                z.yupperbound, z.ylowerbound, z.yupperbound2,
                z.ylowerbound2, new_bound_id, z.mpcamzoomadjust,
                z.yupperbound3, z.ylowerbound3
            )

            bgAstruct.pack_into(buffer4, offset,
                new_bga_id, z.XscrollA, z.YscrollA, z.YpositionA,
                z.XpositionA, z.bg1A, z.bg2A, z.bg3A, z.ZoomA
            )

            bgBstruct.pack_into(buffer5, offset,
                new_bgb_id, z.XscrollB, z.YscrollB, z.YpositionB,
                z.XpositionB, z.bg1B, z.bg2B, z.bg3B, z.ZoomB
            )

            zonestruct.pack_into(buffer9, offset,
                z.objx, z.objy, z.width, z.height, z.modeldark,
                z.terraindark, z.id, new_bound_id, z.cammode, z.camzoom,
                z.visibility, new_bga_id, new_bgb_id, z.camtrack,
                z.music, z.sfxmod
            )

        self.blocks[2] = bytes(buffer2)
        self.blocks[4] = bytes(buffer4)
        self.blocks[5] = bytes(buffer5)
        self.blocks[9] = bytes(buffer9)

    def SaveLocations(self):
        """
        Saves block 11, the location data
        """
        locstruct = struct.Struct('>HHHHBxxx')
        buffer = bytearray(12 * len(self.locations))

        for i, l in enumerate(self.locations):
            locstruct.pack_into(buffer, i * 12, int(l.objx), int(l.objy), int(l.width), int(l.height), int(l.id))

        self.blocks[10] = bytes(buffer)

    def SaveCamProfiles(self):
        """
        Saves block 12, the camera profiles data.
        Also appends data to block 3, the bounding data.
        """

        if not self.camprofiles:
            self.blocks[11] = b''
            return

        # Camera profiles include a bounding-block ID, but the game only uses it
        # for one frame before reverting to the zone defaults. So it's not
        # really useful for anything, but we also need to ensure we don't point
        # the camera profiles to any invalid or otherwise terrible bounding
        # settings for that one frame. So we make an extra, all-defaults
        # bounding block and use it for every camera profile.

        bdngstruct = struct.Struct('>4lHHhh')

        bdngid = (len(self.blocks[2]) + 24) // 24
        self.blocks[2] += bdngstruct.pack(0, 0, 0, 0, bdngid, 15, 0, 0)

        profilestruct = struct.Struct('>xxxxxxxxxxxxBBBBxxBx')
        buffer = bytearray(20 * (len(self.camprofiles) + 1))

        offset = 20  # empty first profile to work around game bug
        for p in self.camprofiles:
            profilestruct.pack_into(buffer, offset, bdngid, p[1], p[2], 0, p[0])
            offset += 20

        self.blocks[11] = bytes(buffer)

    def InitialiseIdTypes(self):
        """
        Initialises all used id types in this area.
        """

        self.sprite_idtypes = {}
        decoder = SpriteEditorWidget.PropertyDecoder()

        for sprite in self.sprites:
            sdef = globals_.Sprites[sprite.type]

            # Find what values are used by this sprite
            data = sprite.spritedata

            for field in sdef.fields:
                if field[0] not in (1, 2):
                    # Only values and lists can be idtypes
                    continue

                idtype = field[-1]
                if idtype is None:
                    # Only look at settings with idtypes
                    continue

                value = decoder.retrieve(data, field[2])

                # 3. Add the value to self.sprite_idtypes
                try:
                    counter = self.sprite_idtypes[idtype]
                except KeyError:
                    self.sprite_idtypes[idtype] = {value: 1}
                    continue

                counter[value] = counter.get(value, 0) + 1

    def RemoveSprite(self, sprite):
        """
        This properly removes a sprite from the area.
        """
        # Remove the sprite from the sprites list
        self.sprites.remove(sprite)

        # Remove the ids the sprite used from the id list
        decoder = SpriteEditorWidget.PropertyDecoder()
        sdef = globals_.Sprites[sprite.type]

        # Find what values are used by this sprite
        for field in sdef.fields:
            if field[0] not in (1, 2):
                # Only <value> and <list> tags can have id types
                continue

            idtype = field[-1]
            if idtype is None:
                # Only look at settings with idtypes
                continue

            value = decoder.retrieve(sprite.spritedata, field[2])

            # 3. Decrement the counter for this idtype
            counter = self.sprite_idtypes[idtype]

            if counter[value] == 1:
                del counter[value]
            else:
                counter[value] -= 1


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
                info = DecodeOldReggieInfo(data, {
                    'Creator', 'Title', 'Author', 'Group',
                    'Webpage', 'Password'
                })

                for k, v in info.items():
                    self.setStrData(k, v)
            except Exception:
                pass

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
        return data.decode()

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
        self.setOtherData(key, 1, value.encode("utf-8"))

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
        dataDictSorted = list(self.DataDict.items())
        dataDictSorted.sort(key=lambda entry: entry[0])

        data = b"MD2_"

        # Iterate through self.DataDict
        for dataKey, types in dataDictSorted:

            # Add the key length (4 bytes)
            data += struct.pack(">I", len(dataKey))

            # Add the key (key length bytes)
            data += dataKey.encode("utf-8")

            # Sort the types
            typesSorted = list(types.items())
            typesSorted.sort(key=lambda entry: entry[0])

            # Add the number of types (4 bytes)
            data += struct.pack(">I", len(types))

            # Iterate through typesSorted
            for type, typeData in typesSorted:

                # Add the type (4 bytes)
                # Add the data length (4 bytes)
                data += struct.pack(">2I", type, len(typeData))

                # Add the data (data length bytes)
                data += typeData

        return data
