from PyQt6 import QtCore, QtWidgets, QtGui
import collections
import itertools
import sys
import os
from xml.etree import ElementTree

################################################################################
################################################################################
################################################################################

import globals_
from classlib import CheckBoxSpriteField, DualBoxSpriteField, ExternalSpriteField, ListSpriteField, MenuAction, MultiDualBoxSpriteField, RandTileSelection, SpriteCategory, SpriteField, SpriteSubCategory, SpriteTexSpriteField, TilesetCategory, TilesetFileEntry, ValueSpriteField
from ui import GetIcon
from dirty import setting, setSetting, delSetting

from src.ui.dialogs.diagnostic_tool import DiagnosticToolDialog

################################################################################
################################################################################
################################################################################

def module_path():
    """
    This will get us the program's directory, even if we are frozen using
    PyInstaller.
    """
    if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):  # PyInstaller
        if sys.platform == 'darwin':  # macOS
            # sys.executable is /x/y/z/reggie.app/Contents/MacOS/reggie
            # We need to return /x/y/z/reggie.app/Contents/Resources/

            macos = os.path.dirname(sys.executable)
            if os.path.basename(macos) != 'MacOS':
                return None

            return os.path.join(os.path.dirname(macos), 'Resources')

        else:  # Windows, Linux
            return os.path.dirname(sys.executable)

    if __name__ == 'misc':
        return os.path.dirname(os.path.abspath(__file__))

    return None


def checkContent(data):
    if not data.startswith(b'U\xAA8-'):
        return False

    required = (b'course\0', b'course1.bin\0', b'\0\0\0\x80')
    for r in required:
        if r not in data:
            return False

    return True


def IsNSMBLevel(filename):
    """
    Does some basic checks to confirm a file is a NSMB level
    """
    if not os.path.isfile(filename): return False

    with open(filename, 'rb') as f:
        data = f.read()

    if (data[0] & 0xF0) == 0x40 or not data.startswith(b"U\xAA8-"):  # If LH-compressed or LZ-compressed
        return True

    return checkContent(data)


def FilesAreMissing():
    """
    Checks to see if any of the required files for Reggie are missing
    """

    if not os.path.isdir('reggiedata'):
        QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_MissingFiles', 0), globals_.trans.string('Err_MissingFiles', 1))
        return True

    required = ['icon.png', ]

    missing = []

    for check in required:
        if not os.path.isfile(os.path.join('reggiedata', check)):
            missing.append(check)

    if missing:
        QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_MissingFiles', 0),
                                      globals_.trans.string('Err_MissingFiles', 2, '[files]', ', '.join(missing)))
        return True

    return False


def SetGamePaths(new_stage_path, new_texture_path):
    """
    Sets the NSMBW game path
    """
    # os.path.join crashes if QStrings are used, so we must change the paths to
    # a Python string manually
    globals_.gamedef.SetStageGamePath(str(new_stage_path))
    globals_.gamedef.SetTextureGamePath(str(new_texture_path))


def areValidGamePaths(stage_check='ug', texture_check='ug'):
    """
    Checks to see if the path for NSMBW contains a valid game
    """
    if stage_check == 'ug':
        stage_check = globals_.gamedef.GetStageGamePath()

    if texture_check == 'ug':
        texture_check = globals_.gamedef.GetTextureGamePath()

    if not stage_check or not texture_check:
        return False

    # Check that both the stage and texture folders exist
    if not os.path.isdir(stage_check) or not os.path.isdir(texture_check):
        return False

    # Check that at least one readable level is located in the stage folder
    files = [f for f in os.listdir(stage_check) if os.path.isfile(os.path.join(stage_check, f))]
    for fname in files:
        if os.path.isfile(os.path.join(stage_check, fname)):
            name, ext = os.path.splitext(os.path.join(stage_check, fname))

            # For compressed files, splitting only gives us the LH/LZ extension, while '.arc' is considered part of the filename
            if ext in ('.LH', '.LZ'):
                ext = globals_.FileExtentions[0] + ext
                name = name.removesuffix('.arc')

            if ext in globals_.FileExtentions:
                globals_.FirstStageFilename = name + ext
                return True

    return False


def getResourcePaths(res_name):
    """
    Returns an iterable containing the paths that have the specified resource.
    The paths are included in order from general to specific. That is, the base
    comes before the patch.
    """
    # To make sure that the gamedef is translatable as well, we first need to
    # figure out what paths the gamedef loads its files from
    gamedef_files, is_patch, gamedef_names = globals_.gamedef.recursiveFiles(res_name)

    # Then, we ask the current translation to give a path for each of those
    # gamedefs. If there is no translation for a specific resource and gamedef,
    # the corresponding entry will have the value 'None'.
    trans_files = globals_.trans.paths(res_name, gamedef_names)

    # Combine the gamedef_files and trans_files lists to get them in the right
    # order.
    #   [gamedef_files[0], trans_files[0], ..., gamedef[i], trans_files[i]]
    # If any entry (gamedef or translation) has no value, it will have None. As
    # such, we also need to filter out the None values from the final iterable.
    return filter(lambda x: x is not None, itertools.chain.from_iterable(zip(gamedef_files, trans_files)))


def LoadLevelNames():
    """
    Ensures that the level name info is loaded
    """
    for path in getResourcePaths('levelnames'):
        tree = ElementTree.parse(path)
        root = tree.getroot()

        # Parse the nodes (root acts like a large category)
        globals_.LevelNames = LoadLevelNames_Category(root)


def LoadLevelNames_Category(node):
    """
    Loads a LevelNames XML category
    """
    cat = []
    for child in node:
        if child.tag.lower() == 'category':
            cat.append((str(child.attrib['name']), LoadLevelNames_Category(child)))
        elif child.tag.lower() == 'level':
            cat.append((str(child.attrib['name']), str(child.attrib['file'])))
    return tuple(cat)


def LoadTilesetNames(reload_=False):
    """
    Ensures that the tileset name info is loaded
    """
    if not reload_: return

    # Get paths
    paths = getResourcePaths('tilesets')

    # Read each file
    globals_.TilesetNames = [TilesetCategory() for _ in range(4)]
    for path in paths:
        tree = ElementTree.parse(path)
        root = tree.getroot()

        # Go through each slot
        for node in root:
            if node.tag.lower() != 'slot': continue
            try:
                slot = int(node.attrib['num'])
            except ValueError:
                continue
            if slot > 3: continue

            # Parse the category data into a list
            newlist = TilesetCategory()
            newlist.children = LoadTilesetNames_Category(node)
            newlist.sorted = node.attrib['sorted'].lower() == 'true' if 'sorted' in node.attrib else globals_.TilesetNames[slot].sorted

            # Apply it as a patch over the current entry
            newlist.children = CascadeTilesetNames_Category(globals_.TilesetNames[slot].children, newlist.children)

            # Sort it
            if not newlist.sorted:
                newlist.children = SortTilesetNames_Category(newlist.children)

            globals_.TilesetNames[slot] = newlist



def LoadTilesetNames_Category(node: ElementTree.Element) -> list[TilesetCategory | TilesetFileEntry]:
    """
    Loads a TilesetNames XML category
    """
    cat: list[TilesetCategory | TilesetFileEntry] = []
    for child in node:
        if child.tag.lower() == 'category':
            new = TilesetCategory(child.attrib['name'])
            new.children = LoadTilesetNames_Category(child)
            if 'sorted' in child.attrib:
                new.sorted = str(child.attrib['sorted'].lower()) == 'true'
            cat.append(new)
        elif child.tag.lower() == 'tileset':
            fname = str(child.attrib['filename'])
            cat.append(TilesetFileEntry(fname, str(child.attrib['name'])))

            # read override attribute
            if 'override' not in child.attrib:
                continue

            # override present, add it to the correct type

            types = str(child.attrib['override']).split(',')

            for type_ in types:
                if type_ not in globals_.OverriddenTilesets:
                    raise ValueError("Unknown override type '%s' for tileset '%s'" % (type_, fname))

                globals_.OverriddenTilesets[type_].add(fname)

    return cat


def CascadeTilesetNames_Category(
    lower: list[TilesetCategory | TilesetFileEntry],
    upper: list[TilesetCategory | TilesetFileEntry],
) -> list[TilesetCategory | TilesetFileEntry]:
    """
    Applies upper as a patch of lower
    """
    for item in upper:
        if isinstance(item, TilesetCategory):
            found = False
            for i, lowitem in enumerate(lower):
                if isinstance(lowitem, TilesetCategory) and lowitem.name == item.name:  # names are ==
                    lowitem.children = CascadeTilesetNames_Category(lowitem.children, item.children)
                    found = True
                    break

            if not found:
                i = 0
                while (i < len(lower)) and isinstance(lower[i], TilesetCategory): i += 1
                lower.insert(i + 1, item)

        else: # It's a tileset entry
            found = False
            for i, lowitem in enumerate(lower):
                if not isinstance(lowitem, TilesetFileEntry):
                    continue
                if lowitem.filename == item.filename:  # filenames are ==
                    lower[i] = item
                    found = True
                    break

            if not found:
                lower.append(item)

    return lower


def SortTilesetNames_Category(cat: list[TilesetCategory | TilesetFileEntry]) -> list[TilesetCategory | TilesetFileEntry]:
    """
    Sorts a tileset names category
    """
    # First, remove all category nodes
    cats: list[TilesetCategory] = []
    for node in cat:
        if isinstance(node, TilesetCategory):
            cats.append(node)
    for node in cats: cat.remove(node)

    # Sort the tileset names
    cat.sort(key=lambda entry: entry.name)

    # Sort the data within each category
    for i, cat_ in enumerate(cats):
        cats[i] = cat_
        if not cats[i].sorted: cats[i].children = SortTilesetNames_Category(cats[i].children)

    # Put them back together
    new = cats + cat
    return new


def LoadObjDescriptions(reload_=False):
    """
    Ensures that the object description is loaded
    """
    if globals_.ObjDesc and not reload_: return

    paths = getResourcePaths('ts1_descriptions')

    globals_.ObjDesc = {}
    for path in paths:
        with open(path, 'r', encoding='utf-8') as f:
            raw = [x.strip() for x in f.readlines()]

        for line in raw:
            w = line.split('=')
            globals_.ObjDesc[int(w[0])] = w[1]


def LoadBgANames(reload_=False):
    """
    Ensures that the background name info is loaded
    """
    if globals_.BgANames and not reload_: return

    paths = getResourcePaths('bga')

    globals_.BgANames = []
    for path in paths:
        with open(path, 'r', encoding='utf-8') as f:
            raw = [x.strip() for x in f.readlines()]

        for line in raw:
            w = line.split('=')

            found = False
            for check in globals_.BgANames:
                if check[0] == w[0]:
                    check[1] = w[1]
                    found = True

            if not found: globals_.BgANames.append([w[0], w[1]])

        globals_.BgANames.sort(key=lambda entry: int(entry[0], 16))


def LoadBgBNames(reload_=False):
    """
    Ensures that the background name info is loaded
    """
    if (globals_.BgBNames) and not reload_: return

    paths = getResourcePaths('bgb')

    globals_.BgBNames = []
    for path in paths:
        with open(path, 'r', encoding='utf-8') as f:
            raw = [x.strip() for x in f.readlines()]

        for line in raw:
            w = line.split('=')

            found = False
            for check in globals_.BgBNames:
                if check[0] == w[0]:
                    check[1] = w[1]
                    found = True

            if not found: globals_.BgBNames.append([w[0], w[1]])

        globals_.BgBNames.sort(key=lambda entry: int(entry[0], 16))


def LoadZoneThemes(reload_=False):
    """
    Ensures that custom zone themes get loaded
    """
    if globals_.ZoneThemeValues and not reload_: return

    paths = getResourcePaths('zonethemes')

    for path in paths:
        with open(path, 'r', encoding='utf-8') as f:
            globals_.ZoneThemeValues = [x.strip() for x in f]


def LoadConfig():
    """
    Ensures that gamedef-specific config info is loaded
    """
    for path in getResourcePaths('config'):
        tree = ElementTree.parse(path)

        for node in tree.getroot():
            if node.tag.lower() == 'option':
                opt = node.attrib['key']
                value = node.attrib['value']

                if opt == 'DispConnectPipeDir':
                    globals_.DispConnectedPipeDir = value.strip().lower() == 'true'
                elif opt == 'SpecialEventID':
                    globals_.SpecialEventSpriteID = int(value)
                elif opt == 'AllowSizeHacks':
                    globals_.AllowSizeHacks = value.strip().lower() == 'true'


class SpriteDefinition:
    """
    Stores and manages the data info for a specific sprite
    """

    def __init__(self):
        self.id: int = -1
        self.name: str | None = None
        self.notes: str | None = None
        self.advNotes: str | None = None
        self.relatedObjFiles: str | None = None
        self.yoshiNotes: str | None = None
        self.noyoshi: bool = False
        self.asm: bool = False
        self.size: bool = False
        self.noLayer: bool = False
        self.dependencies: list[tuple[int, int]] = []
        self.dependencynotes: str | None = None
        self.fields: list[SpriteField] = []


    class ListPropertyModel(QtCore.QAbstractListModel):
        """
        Contains all the possible values for a list property on a sprite
        """

        def __init__(self, entries, hideVal=False):
            """
            Constructor
            """
            QtCore.QAbstractListModel.__init__(self)
            self.entries = entries
            self.hideVal = hideVal

        def rowCount(self, parent=None):
            """
            Required by Qt
            """
            return len(self.entries)

        def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
            """
            Get what we have for a specific row
            """
            if not index.isValid() or role != QtCore.Qt.ItemDataRole.DisplayRole:
                return None

            n = index.row()
            if not 0 <= n < len(self.entries):
                return None

            if self.hideVal:
                return '%s' % self.entries[n][1]
            else:
                return '%d: %s' % self.entries[n]


    def loadFrom(self, elem):
        """
        Loads in all the field data from an XML node
        """
        fields = self.fields
        allowed = ['checkbox', 'list', 'value', 'dualbox', 'dependency', 'external', 'multidualbox', 'spritetex']

        for field in elem:
            if field.tag not in allowed:
                continue

            attribs = field.attrib

            if field.tag == 'dualbox':
                title = attribs['title1'] + " / " + attribs['title2']
            elif field.tag == 'multidualbox':
                title = attribs['title1'] + " / " + attribs['title2']
            elif 'title' in attribs:
                title = attribs['title']
            else:
                title = globals_.trans.string('SpriteDataEditor', 28)

            advanced = attribs.get("advanced", "False") == "True"
            comment = comment2 = advancedcomment = required = idtype = None
            start = 0
            increment = 1

            if 'comment' in attribs:
                comment = globals_.trans.string('SpriteDataEditor', 1, '[name]', title, '[note]', attribs['comment'])

            if 'comment2' in attribs:
                comment2 = globals_.trans.string('SpriteDataEditor', 1, '[name]', title, '[note]', attribs['comment2'])

            if 'advancedcomment' in attribs:
                advancedcomment = globals_.trans.string('SpriteDataEditor', 1, '[name]', title, '[note]', attribs['advancedcomment'])

            if 'requirednybble' in attribs:
                bit_ranges, _ = self.parseBits(attribs.get("requirednybble"))
                required = []

                if 'requiredval' in attribs:
                    vals = attribs['requiredval'].split(",")

                    if len(bit_ranges) != len(vals):
                        raise ValueError("Required bits and vals have different lengths.")
                else:
                    vals = [None] * len(bit_ranges)

                # The associated values are a comma-separated list of values or
                # (inclusive) ranges.
                for bit_range, sval in zip(bit_ranges, vals):
                    if sval is None:
                        a = 1
                        b = (1 << (bit_range[1] - bit_range[0] + 1)) - 1
                    elif '-' not in sval:
                        a = b = int(sval)
                    else:
                        a, b = map(int, sval.split('-'))

                    required.append(((bit_range,), (a, b + 1)))

            # NOTE: idtype must be the LAST field passed to a sprite
            if 'idtype' in attribs:
                idtype = attribs['idtype']

                if field.tag not in {'value', 'list'}:
                    raise ValueError("Only values and lists support idtypes.")

            if 'start' in attribs:
                start = int(attribs['start'])

                if field.tag != 'value':
                    raise ValueError("Only values support a start index.")

            if 'increment' in attribs:
                increment = int(attribs['increment'])

                if field.tag != 'value':
                    raise ValueError("Only values support an increment.")

            # Parse the remaining type-specific attributes.
            # TODO: Make proper field classes in classlib.py instead of using tuples and relying on index 0 for the field type.
            if field.tag == 'checkbox':
                bit, _ = self.parseBits(attribs.get("nybble"))
                mask = int(attribs.get('mask', 1))
                fullNybble = attribs.get('fullnybble', 'False') == "True"

                fields.append(CheckBoxSpriteField(attribs['title'], comment, comment2, advancedcomment, required, bit, mask, fullNybble))

            elif field.tag == 'list':
                bit, _ = self.parseBits(attribs.get("nybble"))

                entries = []
                for e in field:
                    if e.tag != 'entry': continue

                    entries.append((int(e.attrib['value']), e.text))

                model = SpriteDefinition.ListPropertyModel(entries)
                fields.append(ListSpriteField(title, comment, comment2, advancedcomment, required, bit, model, idtype))

            elif field.tag == 'value':
                bit, max_ = self.parseBits(attribs.get("nybble"))

                overrides = []
                for o in field:
                    if o.tag != 'override': continue

                    overrides.append((int(o.attrib['index']), int(o.attrib['value'])))

                fields.append(ValueSpriteField(attribs['title'], comment, comment2, advancedcomment, required, bit, max_, start, increment, overrides, idtype))

            elif field.tag == 'dualbox':
                bit, _ = self.parseBits(attribs.get("nybble"))
                fullNybble = attribs.get('fullnybble', 'False') == "True"

                fields.append(DualBoxSpriteField(attribs['title1'], comment, comment2, advancedcomment, required, bit, attribs['title2'], fullNybble))

            elif field.tag == 'dependency':
                type_dict = {'required': 0, 'suggested': 1, 'resource': 2, 'suggestedresource': 3}

                for entry in field:
                    if entry.attrib['sprite'] == "":
                        continue

                    self.dependencies.append((int(entry.attrib['sprite']), type_dict[entry.tag]))

                self.dependencynotes = attribs.get('notes')

            elif field.tag == 'external':
                # Uses a list from an external resource. This is used for big
                # lists like actors, sound effects etc.
                bit, _ = self.parseBits(attribs.get("nybble"))
                type_ = attribs['type']

                fields.append(ExternalSpriteField(title, comment, comment2, advancedcomment, required, bit, type_))

            elif field.tag == 'multidualbox':
                # multibox but with dualboxes instead of checkboxes
                bit, _ = self.parseBits(attribs.get("nybble"))

                fields.append(MultiDualBoxSpriteField(attribs['title1'], comment, comment2, advancedcomment, required, bit, attribs['title2']))

            elif field.tag == 'spritetex':
                bit, max_ = self.parseBits(attribs.get("nybble"))

                entries = []
                for e in field:
                    if e.tag != 'entry': continue

                    entries.append((int(e.attrib['value']), e.text))

                model = SpriteDefinition.ListPropertyModel(entries)
                fields.append(SpriteTexSpriteField(title, comment, comment2, advancedcomment, required, bit, model, max_))

    def parseBits(self, nybble_val) -> tuple[list[tuple[int, int]], int]:
        """
        Parses a description of the bits a setting affects into a tuple of a
        list of ranges and the number of possible values. Ranges include the
        start and exclude the end. The most significant bit is considered 1.
        Precise bits can be specified by adding a period after the number,
        followed by a number from 1 to 4, where 1 is the most significant bit in
        a nybble, and 4 the least significant bit.

        Raises a ValueError if 'nybble_val' is None or if any of the specified
        ranges refer to bits that are not in the first 8 bytes.
        """
        if nybble_val is None:
            raise ValueError("No nybble specification given.")

        # The total number of bits that can be controlled.
        bit_length = 0
        # A list of tuples (start_bit, end_bit) that represent inclusive ranges.
        bit_ranges: list[tuple[int, int]] = []

        for range_ in nybble_val.split(","):
            if "-" in range_:
                # Multiple nybbles
                a, b = range_.split("-")
            else:
                # Just a nybble
                a = b = range_

            if "." in a:
                nybble, bits = map(int, a.split("."))
            else:
                nybble, bits = int(a), 1

            a = 4 * (nybble - 1) + bits

            if "." in b:
                nybble, bits = map(int, b.split("."))
            else:
                nybble, bits = int(b), 4

            b = 4 * (nybble - 1) + bits

            # Check if the resulting range would be valid.
            if not 1 <= a < b + 1 <= 65:
                raise ValueError("Indexed bits out of bounds: " + str(range_) + "->" + str((a, b + 1)))

            bit_length += b - a + 1
            bit_ranges.append((a, b + 1))

        return bit_ranges, 1 << bit_length


def LoadSpriteData():
    """
    Ensures that the sprite data info is loaded
    """
    errors = []
    errortext = []
    sprite_ids = [-1]

    # Convert the iterable to list, because we need to iterate over it twice
    paths = list(getResourcePaths('spritedata'))

    for path in paths:

        # Add XML sprite data, if there is any
        if not isinstance(path, str):
            path = path.path

        tree = ElementTree.parse(path)

        for sprite in tree.iter("sprite"):
            id_text = sprite.get("id")

            if id_text is None:
                continue

            id_ = int(id_text)
            sprite_ids.append(id_)

    globals_.NumSprites = max(sprite_ids) + 1
    globals_.Sprites = [SpriteDefinition()] * globals_.NumSprites

    for sdpath in paths:

        # Add XML sprite data, if there is any
        if sdpath in (None, ''):
            continue

        path = sdpath if isinstance(sdpath, str) else sdpath.path
        tree = ElementTree.parse(path)
        root = tree.getroot()

        for sprite in tree.iter("sprite"):

            try:
                spriteid = int(sprite.get("id"))
            except ValueError:
                continue

            spritename = sprite.get("name")
            notes = None
            advNotes = None
            relatedObjFiles = None
            yoshiNotes = None

            attribs = sprite.keys()

            if 'notes' in attribs:
                notes = globals_.trans.string('SpriteDataEditor', 2, '[notes]', sprite.get('notes'))

            if 'advancednotes' in attribs:
                advNotes = globals_.trans.string('SpriteDataEditor', 11, '[notes]', sprite.get('advancednotes'))

            if 'files' in attribs:
                relatedObjFiles = globals_.trans.string('SpriteDataEditor', 8, '[list]',
                                                sprite.get('files').replace(';', '<br>* '))

            if 'yoshinotes' in attribs:
                yoshiNotes = globals_.trans.string('SpriteDataEditor', 9, '[notes]',
                                                sprite.get('yoshinotes'))

            noyoshi = sprite.get('noyoshi', 'False') == "True"
            asm = sprite.get('asmhacks', 'False') == "True"
            size = sprite.get('sizehacks', 'False') == "True"
            noLayer = sprite.get('nolayer', 'False') == "True"

            sdef = SpriteDefinition()
            sdef.id = spriteid
            sdef.name = spritename
            sdef.notes = notes
            sdef.advNotes = advNotes
            sdef.relatedObjFiles = relatedObjFiles
            sdef.yoshiNotes = yoshiNotes
            sdef.noyoshi = noyoshi
            sdef.asm = asm
            sdef.size = size
            sdef.noLayer = noLayer
            sdef.dependencies = []
            sdef.dependencynotes = None

            try:
                sdef.loadFrom(sprite)
            except Exception as e:
                errors.append(str(spriteid))
                errortext.append(str(e))

            globals_.Sprites[spriteid] = sdef

    # Warn the user if errors occurred
    if errors:
        QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_BrokenSpriteData', 0),
                                      globals_.trans.string('Err_BrokenSpriteData', 1, '[sprites]', ', '.join(errors)),
                                      QtWidgets.QMessageBox.StandardButton.Ok)
        QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_BrokenSpriteData', 2), repr(errortext))


def LoadSpriteCategories(reload_=False):
    """
    Ensures that the sprite category info is loaded
    """
    if not globals_.SpriteCategories and not reload_: return

    paths = getResourcePaths('spritecategories')

    globals_.SpriteCategories = []
    # Add a Search category
    globals_.SpriteCategories.append(SpriteCategory(globals_.trans.string('Sprites', 19), [SpriteSubCategory(globals_.trans.string('Sprites', 16), list(range(globals_.NumSprites)))], []))
    globals_.SpriteCategories[0].sub_categories[0].sprite_ids.append(9999)  # 'no results' special case
    for path in paths:
        if path is None:
            continue
        tree = ElementTree.parse(path)
        root = tree.getroot()

        CurrentView: list[SpriteSubCategory] | None = None
        for view in root:
            if view.tag.lower() != 'view': continue

            viewname = view.attrib['name']

            # See if it's in there already
            CurrentView = []
            for potentialview in globals_.SpriteCategories:
                if potentialview.name == viewname:
                    CurrentView = potentialview.sub_categories
            if CurrentView == []: globals_.SpriteCategories.append(SpriteCategory(viewname, CurrentView, []))

            CurrentCategory = None
            for category in view:
                if category.tag.lower() != 'category': continue

                catname = category.attrib['name']

                # See if it's in there already
                CurrentCategory = []
                for potentialcat in CurrentView:
                    if potentialcat.name == catname: CurrentCategory = potentialcat.sprite_ids
                if CurrentCategory == []: CurrentView.append(SpriteSubCategory(catname, CurrentCategory))

                for attach in category:
                    if attach.tag.lower() != 'attach': continue

                    sprite = attach.attrib['sprite']
                    if '-' not in sprite:
                        if int(sprite) not in CurrentCategory:
                            CurrentCategory.append(int(sprite))
                    else:
                        x = sprite.split('-')
                        for i in range(int(x[0]), int(x[1]) + 1):
                            if i not in CurrentCategory:
                                CurrentCategory.append(i)


def LoadSpriteListData(reload_=False):
    """
    Ensures that the sprite list modifier data is loaded
    """
    if globals_.SpriteListData and not reload_: return

    paths = getResourcePaths('spritelistdata')

    globals_.SpriteListData = [[] for _ in range(24)]
    for path in paths:
        with open(path, 'r', encoding='utf-8') as f:
            data = f.read()

        split = data.replace('\n', '').split(';')
        for lineidx in range(24):
            line = split[lineidx]
            splitline = line.split(',')

            # Add them
            for item in splitline:
                try:
                    newitem = int(item)
                except ValueError:
                    continue
                if newitem in globals_.SpriteListData[lineidx]: continue
                globals_.SpriteListData[lineidx].append(newitem)
            globals_.SpriteListData[lineidx].sort()


def LoadEntranceNames(reload_=False):
    """
    Ensures that the entrance names are loaded
    """
    if globals_.EntranceTypeNames and not reload_: return

    paths = getResourcePaths('entrancetypes')

    names = collections.OrderedDict()
    for path in paths:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                id_, name = line.strip().split(':')
                names[int(id_)] = name

    globals_.EntranceTypeNames.clear()
    for idx in names:
        entrance_name = globals_.trans.string('EntranceDataEditor', 28, '[id]', idx, '[name]', names[idx])
        if not entrance_name:
            continue

        globals_.EntranceTypeNames[idx] = entrance_name


def LoadTilesetInfo(reload_=False):
    def parseRandom(
        node: ElementTree.Element, types: dict[str, dict[int, RandTileSelection]]
    ) -> dict[int, RandTileSelection]:
        """Parses all 'random' tags that are a child of the given node"""
        randoms: dict[int, RandTileSelection] = {}
        for type_ in node:
            # if this uses the 'name' attribute, insert the settings of the type
            # and go to the next child
            if 'name' in type_.attrib:
                name = type_.attrib['name']
                randoms.update(types[name])
                continue

            # [list | range] = input space
            if 'list' in type_.attrib:
                list_ = [int(s, 0) for s in type_.attrib['list'].split(",")]
            else:
                numbers = type_.attrib['range'].split(",")

                # inclusive range
                list_ = range(int(numbers[0], 0), int(numbers[1], 0) + 1)

            # values = output space [= [list | range] by default]
            if 'values' in type_.attrib:
                values = [int(s, 0) for s in type_.attrib['values'].split(",")]
            else:
                values = list(list_)[:]

            direction = 0
            if 'direction' in type_.attrib:
                direction_s = type_.attrib['direction']
                if direction_s in ['horizontal', 'both']:
                    direction |= 0b01
                if direction_s in ['vertical', 'both']:
                    direction |= 0b10
            else:
                direction = 0b11

            special = 0
            if 'special' in type_.attrib:
                special_s = type_.attrib['special']
                if special_s == 'double-top':
                    special = 0b01
                elif special_s == 'double-bottom':
                    special = 0b10

            for item in list_:
                randoms[item] = RandTileSelection(values, direction, special)

        return randoms

    if globals_.TilesetInfo and not reload_:
        return

    # Convert the iterable to list, because we need to iterate over it twice
    paths = list(getResourcePaths('tilesetinfo'))

    # go through the types
    types: dict[str, dict[int, RandTileSelection]] = {}
    for path in paths:
        tree = ElementTree.parse(path)
        root = tree.getroot()

        for node in root:
            if node.tag.lower() == "types":
                # read all types
                for type_ in node:
                    name = type_.attrib['name'].strip()
                    stuff = parseRandom(type_, types)
                    types[name] = stuff

        del tree
        del root

    # go through the groups
    groups: dict[str, dict[int, RandTileSelection]] = {}
    for path in paths:
        tree = ElementTree.parse(path)
        root = tree.getroot()

        for node in root:
            if node.tag.lower() == "group":
                randoms = parseRandom(node, types)

                for name in node.attrib['names'].split(","):
                    name = name.strip()
                    groups[name] = randoms

        del tree
        del root

    globals_.TilesetInfo = groups


def LoadMusicInfo(reload_=False):
    """
    Uses the current gamedef + translation to load the music data, and saves it
    in the MusicInfo global.
    """
    if globals_.MusicInfo and not reload_:
        return

    paths = getResourcePaths('music')

    songs = {}
    for path in paths:
        with open(path, 'r', encoding='utf-8') as musicfile:
            data = musicfile.read()

        del musicfile

        # Apply the data
        for line in data.split('\n'):
            line_items = line.strip().split(':')

            if len(line_items) != 2:
                # Ignore lines that do not follow the <songid>:<name> format
                continue

            songid, name = line_items
            songs[songid] = name

    globals_.MusicInfo = sorted(songs.items(), key=lambda kv: int(kv[0]))


class DiagnosticWidget(QtWidgets.QWidget):
    """
    Widget for the auto-diagnostic tool
    """
    def __init__(self):
        """
        Creates and initializes the widget
        """
        super().__init__()
        self.CheckFunctions = (('objects', globals_.trans.string('Diag', 1), DiagnosticToolDialog.UnusedTilesets, False),
               ('objects', globals_.trans.string('Diag', 2), DiagnosticToolDialog.ObjsInTileset, True),
               ('sprites', globals_.trans.string('Diag', 3), DiagnosticToolDialog.CrashSprites, False),
               ('sprites', globals_.trans.string('Diag', 4), DiagnosticToolDialog.CrashSpriteSettings, True),
               ('sprites', globals_.trans.string('Diag', 5), DiagnosticToolDialog.TooManySprites, False),
               ('entrances', globals_.trans.string('Diag', 6), DiagnosticToolDialog.DuplicateEntranceIDs, True),
               ('entrances', globals_.trans.string('Diag', 7), DiagnosticToolDialog.NoStartEntrance, True),
               ('entrances', globals_.trans.string('Diag', 8), DiagnosticToolDialog.EntranceTooCloseToZoneEdge, False),
               ('entrances', globals_.trans.string('Diag', 9), DiagnosticToolDialog.EntranceOutsideOfZone, False),
               ('zones', globals_.trans.string('Diag', 10), DiagnosticToolDialog.TooManyZones, True),
               ('zones', globals_.trans.string('Diag', 11), DiagnosticToolDialog.NoZones, True),
               ('zones', globals_.trans.string('Diag', 12), DiagnosticToolDialog.ZonesTooClose, True),
               ('zones', globals_.trans.string('Diag', 13), DiagnosticToolDialog.ZonesTooCloseToAreaEdges, True),
               ('zones', globals_.trans.string('Diag', 14), DiagnosticToolDialog.BiasNotEnabled, False),
               ('zones', globals_.trans.string('Diag', 15), DiagnosticToolDialog.ZonesTooBig, True),
               ('background', globals_.trans.string('Diag', 16), DiagnosticToolDialog.UnusedBackgrounds, False),
               )
        self.diagnosticIcon = QtWidgets.QPushButton()

        self.diagnosticIcon.setIcon(GetIcon('autodiagnosticgood'))
        self.diagnosticIcon.setFlat(True)
        self.diagnosticIcon.setGeometry(2, 1, 2, 1)
        # self.diagnosticIcon.setHeight(59)
        # self.diagnosticIcon.clicked.connect(ReggieWindow.HandleDiagnostics)
        self.diagnosticIcon.clicked.connect(self.findIssues)
        self.layout = QtWidgets.QGridLayout()
        self.layout.addWidget(self.diagnosticIcon, 0, 0)
        self.layout.setVerticalSpacing(0)
        self.layout.setHorizontalSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.starttimer = QtCore.QTimer()
        self.starttimer.setSingleShot(True)
        self.starttimer.timeout.connect(self.startloopytimer)
        self.starttimer.start(10000)

    def startloopytimer(self):
        self.loopytimer = QtCore.QTimer()
        self.loopytimer.timeout.connect(self.findIssues)
        self.loopytimer.start(50)

    def findIssues(self):
        try:
            dtd = DiagnosticToolDialog()
            issues = dtd.populateLists()

            print(issues)

        except:
            pass

    def populateLists(self):
        """
        Runs the check functions and adds items to the list if needed
        """
        self.buttonHandlers = []

        foundAnything = False
        foundCritical = False
        for ico, desc, fxn, isCritical in self.CheckFunctions:
            if False and fxn('c'):

                foundAnything = True
                if isCritical: foundCritical = True

                if isCritical:
                    self.diagnosticIcon.setIcon(GetIcon('autodiagnosticbad'))
                    print("THIS IS BAD")
                else:
                    self.diagnosticIcon.setIcon(GetIcon('autodiagnosticwarning'))
                    print("Warning!")
        if not foundAnything:
            self.diagnosticIcon.setIcon(GetIcon('autodiagnosticgood', True))
            print("'Sall cool!")

        '''if foundCritical: True, len(self.buttonHandlers)#   self.diagnosticIcon.setIcon(GetIcon('autodiagnosticbad'))
        elif foundAnything: False, len(self.buttonHandlers)   #self.diagnosticIcon.setIcon(GetIcon('autodiagnosticwarning'))
        return None, len(self.buttonHandlers)'''
        if foundCritical: return True, len(self.buttonHandlers)
        elif foundAnything: return False, len(self.buttonHandlers)
        return None, len(self.buttonHandlers)


class ZoomWidget(QtWidgets.QWidget):
    """
    Widget that allows easy zoom level control
    """

    def __init__(self):
        """
        Creates and initializes the widget
        """
        QtWidgets.QWidget.__init__(self)
        maxwidth = 512 - 128
        maxheight = 20

        self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.minLabel = QtWidgets.QPushButton()
        self.minusLabel = QtWidgets.QPushButton()
        self.plusLabel = QtWidgets.QPushButton()
        self.maxLabel = QtWidgets.QPushButton()

        self.slider.setMaximumHeight(maxheight)
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(globals_.mainWindow.ZoomLevels) - 1)
        self.slider.setTickInterval(2)
        self.slider.setTickPosition(self.slider.TickPosition.TicksAbove)
        self.slider.setPageStep(1)
        self.slider.setTracking(True)
        self.slider.setSliderPosition(self.findIndexOfLevel(100))
        self.slider.valueChanged.connect(self.sliderMoved)

        self.minLabel.setIcon(GetIcon('zoommin'))
        self.minusLabel.setIcon(GetIcon('zoomout'))
        self.plusLabel.setIcon(GetIcon('zoomin'))
        self.maxLabel.setIcon(GetIcon('zoommax'))
        self.minLabel.setFlat(True)
        self.minusLabel.setFlat(True)
        self.plusLabel.setFlat(True)
        self.maxLabel.setFlat(True)
        self.minLabel.clicked.connect(globals_.mainWindow.HandleZoomMin)
        self.minusLabel.clicked.connect(globals_.mainWindow.HandleZoomOut)
        self.plusLabel.clicked.connect(globals_.mainWindow.HandleZoomIn)
        self.maxLabel.clicked.connect(globals_.mainWindow.HandleZoomMax)

        self.layout = QtWidgets.QGridLayout()
        self.layout.addWidget(self.minLabel, 0, 0)
        self.layout.addWidget(self.minusLabel, 0, 1)
        self.layout.addWidget(self.slider, 0, 2)
        self.layout.addWidget(self.plusLabel, 0, 3)
        self.layout.addWidget(self.maxLabel, 0, 4)
        self.layout.setVerticalSpacing(0)
        self.layout.setHorizontalSpacing(0)
        self.layout.setContentsMargins(0, 0, 4, 0)

        self.setLayout(self.layout)
        self.setMinimumWidth(maxwidth)
        self.setMaximumWidth(maxwidth)
        self.setMaximumHeight(maxheight)

    def sliderMoved(self):
        """
        Handle the slider being moved
        """
        globals_.mainWindow.ZoomTo(globals_.mainWindow.ZoomLevels[self.slider.value()])

    def setZoomLevel(self, newLevel):
        """
        Moves the slider to the zoom level given
        """
        self.slider.setSliderPosition(self.findIndexOfLevel(newLevel))

    def findIndexOfLevel(self, level):
        for i, mainlevel in enumerate(globals_.mainWindow.ZoomLevels):
            if float(mainlevel) == float(level): return i


class ZoomStatusWidget(QtWidgets.QWidget):
    """
    Shows the current zoom level, in percent
    """

    def __init__(self):
        """
        Creates and initializes the widget
        """
        QtWidgets.QWidget.__init__(self)
        self.label = QtWidgets.QPushButton('100%')
        self.label.setFlat(True)
        self.label.clicked.connect(globals_.mainWindow.HandleZoomActual)

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.setContentsMargins(4, 0, 8, 0)
        self.setMaximumWidth(57)

        self.setLayout(self.layout)

    def setZoomLevel(self, zoomLevel):
        """
        Updates the widget
        """
        if float(int(zoomLevel)) == float(zoomLevel):
            self.label.setText(str(int(zoomLevel)) + '%')
        else:
            self.label.setText(str(float(zoomLevel)) + '%')


def LoadActionsLists():
    # Define the menu items, their default settings and their globals_.mainWindow.actions keys
    # These are used both in the Preferences Dialog and when init'ing the toolbar.

    globals_.FileActions = (
        MenuAction('newlevel', globals_.trans.string('MenuItems', 0), True),
        MenuAction('openfromname', globals_.trans.string('MenuItems', 2), True),
        MenuAction('openfromfile', globals_.trans.string('MenuItems', 4), False),
        MenuAction('openrecent', globals_.trans.string('MenuItems', 6), False),
        MenuAction('save', globals_.trans.string('MenuItems', 8), True),
        MenuAction('saveas', globals_.trans.string('MenuItems', 10), False),
        MenuAction('savecopyas', globals_.trans.string('MenuItems', 128), False),
        MenuAction('metainfo', globals_.trans.string('MenuItems', 12), False),
        MenuAction('changegamedef', globals_.trans.string('MenuItems', 98), False),
        MenuAction('screenshot', globals_.trans.string('MenuItems', 14), True),
        MenuAction('changegamepath', globals_.trans.string('MenuItems', 16), False),
        MenuAction('preferences', globals_.trans.string('MenuItems', 18), False),
        MenuAction('exit', globals_.trans.string('MenuItems', 20), False),
    )
    globals_.EditActions = (
        MenuAction('selectall', globals_.trans.string('MenuItems', 22), False),
        MenuAction('deselect', globals_.trans.string('MenuItems', 24), False),
        MenuAction('cut', globals_.trans.string('MenuItems', 26), True),
        MenuAction('copy', globals_.trans.string('MenuItems', 28), True),
        MenuAction('paste', globals_.trans.string('MenuItems', 30), True),
        MenuAction('shiftitems', globals_.trans.string('MenuItems', 32), False),
        MenuAction('mergelocations', globals_.trans.string('MenuItems', 34), False),
        MenuAction('diagnostic', globals_.trans.string('MenuItems', 36), False),
        MenuAction('freezeobjects', globals_.trans.string('MenuItems', 38), False),
        MenuAction('freezesprites', globals_.trans.string('MenuItems', 40), False),
        MenuAction('freezeentrances', globals_.trans.string('MenuItems', 42), False),
        MenuAction('freezelocations', globals_.trans.string('MenuItems', 44), False),
        MenuAction('freezepaths', globals_.trans.string('MenuItems', 46), False),
    )
    globals_.ViewActions = (
        MenuAction('showlay0', globals_.trans.string('MenuItems', 48), True),
        MenuAction('showlay1', globals_.trans.string('MenuItems', 50), True),
        MenuAction('showlay2', globals_.trans.string('MenuItems', 52), True),
        MenuAction('tileanim', globals_.trans.string('MenuItems', 108), False),
        MenuAction('collisions', globals_.trans.string('MenuItems', 110), False),
        MenuAction('realview', globals_.trans.string('MenuItems', 118), False),
        MenuAction('showsprites', globals_.trans.string('MenuItems', 54), True),
        MenuAction('showspriteimages', globals_.trans.string('MenuItems', 56), False),
        MenuAction('showentrances', globals_.trans.string('MenuItems', 144), False),
        MenuAction('showlocations', globals_.trans.string('MenuItems', 58), True),
        MenuAction('showpaths', globals_.trans.string('MenuItems', 130), True),
        MenuAction('grid', globals_.trans.string('MenuItems', 60), True),
        MenuAction('zoommax', globals_.trans.string('MenuItems', 62), True),
        MenuAction('zoomin', globals_.trans.string('MenuItems', 64), True),
        MenuAction('zoomactual', globals_.trans.string('MenuItems', 66), True),
        MenuAction('zoomout', globals_.trans.string('MenuItems', 68), True),
        MenuAction('zoommin', globals_.trans.string('MenuItems', 70), True),
    )
    globals_.SettingsActions = (
        MenuAction('areaoptions', globals_.trans.string('MenuItems', 72), True),
        MenuAction('camprofiles', globals_.trans.string('MenuItems', 140), False),
        MenuAction('zones', globals_.trans.string('MenuItems', 74), True),
        MenuAction('backgrounds', globals_.trans.string('MenuItems', 76), True),
        MenuAction('addarea', globals_.trans.string('MenuItems', 78), False),
        MenuAction('importarea', globals_.trans.string('MenuItems', 80), False),
        MenuAction('deletearea', globals_.trans.string('MenuItems', 82), False),
        MenuAction('reloadgfx', globals_.trans.string('MenuItems', 84), False),
        MenuAction('reloaddata', globals_.trans.string('MenuItems', 138), False),
    )
    globals_.HelpActions = (
        MenuAction('infobox', globals_.trans.string('MenuItems', 86), False),
        MenuAction('helpbox', globals_.trans.string('MenuItems', 88), False),
        MenuAction('tipbox', globals_.trans.string('MenuItems', 90), False),
        MenuAction('aboutqt', globals_.trans.string('MenuItems', 92), False),
    )


def LoadDefaultKeybinds():
    """
    Defines the default keybinds (and display strings) for each menu item
    """
    globals_.FileKeybinds = {
        # Identifier      # Key Sequence                          # Display String, used by Preferences
        'newlevel':       (QtGui.QKeySequence.StandardKey.New,    globals_.trans.string('MenuItems', 0)),
        'openfromname':   (QtGui.QKeySequence.StandardKey.Open,   globals_.trans.string('MenuItems', 2)),
        'openfromfile':   ('Ctrl+Shift+O',                        globals_.trans.string('MenuItems', 4)),
        'save':           (QtGui.QKeySequence.StandardKey.Save,   globals_.trans.string('MenuItems', 8)),
        'saveas':         (QtGui.QKeySequence.StandardKey.SaveAs, globals_.trans.string('MenuItems', 10)),
        'savecopyas':     (None,                                  globals_.trans.string('MenuItems', 128)),
        'metainfo':       ('Ctrl+Alt+I',                          globals_.trans.string('MenuItems', 12)),
        'screenshot':     ('Ctrl+Alt+S',                          globals_.trans.string('MenuItems', 14)),
        'changegamepath': ('Ctrl+Alt+G',                          globals_.trans.string('MenuItems', 16)),
        'preferences':    ('Ctrl+Alt+P',                          globals_.trans.string('MenuItems', 18)),
        'exit':           ('Ctrl+Q',                              globals_.trans.string('MenuItems', 20)),
    }
    globals_.EditKeybinds = {
        'selectall':           (QtGui.QKeySequence.StandardKey.SelectAll, globals_.trans.string('MenuItems', 22)),
        'deselect':            ('Ctrl+D',                                 globals_.trans.string('MenuItems', 24)),
        'undo':                (QtGui.QKeySequence.StandardKey.Undo,      globals_.trans.string('MenuItems', 124)),
        'redo':                (QtGui.QKeySequence.StandardKey.Redo,      globals_.trans.string('MenuItems', 126)),
        'cut':                 (QtGui.QKeySequence.StandardKey.Cut,       globals_.trans.string('MenuItems', 26)),
        'copy':                (QtGui.QKeySequence.StandardKey.Copy,      globals_.trans.string('MenuItems', 28)),
        'paste':               (QtGui.QKeySequence.StandardKey.Paste,     globals_.trans.string('MenuItems', 30)),
        'shiftitems':          ('Ctrl+Alt+Shift+S',                       globals_.trans.string('MenuItems', 32)),
        'mergelocations':      ('Ctrl+Shift+E',                           globals_.trans.string('MenuItems', 34)),
        'swapobjectstilesets': ('Ctrl+Shift+L',                           globals_.trans.string('MenuItems', 104)),
        'swapobjectstypes':    ('Ctrl+Shift+Y',                           globals_.trans.string('MenuItems', 106)),
        'switchsprites':       (None,                                     globals_.trans.string('MenuItems', 142)),
        'diagnostic':          ('Ctrl+Shift+D',                           globals_.trans.string('MenuItems', 36)),
        'freezeobjects':       ('Ctrl+Shift+1',                           globals_.trans.string('MenuItems', 38)),
        'freezesprites':       ('Ctrl+Shift+2',                           globals_.trans.string('MenuItems', 40)),
        'freezeentrances':     ('Ctrl+Shift+3',                           globals_.trans.string('MenuItems', 42)),
        'freezelocations':     ('Ctrl+Shift+4',                           globals_.trans.string('MenuItems', 44)),
        'freezepaths':         ('Ctrl+Shift+5',                           globals_.trans.string('MenuItems', 46)),
        'freezecomments':      ('Ctrl+Shift+9',                           globals_.trans.string('MenuItems', 114)),
    }
    globals_.ViewKeybinds = {
        'showlay0':         ('Ctrl+1',                               globals_.trans.string('MenuItems', 48)),
        'showlay1':         ('Ctrl+2',                               globals_.trans.string('MenuItems', 50)),
        'showlay2':         ('Ctrl+3',                               globals_.trans.string('MenuItems', 52)),
        'tileanim':         ('Ctrl+7',                               globals_.trans.string('MenuItems', 108)),
        'collisions':       ('Ctrl+8',                               globals_.trans.string('MenuItems', 110)),
        'realview':         ('Ctrl+9',                               globals_.trans.string('MenuItems', 118)),
        'showsprites':      ('Ctrl+4',                               globals_.trans.string('MenuItems', 54)),
        'showspriteimages': ('Ctrl+6',                               globals_.trans.string('MenuItems', 56)),
        'showentrances':    (None,                                   globals_.trans.string('MenuItems', 144)),
        'showlocations':    ('Ctrl+5',                               globals_.trans.string('MenuItems', 58)),
        'showcomments':     (None,                                   globals_.trans.string('MenuItems', 116)),
        'showpaths':        ('Ctrl+*',                               globals_.trans.string('MenuItems', 130)),
        'grid':             ('Ctrl+G',                               globals_.trans.string('MenuItems', 60)),
        'zoommax':          ('Ctrl+PgDown',                          globals_.trans.string('MenuItems', 62)),
        'zoomin':           (QtGui.QKeySequence.StandardKey.ZoomIn,  globals_.trans.string('MenuItems', 64)),
        'zoomactual':       ('Ctrl+0',                               globals_.trans.string('MenuItems', 66)),
        'zoomout':          (QtGui.QKeySequence.StandardKey.ZoomOut, globals_.trans.string('MenuItems', 68)),
        'zoommin':          ('Ctrl+PgUp',                            globals_.trans.string('MenuItems', 70)),
        'leveloverview':    ('Ctrl+M',                               globals_.trans.string('MenuItems', 94)),
        'palette':          ('Ctrl+P',                               globals_.trans.string('MenuItems', 96)),
        'toolbar':          ('Ctrl+T',                               globals_.trans.string('Menubar', 5)),
    }
    globals_.SettingsKeybinds = {
        'areaoptions': ('Ctrl+Alt+A',   globals_.trans.string('MenuItems', 72)),
        'zones':       ('Ctrl+Alt+Z',   globals_.trans.string('MenuItems', 74)),
        'backgrounds': ('Ctrl+Alt+B',   globals_.trans.string('MenuItems', 76)),
        'camprofiles': ('Ctrl+Alt+C',   globals_.trans.string('MenuItems', 140)),
        'addarea':     ('Ctrl+Alt+N',   globals_.trans.string('MenuItems', 78)),
        'importarea':  ('Ctrl+Alt+O',   globals_.trans.string('MenuItems', 80)),
        'deletearea':  ('Ctrl+Alt+D',   globals_.trans.string('MenuItems', 82)),
        'reloadgfx':   ('Ctrl+Shift+R', globals_.trans.string('MenuItems', 84)),
        'reloaddata':  (None,           globals_.trans.string('MenuItems', 138)),
    }
    globals_.HelpKeybinds = {
        'infobox': ('Ctrl+Shift+I', globals_.trans.string('MenuItems', 86)),
        'helpbox': ('Ctrl+Shift+H', globals_.trans.string('MenuItems', 88)),
        'tipbox':  ('Ctrl+Shift+T', globals_.trans.string('MenuItems', 90)),
        'aboutqt': ('Ctrl+Shift+Q', globals_.trans.string('MenuItems', 92)),
    }


def GetKeybind(name: str):
    """
    Returns a QKeySequence from the settings, or a default keybind
    """
    groups = [
        globals_.FileKeybinds,
        globals_.EditKeybinds,
        globals_.ViewKeybinds,
        globals_.SettingsKeybinds,
        globals_.HelpKeybinds,
    ]

    for g in groups:
        if name in g.keys():
            keySeq = setting('Keybind_' + name, g[name][0])
            return QtGui.QKeySequence(keySeq)

    print(f'GetKeybind(): Unknown identifier \'{name}\'!')
    return QtGui.QKeySequence(None)


def SetKeybind(name, sequence: QtGui.QKeySequence | None):
    """
    Saves a QKeySequence keybind to the settings, and updates the relevant menubar action
    """
    groups = [
        globals_.FileKeybinds,
        globals_.EditKeybinds,
        globals_.ViewKeybinds,
        globals_.SettingsKeybinds,
        globals_.HelpKeybinds,
    ]

    # Fix issues with items that have no default keybind
    if sequence is None:
        sequence = QtGui.QKeySequence()

    # Update the action keybind
    if globals_.mainWindow is not None:
        globals_.mainWindow.actions[name].setShortcut(sequence)

    # Check if the given keybind is identical to the default
    # If so, remove the keybind setting, no need to store it
    for g in groups:
        if name in g.keys() and QtGui.QKeySequence(g[name][0]) == sequence:
            delSetting('Keybind_' + name)
            return

    # Convert QKeySequence to string for storage
    key_str = sequence.toString()
    setSetting('Keybind_' + name, key_str)
