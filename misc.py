from PyQt5 import QtCore, QtWidgets, QtGui
import collections
import sys
import os
from xml.etree import ElementTree

################################################################################
################################################################################
################################################################################

import globals_
from ui import GetIcon, ReggieTheme, toQColor, clipStr
from dirty import setting, setSetting
from dialogs import DiagnosticToolDialog
from translation import ReggieTranslation
from libs import lh
from misc2 import LevelViewWidget
from levelitems import Path, CommentItem

################################################################################
################################################################################
################################################################################

def GetPath(id_):
    """
    Checks the game definition and the translation and returns the appropriate path
    """
    # If there's a custom globals_.gamedef, use that
    if globals_.gamedef.custom and globals_.gamedef.file(id_) is not None:
        return globals_.gamedef.file(id_)
    else:
        return globals_.trans.path(id_)


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

    globals_.compressed = False

    if (data[0] & 0xF0) == 0x40 or not data.startswith(b"U\xAA8-"):  # If LH-compressed or LZ-compressed
        globals_.compressed = True
        return True

    return checkContent(data)


def FilesAreMissing():
    """
    Checks to see if any of the required files for Reggie are missing
    """

    if not os.path.isdir('reggiedata'):
        QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_MissingFiles', 0), globals_.trans.string('Err_MissingFiles', 1))
        return True

    required = ['icon.png', 'about.png', ]

    missing = []

    for check in required:
        if not os.path.isfile('reggiedata/' + check):
            missing.append(check)

    if missing:
        QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_MissingFiles', 0),
                                      globals_.trans.string('Err_MissingFiles', 2, '[files]', ', '.join(missing)))
        return True

    return False


def SetGamePaths(new_stage_path, new_texture_path):
    """
    Sets the NSMBWii game path
    """
    # os.path.join crashes if QStrings are used, so we must change the paths to
    # a Python string manually
    globals_.gamedef.SetStageGamePath(str(new_stage_path))
    globals_.gamedef.SetTextureGamePath(str(new_texture_path))


def areValidGamePaths(stage_check='ug', texture_check='ug'):
    """
    Checks to see if the path for NSMBWii contains a valid game
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

    # Check that a readable 01-01 file is located in the stage folder
    for ext in globals_.FileExtentions:
        if os.path.isfile(os.path.join(stage_check, "01-01" + ext)):
            return True

    return False

def LoadLevelNames():
    """
    Ensures that the level name info is loaded
    """
    # Parse the file
    tree = ElementTree.parse(GetPath('levelnames'))
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
    if (globals_.TilesetNames is not None) and (not reload_): return

    # Get paths
    paths = globals_.gamedef.recursiveFiles('tilesets')
    new = []
    new.append(globals_.trans.files['tilesets'])
    for path in paths: new.append(path)
    paths = new

    # Read each file
    globals_.TilesetNames = [[[], False], [[], False], [[], False], [[], False]]
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
            newlist = [LoadTilesetNames_Category(node), ]
            if 'sorted' in node.attrib:
                newlist.append(node.attrib['sorted'].lower() == 'true')
            else:
                newlist.append(globals_.TilesetNames[slot][1])  # inherit

            # Apply it as a patch over the current entry
            newlist[0] = CascadeTilesetNames_Category(globals_.TilesetNames[slot][0], newlist[0])

            # Sort it
            if not newlist[1]:
                newlist[0] = SortTilesetNames_Category(newlist[0])

            globals_.TilesetNames[slot] = newlist


def LoadTilesetNames_Category(node):
    """
    Loads a TilesetNames XML category
    """
    cat = []
    for child in node:
        if child.tag.lower() == 'category':
            new = [
                str(child.attrib['name']),
                LoadTilesetNames_Category(child),
            ]
            if 'sorted' in child.attrib:
                new.append(str(child.attrib['sorted'].lower()) == 'true')
            else:
                new.append(False)
            cat.append(new)
        elif child.tag.lower() == 'tileset':
            fname = str(child.attrib['filename'])
            cat.append((fname, str(child.attrib['name'])))

            # read override attribute
            if 'override' not in child.attrib:
                continue

            # override present, add it to the correct type
            type_ = str(child.attrib['override'])

            if type_ not in globals_.OverriddenTilesets:
                raise ValueError("Unknown override type '%s' for tileset '%s'" % (type_, fname))

            globals_.OverriddenTilesets[type_].add(fname)

    return list(cat)


def CascadeTilesetNames_Category(lower, upper):
    """
    Applies upper as a patch of lower
    """
    lower = list(lower)
    for item in upper:

        if isinstance(item[1], tuple) or isinstance(item[1], list):
            # It's a category

            found = False
            for i, lowitem in enumerate(lower):
                lowitem = lower[i]
                if lowitem[0] == item[0]:  # names are ==
                    lower[i] = list(lower[i])
                    lower[i][1] = CascadeTilesetNames_Category(lowitem[1], item[1])
                    found = True
                    break

            if not found:
                i = 0
                while (i < len(lower)) and (isinstance(lower[i][1], tuple) or isinstance(lower[i][1], list)): i += 1
                lower.insert(i + 1, item)

        else:  # It's a tileset entry
            found = False
            for i, lowitem in enumerate(lower):
                lowitem = lower[i]
                if lowitem[0] == item[0]:  # filenames are ==
                    lower[i] = list(lower[i])
                    lower[i][1] = item[1]
                    found = True
                    break

            if not found: lower.append(item)
    return lower


def SortTilesetNames_Category(cat):
    """
    Sorts a tileset names category
    """
    cat = list(cat)

    # First, remove all category nodes
    cats = []
    for node in cat:
        if isinstance(node[1], tuple) or isinstance(node[1], list):
            cats.append(node)
    for node in cats: cat.remove(node)

    # Sort the tileset names
    cat.sort(key=lambda entry: entry[1])

    # Sort the data within each category
    for i, cat_ in enumerate(cats):
        cats[i] = list(cat_)
        if not cats[i][2]: cats[i][1] = SortTilesetNames_Category(cats[i][1])

    # Put them back together
    new = []
    for category in cats: new.append(tuple(category))
    for tileset in cat: new.append(tuple(tileset))
    return tuple(new)


def LoadObjDescriptions(reload_=False):
    """
    Ensures that the object description is loaded
    """
    if (globals_.ObjDesc is not None) and not reload_: return

    paths, isPatch = globals_.gamedef.recursiveFiles('ts1_descriptions', True)
    if isPatch:
        new = []
        new.append(globals_.trans.files['ts1_descriptions'])
        for path in paths: new.append(path)
        paths = new

    globals_.ObjDesc = {}
    for path in paths:
        f = open(path)
        raw = [x.strip() for x in f.readlines()]
        f.close()

        for line in raw:
            w = line.split('=')
            globals_.ObjDesc[int(w[0])] = w[1]


def LoadBgANames(reload_=False):
    """
    Ensures that the background name info is loaded
    """
    if (globals_.BgANames is not None) and not reload_: return

    paths, isPatch = globals_.gamedef.recursiveFiles('bga', True)
    if isPatch:
        new = []
        new.append(globals_.trans.files['bga'])
        for path in paths: new.append(path)
        paths = new

    globals_.BgANames = []
    for path in paths:
        f = open(path)
        raw = [x.strip() for x in f.readlines()]
        f.close()

        for line in raw:
            w = line.split('=')

            found = False
            for check in globals_.BgANames:
                if check[0] == w[0]:
                    check[1] = w[1]
                    found = True

            if not found: globals_.BgANames.append([w[0], w[1]])

        globals_.BgANames = sorted(globals_.BgANames, key=lambda entry: int(entry[0], 16))


def LoadBgBNames(reload_=False):
    """
    Ensures that the background name info is loaded
    """
    if (globals_.BgBNames is not None) and not reload_: return

    paths, isPatch = globals_.gamedef.recursiveFiles('bgb', True)
    if isPatch:
        new = [globals_.trans.files['bgb']]
        for path in paths: new.append(path)
        paths = new

    globals_.BgBNames = []
    for path in paths:
        f = open(path)
        raw = [x.strip() for x in f.readlines()]
        f.close()

        for line in raw:
            w = line.split('=')

            found = False
            for check in globals_.BgBNames:
                if check[0] == w[0]:
                    check[1] = w[1]
                    found = True

            if not found: globals_.BgBNames.append([w[0], w[1]])

        globals_.BgBNames = sorted(globals_.BgBNames, key=lambda entry: int(entry[0], 16))


def LoadZoneThemes(reload_=False):
    """
    Ensures that custom zone themes get loaded
    """
    if (globals_.ZoneThemeValues is not None) and not reload_: return

    paths, isPatch = globals_.gamedef.recursiveFiles('zonethemes', True)

    globals_.ZoneThemeValues = []
    for path in paths:
        f = open(path)
        raw = [x.strip() for x in f.readlines()]
        f.close()

        globals_.ZoneThemeValues.extend(raw)

def LoadConstantLists():
    """
    Loads some lists of constants
    """
    globals_.BgScrollRateStrings = globals_.trans.stringList('BGDlg', 1)
    globals_.ZoneTerrainThemeValues = globals_.trans.stringList('ZonesDlg', 2)


class SpriteDefinition:
    """
    Stores and manages the data info for a specific sprite
    """

    class ListPropertyModel(QtCore.QAbstractListModel):
        """
        Contains all the possible values for a list property on a sprite
        """

        def __init__(self, entries):
            """
            Constructor
            """
            QtCore.QAbstractListModel.__init__(self)
            self.entries = entries

        def rowCount(self, parent=None):
            """
            Required by Qt
            """
            return len(self.entries)

        def data(self, index, role=QtCore.Qt.DisplayRole):
            """
            Get what we have for a specific row
            """
            if not index.isValid() or role != QtCore.Qt.DisplayRole:
                return None

            n = index.row()
            if not 0 <= n < len(self.entries):
                return None

            return '%d: %s' % self.entries[n]


    def loadFrom(self, elem):
        """
        Loads in all the field data from an XML node
        """
        self.fields = []
        fields = self.fields
        allowed = ['checkbox', 'list', 'value', 'bitfield', 'multibox', 'dualbox',
                   'dependency', 'external', 'multidualbox']

        for field in elem:
            if field.tag not in allowed:
                continue

            attribs = field.attrib

            if field.tag == 'dualbox':
                title = attribs['title1'] + " / " + attribs['title2']
            elif 'title' in attribs:
                title = attribs['title']
            else:
                title = "NO TITLE GIVEN!"

            advanced = attribs.get("advanced", "False") == "True"
            comment = comment2 = advancedcomment = required = idtype = None

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

            if 'idtype' in attribs:
                idtype = attribs['idtype']

                if field.tag not in {'value', 'list'}:
                    raise ValueError("Only values and lists support idtypes.")

            # Parse the remaining type-specific attributes.
            if field.tag == 'checkbox':
                bit, _ = self.parseBits(attribs.get("nybble"))
                mask = int(attribs.get('mask', 1))

                fields.append((0, attribs['title'], bit, mask, comment, required, advanced, comment2, advancedcomment))

            elif field.tag == 'list':
                bit, _ = self.parseBits(attribs.get("nybble"))

                entries = []
                for e in field:
                    if e.tag != 'entry': continue

                    entries.append((int(e.attrib['value']), e.text))

                model = SpriteDefinition.ListPropertyModel(entries)
                fields.append((1, title, bit, model, comment, required, advanced, comment2, advancedcomment, idtype))

            elif field.tag == 'value':
                bit, max_ = self.parseBits(attribs.get("nybble"))

                fields.append((2, attribs['title'], bit, max_, comment, required, advanced, comment2, advancedcomment, idtype))

            elif field.tag == 'bitfield':
                startbit = int(attribs['startbit'])
                bitnum = int(attribs['bitnum'])

                fields.append((3, attribs['title'], startbit, bitnum, comment, required, advanced, comment2, advancedcomment))

            elif field.tag == 'multibox':
                bit, _ = self.parseBits(attribs.get("nybble"))

                fields.append((4, attribs['title'], bit, comment, required, advanced, comment2, advancedcomment))

            elif field.tag == 'dualbox':
                bit, _ = self.parseBits(attribs.get("nybble"))

                fields.append((5, attribs['title1'], attribs['title2'], bit, comment, required, advanced, comment2, advancedcomment))

            elif field.tag == 'dependency':
                type_dict = {'required': 0, 'suggested': 1}

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

                fields.append((6, title, bit, comment, required, advanced, comment2, advancedcomment, type_))

            elif field.tag == 'multidualbox':
                # multibox but with dualboxes instead of checkboxes
                bit, _ = self.parseBits(attribs.get("nybble"))

                fields.append((7, attribs['title1'], attribs['title2'], bit, comment, required, advanced, comment2, advancedcomment))

    def parseBits(self, nybble_val):
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
        bit_ranges = []

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

    # It works this way so that it can overwrite settings based on order of precedence
    paths = [(globals_.trans.files['spritedata'], None)]
    for pathtuple in globals_.gamedef.multipleRecursiveFiles('spritedata', 'spritenames'):
        paths.append(pathtuple)

    for sdpath, snpath in paths:

        # Add XML sprite data, if there is any
        if sdpath not in (None, ''):
            path = sdpath if isinstance(sdpath, str) else sdpath.path
            tree = ElementTree.parse(path)

            for sprite in tree.iter("sprite"):
                id_text = sprite.get("id")

                try:
                    id_ = int(id_text)
                except ValueError:
                    continue

                sprite_ids.append(id_)

    globals_.NumSprites = max(sprite_ids) + 1
    globals_.Sprites = [None] * globals_.NumSprites

    for sdpath, snpath in paths:

        # Add XML sprite data, if there is any
        if sdpath not in (None, ''):
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
                                                   sprite.get('files').replace(';', '<br>'))

                if 'yoshinotes' in attribs:
                    yoshiNotes = globals_.trans.string('SpriteDataEditor', 9, '[notes]',
                                                   sprite.get('yoshinotes'))

                noyoshi = sprite.get('noyoshi', 'False') == "True"
                asm = sprite.get('asmhacks', 'False') == "True"
                size = sprite.get('sizehacks', 'False') == "True"

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
                sdef.dependencies = []
                sdef.dependencynotes = None

                try:
                    sdef.loadFrom(sprite)
                except Exception as e:
                    errors.append(str(spriteid))
                    errortext.append(str(e))

                globals_.Sprites[spriteid] = sdef

        # Add TXT sprite names, if there are any
        # This code is only ever run when a custom
        # gamedef is loaded, because spritenames.txt
        # is a file only ever used by custom gamedefs.
        if (snpath is not None) and (snpath.path is not None):
            with open(snpath.path) as snfile:
                data = snfile.read()

            # Split the data
            data = data.split('\n')
            for i, line in enumerate(data):
                data[i] = line.split(':')

            # Apply it
            for spriteid, name in data:
                spriteid = int(spriteid)

                if 0 <= spriteid < globals_.NumSprites:
                    globals_.Sprites[spriteid].name = name

    # Warn the user if errors occurred
    if errors:
        QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_BrokenSpriteData', 0),
                                      globals_.trans.string('Err_BrokenSpriteData', 1, '[sprites]', ', '.join(errors)),
                                      QtWidgets.QMessageBox.Ok)
        QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_BrokenSpriteData', 2), repr(errortext))


def LoadSpriteCategories(reload_=False):
    """
    Ensures that the sprite category info is loaded
    """
    if (globals_.SpriteCategories is not None) and not reload_: return

    paths, isPatch = globals_.gamedef.recursiveFiles('spritecategories', True)
    if isPatch:
        new = [globals_.trans.files['spritecategories']]
        for path in paths: new.append(path)
        paths = new

    globals_.SpriteCategories = []
    # Add a Search category
    globals_.SpriteCategories.append((globals_.trans.string('Sprites', 19), [(globals_.trans.string('Sprites', 16), list(range(globals_.NumSprites)))], []))
    globals_.SpriteCategories[-1][1][0][1].append(9999)  # 'no results' special case
    for path in paths:
        tree = ElementTree.parse(path)
        root = tree.getroot()

        CurrentView = None
        for view in root:
            if view.tag.lower() != 'view': continue

            viewname = view.attrib['name']

            # See if it's in there already
            CurrentView = []
            for potentialview in globals_.SpriteCategories:
                if potentialview[0] == viewname: CurrentView = potentialview[1]
            if CurrentView == []: globals_.SpriteCategories.append((viewname, CurrentView, []))

            CurrentCategory = None
            for category in view:
                if category.tag.lower() != 'category': continue

                catname = category.attrib['name']

                # See if it's in there already
                CurrentCategory = []
                for potentialcat in CurrentView:
                    if potentialcat[0] == catname: CurrentCategory = potentialcat[1]
                if CurrentCategory == []: CurrentView.append((catname, CurrentCategory))

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
    # global SpriteListData
    if (globals_.SpriteListData is not None) and not reload_: return

    paths = globals_.gamedef.recursiveFiles('spritelistdata')
    new = [os.path.join('reggiedata', 'spritelistdata.txt')]
    for path in paths: new.append(path)
    paths = new

    globals_.SpriteListData = [[] for _ in range(24)]
    for path in paths:
        with open(path) as f:
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
    if (globals_.EntranceTypeNames is not None) and not reload_: return

    paths, isPatch = globals_.gamedef.recursiveFiles('entrancetypes', True)
    if isPatch:
        paths = [globals_.trans.files['entrancetypes']] + paths

    names = collections.OrderedDict()
    for path in paths:
        with open(path, 'r') as f:
            for line in f.readlines():
                id_, name = line.strip().split(':')
                names[int(id_)] = name

    globals_.EntranceTypeNames = collections.OrderedDict()
    for idx in names:
        globals_.EntranceTypeNames[idx] = globals_.trans.string('EntranceDataEditor', 28, '[id]', idx, '[name]', names[idx])


def LoadTilesetInfo(reload_=False):
    def parseRandom(node, types):
        """Parses all 'random' tags that are a child of the given node"""
        randoms = {}
        for type_ in node:
            # if this uses the 'name' attribute, insert the settings of the type
            # and go to the next child
            if 'name' in type_.attrib:
                name = type_.attrib['name']
                randoms.update(types[name])
                continue

            # [list | range] = input space
            if 'list' in type_.attrib:
                list_ = list(map(lambda s: int(s, 0), type_.attrib['list'].split(",")))
            else:
                numbers = type_.attrib['range'].split(",")

                # inclusive range
                list_ = range(int(numbers[0], 0), int(numbers[1], 0) + 1)

            # values = output space [= [list | range] by default]
            if 'values' in type_.attrib:
                values = list(map(lambda s: int(s, 0), type_.attrib['values'].split(",")))
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
                randoms[item] = [values, direction, special]

        return randoms

    if (globals_.TilesetInfo is not None) and not reload_:
        return

    paths, isPatch = globals_.gamedef.recursiveFiles('tilesetinfo', True)
    if isPatch:
        new = [globals_.trans.files['tilesetinfo']]

        for path in paths:
            new.append(path)

        paths = new

    # go through the types
    types = {}
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
    info = {}
    for path in paths:
        tree = ElementTree.parse(path)
        root = tree.getroot()

        for node in root:
            if node.tag.lower() == "group":
                randoms = parseRandom(node, types)

                for name in node.attrib['names'].split(","):
                    name = name.strip()
                    info[name] = randoms

        del tree
        del root

    globals_.TilesetInfo = info


class ChooseLevelNameDialog(QtWidgets.QDialog):
    """
    Dialog which lets you choose a level from a list
    """

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle(globals_.trans.string('OpenFromNameDlg', 0))
        self.setWindowIcon(GetIcon('open'))
        LoadLevelNames()
        self.currentlevel = None

        # create the tree
        tree = QtWidgets.QTreeWidget()
        tree.setColumnCount(1)
        tree.setHeaderHidden(True)
        tree.setIndentation(16)
        tree.currentItemChanged.connect(self.HandleItemChange)
        tree.itemActivated.connect(self.HandleItemActivated)

        # add items (LevelNames is effectively a big category)
        tree.addTopLevelItems(self.ParseCategory(globals_.LevelNames))

        # assign it to self.leveltree
        self.leveltree = tree

        # create the buttons
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # create the layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.leveltree)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)
        self.layout = layout

        self.setMinimumWidth(320)  # big enough to fit "World 5: Freezeflame Volcano/Freezeflame Glacier"
        self.setMinimumHeight(384)

    def ParseCategory(self, items):
        """
        Parses a XML category
        """
        nodes = []
        for item in items:
            node = QtWidgets.QTreeWidgetItem()
            node.setText(0, item[0])
            # see if it's a category or a level
            if isinstance(item[1], str):
                # it's a level
                node.setData(0, QtCore.Qt.UserRole, item[1])
                node.setToolTip(0, item[1])
            else:
                # it's a category
                children = self.ParseCategory(item[1])
                for cnode in children:
                    node.addChild(cnode)
                node.setToolTip(0, item[0])
            nodes.append(node)
        return tuple(nodes)

    def HandleItemChange(self, current, previous):
        """
        Catch the selected level and enable/disable OK button as needed
        """
        self.currentlevel = current.data(0, QtCore.Qt.UserRole)
        if self.currentlevel is None:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        else:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
            self.currentlevel = str(self.currentlevel)

    def HandleItemActivated(self, item, column):
        """
        Handle a doubleclick on a level
        """
        self.currentlevel = item.data(0, QtCore.Qt.UserRole)
        if self.currentlevel is not None:
            self.currentlevel = str(self.currentlevel)
            self.accept()


class RecentFilesMenu(QtWidgets.QMenu):
    """
    A menu which displays recently opened files
    """
    def __init__(self):
        """
        Creates and initializes the menu
        """
        QtWidgets.QMenu.__init__(self)
        self.setMinimumWidth(192)

        # Here's how this works:
        # - Upon startup, RecentFiles is obtained from QSettings and put into self.FileList
        # - All modifications to the menu thereafter are then applied to self.FileList
        # - The actions displayed in the menu are determined by whatever's in self.FileList
        # - Whenever self.FileList is changed, self.writeSettings is called which writes
        #      it all back to the QSettings

        # Populate FileList upon startup
        if globals_.settings.contains('RecentFiles'):
            self.FileList = str(setting('RecentFiles')).split('|')

        else:
            self.FileList = ['']

        # This fixes bugs
        self.FileList = [path for path in self.FileList if path.lower() not in ('', 'none', 'false', 'true')]

        self.updateActionList()

    def writeSettings(self):
        """
        Writes FileList back to the Registry
        """
        setSetting('RecentFiles', str('|'.join(self.FileList)))

    def updateActionList(self):
        """
        Updates the actions visible in the menu
        """

        self.clear()  # removes any actions already in the menu
        ico = GetIcon('new')

        for i, filename in enumerate(self.FileList):
            filename = os.path.basename(filename)
            short = clipStr(filename, 72)
            if short is not None: filename = short + '...'

            act = QtWidgets.QAction(ico, filename, self)
            if i <= 9: act.setShortcut(QtGui.QKeySequence('Ctrl+Alt+%d' % i))
            act.setToolTip(str(self.FileList[i]))

            handler = self.HandleOpenRecentFile_(i)
            act.triggered.connect(handler)

            self.addAction(act)

    def AddToList(self, path):
        """
        Adds an entry to the list
        """
        MaxLength = 16
        path = str(path)

        if path in ('None', 'True', 'False'): return  # fixes bugs

        new = [path]
        for filename in self.FileList:
            if filename != path:
                new.append(filename)

        self.FileList = new[:MaxLength]
        self.writeSettings()
        self.updateActionList()

    def RemoveFromList(self, index):
        """
        Removes an entry from the list
        """
        del self.FileList[index]
        self.writeSettings()
        self.updateActionList()

    def clearAll(self):
        """
        Clears all recent files from the list and the registry
        """
        self.FileList = []
        self.writeSettings()
        self.updateActionList()

    def HandleOpenRecentFile_(self, i):
        return (lambda e: self.HandleOpenRecentFile(i))

    def HandleOpenRecentFile(self, number):
        """
        Open a recently opened level picked from the main menu
        """
        if globals_.mainWindow.CheckDirty(): return

        if not globals_.mainWindow.LoadLevel(self.FileList[number], True, 1): self.RemoveFromList(number)


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

        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.minLabel = QtWidgets.QPushButton()
        self.minusLabel = QtWidgets.QPushButton()
        self.plusLabel = QtWidgets.QPushButton()
        self.maxLabel = QtWidgets.QPushButton()

        self.slider.setMaximumHeight(maxheight)
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(globals_.mainWindow.ZoomLevels) - 1)
        self.slider.setTickInterval(2)
        self.slider.setTickPosition(self.slider.TicksAbove)
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
        self.setMaximumWidth(56)

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
        (globals_.trans.string('MenuItems', 0), True, 'newlevel'),
        (globals_.trans.string('MenuItems', 2), True, 'openfromname'),
        (globals_.trans.string('MenuItems', 4), False, 'openfromfile'),
        (globals_.trans.string('MenuItems', 6),  False, 'openrecent'),
        (globals_.trans.string('MenuItems', 8), True, 'save'),
        (globals_.trans.string('MenuItems', 10), False, 'saveas'),
        (globals_.trans.string('MenuItems', 128), False, 'savecopyas'),
        (globals_.trans.string('MenuItems', 12), False, 'metainfo'),
        (globals_.trans.string('MenuItems', 14), True, 'screenshot'),
        (globals_.trans.string('MenuItems', 16), False, 'changegamepath'),
        (globals_.trans.string('MenuItems', 18), False, 'preferences'),
        (globals_.trans.string('MenuItems', 20), False, 'exit'),
    )
    globals_.EditActions = (
        (globals_.trans.string('MenuItems', 22), False, 'selectall'),
        (globals_.trans.string('MenuItems', 24), False, 'deselect'),
        (globals_.trans.string('MenuItems', 26), True, 'cut'),
        (globals_.trans.string('MenuItems', 28), True, 'copy'),
        (globals_.trans.string('MenuItems', 30), True, 'paste'),
        (globals_.trans.string('MenuItems', 32), False, 'shiftitems'),
        (globals_.trans.string('MenuItems', 34), False, 'mergelocations'),
        (globals_.trans.string('MenuItems', 36), False, 'diagnostic'),
        (globals_.trans.string('MenuItems', 38), False, 'freezeobjects'),
        (globals_.trans.string('MenuItems', 40), False, 'freezesprites'),
        (globals_.trans.string('MenuItems', 42), False, 'freezeentrances'),
        (globals_.trans.string('MenuItems', 44), False, 'freezelocations'),
        (globals_.trans.string('MenuItems', 46), False, 'freezepaths'),
    )
    globals_.ViewActions = (
        (globals_.trans.string('MenuItems', 48), True, 'showlay0'),
        (globals_.trans.string('MenuItems', 50), True, 'showlay1'),
        (globals_.trans.string('MenuItems', 52), True, 'showlay2'),
        (globals_.trans.string('MenuItems', 54), True, 'showsprites'),
        (globals_.trans.string('MenuItems', 56), False, 'showspriteimages'),
        (globals_.trans.string('MenuItems', 58), True, 'showlocations'),
        (globals_.trans.string('MenuItems', 130), True, 'showpaths'),
        (globals_.trans.string('MenuItems', 60), True, 'grid'),
        (globals_.trans.string('MenuItems', 62), True, 'zoommax'),
        (globals_.trans.string('MenuItems', 64), True, 'zoomin'),
        (globals_.trans.string('MenuItems', 66), True, 'zoomactual'),
        (globals_.trans.string('MenuItems', 68), True, 'zoomout'),
        (globals_.trans.string('MenuItems', 70), True, 'zoommin'),
    )
    globals_.SettingsActions = (
        (globals_.trans.string('MenuItems', 72), True, 'areaoptions'),
        (globals_.trans.string('MenuItems', 74), True, 'zones'),
        (globals_.trans.string('MenuItems', 76), True, 'backgrounds'),
        (globals_.trans.string('MenuItems', 78), False, 'addarea'),
        (globals_.trans.string('MenuItems', 80), False, 'importarea'),
        (globals_.trans.string('MenuItems', 82), False, 'deletearea'),
        (globals_.trans.string('MenuItems', 84), False, 'reloadgfx'),
        (globals_.trans.string('MenuItems', 138), False, 'reloaddata'),
    )
    globals_.HelpActions = (
        (globals_.trans.string('MenuItems', 86), False, 'infobox'),
        (globals_.trans.string('MenuItems', 88), False, 'helpbox'),
        (globals_.trans.string('MenuItems', 90), False, 'tipbox'),
        (globals_.trans.string('MenuItems', 92), False, 'aboutqt'),
    )


class PreferencesDialog(QtWidgets.QDialog):
    """
    Dialog which lets you customize Reggie
    """

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle(globals_.trans.string('PrefsDlg', 0))
        self.setWindowIcon(GetIcon('settings'))

        # Create the tab widget
        self.tabWidget = QtWidgets.QTabWidget()
        self.tabWidget.currentChanged.connect(self.tabChanged)

        # Create other widgets
        self.infoLabel = QtWidgets.QLabel()
        self.generalTab = self.getGeneralTab()
        self.toolbarTab = self.getToolbarTab()
        self.themesTab = self.getThemesTab(QtWidgets.QWidget)()
        self.tabWidget.addTab(self.generalTab, globals_.trans.string('PrefsDlg', 1))
        self.tabWidget.addTab(self.toolbarTab, globals_.trans.string('PrefsDlg', 2))
        self.tabWidget.addTab(self.themesTab, globals_.trans.string('PrefsDlg', 3))

        # Create the buttonbox
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        # Create a main layout
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.infoLabel)
        mainLayout.addWidget(self.tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        # Update it
        self.tabChanged()

    def tabChanged(self):
        """
        Handles the current tab being changed
        """
        self.infoLabel.setText(self.tabWidget.currentWidget().info)

    def getGeneralTab(self):
        """
        Returns the General Tab
        """

        class GeneralTab(QtWidgets.QWidget):
            """
            General Tab
            """
            info = globals_.trans.string('PrefsDlg', 4)

            def __init__(self):
                """
                Initializes the General Tab
                """
                QtWidgets.QWidget.__init__(self)

                # Add the Clear Recent Files button
                ClearRecentBtn = QtWidgets.QPushButton(globals_.trans.string('PrefsDlg', 16))
                ClearRecentBtn.setMaximumWidth(ClearRecentBtn.minimumSizeHint().width())
                ClearRecentBtn.clicked.connect(self.ClearRecent)

                # Add the Translation Language setting
                self.Trans = QtWidgets.QComboBox()
                self.Trans.setMaximumWidth(256)

                # Add the Zone Entrance Indicator checkbox
                self.zEntIndicator = QtWidgets.QCheckBox(globals_.trans.string('PrefsDlg', 31))

                # Add the Zone Bounds Indicator checkbox
                self.zBndIndicator = QtWidgets.QCheckBox(globals_.trans.string('PrefsDlg', 38))

                # Reset data when hide checkbox
                self.rdhIndicator = QtWidgets.QCheckBox(globals_.trans.string('PrefsDlg', 33))

                # Hide reset spritedata button
                self.erbIndicator = QtWidgets.QCheckBox(globals_.trans.string('PrefsDlg', 34))

                # Enable padding button
                self.epbIndicator = QtWidgets.QCheckBox(globals_.trans.string('PrefsDlg', 35))
                self.epbIndicator.stateChanged.connect(
                    lambda v: self.psValue.setDisabled(v == 0)
                )

                # Padding size value
                self.psValue = QtWidgets.QSpinBox()
                self.psValue.setRange(0, 2147483647) # maximum value allowed by qt

                # Place objects at full size
                self.fullObjSize = QtWidgets.QCheckBox(globals_.trans.string('PrefsDlg', 37))

                self.insertPathNode = QtWidgets.QCheckBox("Insert new path node after selected node")

                # Create the main layout
                L = QtWidgets.QFormLayout()
                L.addRow(globals_.trans.string('PrefsDlg', 14), self.Trans)
                L.addRow(globals_.trans.string('PrefsDlg', 15), ClearRecentBtn)
                L.addWidget(self.epbIndicator)
                L.addRow(globals_.trans.string('PrefsDlg', 36), self.psValue)
                L.addWidget(self.zEntIndicator)
                L.addWidget(self.zBndIndicator)
                L.addWidget(self.rdhIndicator)
                L.addWidget(self.erbIndicator)
                L.addWidget(self.fullObjSize)
                L.addWidget(self.insertPathNode)
                self.setLayout(L)

                # Set the buttons
                self.Reset()

            def Reset(self):
                """
                Read the preferences and check the respective boxes
                """
                self.Trans.addItem('English')
                self.Trans.setItemData(0, None, QtCore.Qt.UserRole)
                self.Trans.setCurrentIndex(0)
                i = 1
                for trans in os.listdir('reggiedata/translations'):
                    if trans.lower() == 'english': continue

                    fp = 'reggiedata/translations/' + trans + '/main.xml'
                    if not os.path.isfile(fp): continue

                    transobj = ReggieTranslation(trans)
                    name = transobj.name
                    self.Trans.addItem(name)
                    self.Trans.setItemData(i, trans, QtCore.Qt.UserRole)
                    if trans == str(setting('Translation')):
                        self.Trans.setCurrentIndex(i)
                    i += 1

                self.zEntIndicator.setChecked(globals_.DrawEntIndicators)
                self.zBndIndicator.setChecked(globals_.BoundsDrawn)
                self.rdhIndicator.setChecked(globals_.ResetDataWhenHiding)
                self.erbIndicator.setChecked(globals_.HideResetSpritedata)

                self.epbIndicator.setChecked(globals_.EnablePadding)
                self.psValue.setEnabled(globals_.EnablePadding)
                self.psValue.setValue(globals_.PaddingLength)

                self.fullObjSize.setChecked(globals_.PlaceObjectsAtFullSize)
                self.insertPathNode.setChecked(globals_.InsertPathNode)

            def ClearRecent(self):
                """
                Handle the Clear Recent Files button being clicked
                """
                ans = QtWidgets.QMessageBox.question(None, globals_.trans.string('PrefsDlg', 17), globals_.trans.string('PrefsDlg', 18), QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
                if ans != QtWidgets.QMessageBox.Yes: return
                globals_.mainWindow.RecentMenu.clearAll()

        return GeneralTab()

    def getToolbarTab(self):
        """
        Returns the Toolbar Tab
        """

        class ToolbarTab(QtWidgets.QWidget):
            """
            Toolbar Tab
            """
            info = globals_.trans.string('PrefsDlg', 5)

            def __init__(self):
                """
                Initializes the Toolbar Tab
                """
                QtWidgets.QWidget.__init__(self)

                # Determine which keys are activated
                if setting('ToolbarActs') in (None, 'None', 'none', '', 0):
                    # Get the default settings
                    toggled = {}
                    for List in (globals_.FileActions, globals_.EditActions, globals_.ViewActions, globals_.SettingsActions, globals_.HelpActions):
                        for name, activated, key in List:
                            toggled[key] = activated
                else:
                    # Get the settings from the .ini
                    toggled = setting('ToolbarActs')
                    newToggled = {}  # here, I'm replacing QStrings w/ python strings
                    for key in toggled:
                        newToggled[str(key)] = toggled[key]
                    toggled = newToggled

                # Create some data
                self.FileBoxes = []
                self.EditBoxes = []
                self.ViewBoxes = []
                self.SettingsBoxes = []
                self.HelpBoxes = []
                FL = QtWidgets.QVBoxLayout()
                EL = QtWidgets.QVBoxLayout()
                VL = QtWidgets.QVBoxLayout()
                SL = QtWidgets.QVBoxLayout()
                HL = QtWidgets.QVBoxLayout()
                FB = QtWidgets.QGroupBox(globals_.trans.string('Menubar', 0))
                EB = QtWidgets.QGroupBox(globals_.trans.string('Menubar', 1))
                VB = QtWidgets.QGroupBox(globals_.trans.string('Menubar', 2))
                SB = QtWidgets.QGroupBox(globals_.trans.string('Menubar', 3))
                HB = QtWidgets.QGroupBox(globals_.trans.string('Menubar', 4))

                # Arrange this data so it can be iterated over
                menuItems = (
                    (globals_.FileActions, self.FileBoxes, FL, FB),
                    (globals_.EditActions, self.EditBoxes, EL, EB),
                    (globals_.ViewActions, self.ViewBoxes, VL, VB),
                    (globals_.SettingsActions, self.SettingsBoxes, SL, SB),
                    (globals_.HelpActions, self.HelpBoxes, HL, HB),
                )

                # Set up the menus by iterating over the above data
                for defaults, boxes, layout, group in menuItems:
                    for L, C, I in defaults:
                        box = QtWidgets.QCheckBox(L.replace('<br>', ' '))
                        boxes.append(box)
                        layout.addWidget(box)
                        try:
                            box.setChecked(toggled[I])
                        except KeyError:
                            pass
                        box.InternalName = I  # to save settings later
                    group.setLayout(layout)

                # Create the always-enabled Current Area checkbox
                CurrentArea = QtWidgets.QCheckBox(globals_.trans.string('PrefsDlg', 19))
                CurrentArea.setChecked(True)
                CurrentArea.setEnabled(False)

                # Create the Reset button
                reset = QtWidgets.QPushButton(globals_.trans.string('PrefsDlg', 20))
                reset.clicked.connect(self.reset)

                # Create the main layout
                L = QtWidgets.QGridLayout()
                L.addWidget(reset, 0, 0, 1, 1)
                L.addWidget(FB, 1, 0, 3, 1)
                L.addWidget(EB, 1, 1, 3, 1)
                L.addWidget(VB, 1, 2, 3, 1)
                L.addWidget(SB, 1, 3, 1, 1)
                L.addWidget(HB, 2, 3, 1, 1)
                L.addWidget(CurrentArea, 3, 3, 1, 1)
                self.setLayout(L)

            def reset(self):
                """
                This is called when the Reset button is clicked
                """
                items = (
                    (self.FileBoxes, globals_.FileActions),
                    (self.EditBoxes, globals_.EditActions),
                    (self.ViewBoxes, globals_.ViewActions),
                    (self.SettingsBoxes, globals_.SettingsActions),
                    (self.HelpBoxes, globals_.HelpActions)
                )

                for boxes, defaults in items:
                    for box, default in zip(boxes, defaults):
                        box.setChecked(default[1])

        return ToolbarTab()

    @staticmethod
    def getThemesTab(parent):
        """
        Returns the Themes Tab
        """

        class ThemesTab(parent):
            """
            Themes Tab
            """
            info = globals_.trans.string('PrefsDlg', 6)

            def __init__(self):
                """
                Initializes the Themes Tab
                """
                super().__init__()

                # Get the current and available themes
                self.themeID = globals_.theme.themeName
                self.themes = self.getAvailableThemes

                # Create the theme box
                self.themeBox = QtWidgets.QComboBox()
                for name, themeObj in self.themes:
                    self.themeBox.addItem(name)

                index = self.themeBox.findText(setting('Theme'), QtCore.Qt.MatchFixedString)
                if index >= 0:
                     self.themeBox.setCurrentIndex(index)

                self.themeBox.currentIndexChanged.connect(self.UpdatePreview)

                boxGB = QtWidgets.QGroupBox('Themes')
                L = QtWidgets.QFormLayout()
                L.addRow('Theme:', self.themeBox)
                L2 = QtWidgets.QGridLayout()
                L2.addLayout(L, 0, 0)
                boxGB.setLayout(L2)

                # Create the preview labels and groupbox
                self.preview = QtWidgets.QLabel()
                self.description = QtWidgets.QLabel()
                L = QtWidgets.QVBoxLayout()
                L.addWidget(self.preview)
                L.addWidget(self.description)
                L.addStretch(1)
                previewGB = QtWidgets.QGroupBox(globals_.trans.string('PrefsDlg', 22))
                previewGB.setLayout(L)

                # Create the options box options
                keys = QtWidgets.QStyleFactory().keys()
                self.NonWinStyle = QtWidgets.QComboBox()
                self.NonWinStyle.setToolTip(globals_.trans.string('PrefsDlg', 24))
                self.NonWinStyle.addItems(keys)
                ui_style = setting('uiStyle', "Fusion")

                if ui_style in keys:
                    self.NonWinStyle.setCurrentIndex(keys.index(ui_style))

                # Create the options groupbox
                L = QtWidgets.QVBoxLayout()
                L.addWidget(self.NonWinStyle)
                optionsGB = QtWidgets.QGroupBox(globals_.trans.string('PrefsDlg', 25))
                optionsGB.setLayout(L)

                # Create a main layout
                Layout = QtWidgets.QGridLayout()
                Layout.addWidget(boxGB, 0, 0)
                Layout.addWidget(optionsGB, 0, 1)
                Layout.addWidget(previewGB, 1, 1)
                Layout.setRowStretch(1, 1)
                self.setLayout(Layout)

                # Update the preview things
                self.UpdatePreview()

            @property
            def getAvailableThemes(self):
                """
                Searches the Themes folder and returns a list of theme filepaths.
                Automatically adds 'Classic' to the list.
                """
                theme_path = os.path.join('reggiedata', 'themes')
                theme_list = [('Classic', ReggieTheme())]
                for theme_name in os.listdir(theme_path):
                    if not os.path.isdir(os.path.join(theme_path, theme_name)):
                        continue

                    try:
                        theme = ReggieTheme(theme_name)
                    except Exception:
                        continue

                    theme_list.append((theme_name, theme))

                return tuple(theme_list)

            def UpdatePreview(self):
                """
                Updates the preview and theme box
                """
                for name, themeObj in self.themes:
                    if name == self.themeBox.currentText():
                        t = themeObj
                        self.preview.setPixmap(self.drawPreview(t))
                        text = globals_.trans.string('PrefsDlg', 26, '[name]', t.themeName, '[creator]', t.creator,
                                            '[description]', t.description)
                        self.description.setText(text)

            def drawPreview(self, theme):
                """
                Returns a preview pixmap for the given theme
                """

                scene = QtWidgets.QGraphicsScene(0, 0, 32 * 16, 17 * 16, self)
                old_theme, old_real_view = globals_.theme, globals_.RealViewEnabled
                globals_.theme = theme
                globals_.RealViewEnabled = False  # Disable so the zone looks 'plain'

                # Sprite [38] at (11, 4)
                sprite = globals_.mainWindow.CreateSprite(11 * 16, 4 * 16, 38, data=bytes(8), add_to_scene=False)
                scene.addItem(sprite)

                # Sprite [53] at (1, 6)
                sprite = globals_.mainWindow.CreateSprite(1 * 16, 6 * 16, 53, data=bytes(8), add_to_scene=False)
                scene.addItem(sprite)

                # Entrance [0] at (13, 8)
                ent = globals_.mainWindow.CreateEntrance(13 * 16, 8 * 16, 0, add_to_scene=False)

                # Location [1] at (1, 9) size (6, 2)
                loc = globals_.mainWindow.CreateLocation(1 * 16, 9 * 16, 6 * 16, 2 * 16, 1, add_to_scene=False)
                scene.addItem(loc)

                # Zone [1] at (8.5, 3.25) size (16, 7.5)
                zone = globals_.mainWindow.CreateZone(8.5 * 16, 3.25 * 16, 16 * 16, 7.5 * 16, id_=1, add_to_scene=False)
                scene.addItem(zone)

                # Path [1] making a rectangle shape between (13, 5) and (18, 9)
                path = Path(1, scene, loops=True)

                for x, y in ((13, 5), (18, 5), (18, 9), (13, 9)):
                    path.add_node(x * 16, y * 16)

                # Empty comment at (2, 3)
                comment = CommentItem(2 * 16, 3 * 16, "")
                scene.addItem(comment)

                # Take a screenshot
                px = QtGui.QPixmap(32 * 16, 17 * 16)
                px.fill(theme.color('bg'))

                rect = QtCore.QRectF(0, 0, 32 * 16, 17 * 16)

                painter = QtGui.QPainter(px)
                scene.render(painter, rect, rect)

                # Add grid
                temp_widget = LevelViewWidget(scene, None)
                temp_widget.drawForeground(painter, rect)

                painter.end()

                # Restore globals that were changed
                globals_.theme = old_theme
                globals_.RealViewEnabled = old_real_view

                return px

        return ThemesTab

