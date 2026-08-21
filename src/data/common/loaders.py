import collections
import itertools
import os
import struct
from xml.etree import ElementTree

from PyQt6 import QtCore, QtGui, QtWidgets

import globals_
import spritelib as SLib
from dirty import delSetting, setSetting, setting
from libs import lh, lib_versions, lz77, tpl
from src.data.common import archive
from src.data.common.keybind import Keybind
from src.data.common.menu_action import MenuAction
from src.data.level.sprite_definition import SpriteDefinition
from src.data.sprite.sprite_category import SpriteCategory, SpriteSubCategory
from src.data.tileset.object.object_def import ObjectDef
from src.data.tileset.object.renderers import IncrementTilesetFrame
from src.data.tileset.tile.rand_tile_selection import RandTileSelection
from src.data.tileset.tile.tileset_tile import TilesetTile
from src.data.tileset.tileset_category import TilesetCategory, TilesetFileEntry


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
    globals_.FileKeybinds = [
        Keybind(
            "newlevel",
            globals_.trans.string("MenuItems", 0),
            QtGui.QKeySequence.StandardKey.New,
        ),
        Keybind(
            "openfromname",
            globals_.trans.string("MenuItems", 2),
            QtGui.QKeySequence.StandardKey.Open,
        ),
        Keybind(
            "openfromfile",
            globals_.trans.string("MenuItems", 4),
            "Ctrl+Shift+O",
        ),
        Keybind(
            "save",
            globals_.trans.string("MenuItems", 8),
            QtGui.QKeySequence.StandardKey.Save,
        ),
        Keybind(
            "saveas",
            globals_.trans.string("MenuItems", 10),
            QtGui.QKeySequence.StandardKey.SaveAs,
        ),
        Keybind(
            "savecopyas",
            globals_.trans.string("MenuItems", 128),
            None,
        ),
        Keybind(
            "metainfo",
            globals_.trans.string("MenuItems", 12),
            "Ctrl+Alt+I",
        ),
        Keybind(
            "screenshot",
            globals_.trans.string("MenuItems", 14),
            "Ctrl+Alt+S",
        ),
        Keybind(
            "changegamepath",
            globals_.trans.string("MenuItems", 16),
            "Ctrl+Alt+G",
        ),
        Keybind(
            "preferences",
            globals_.trans.string("MenuItems", 18),
            "Ctrl+Alt+P",
        ),
        Keybind(
            "exit",
            globals_.trans.string("MenuItems", 20),
            "Ctrl+Q",
        ),
    ]
    globals_.EditKeybinds = [
        Keybind(
            "selectall",
            globals_.trans.string("MenuItems", 22),
            QtGui.QKeySequence.StandardKey.SelectAll,
        ),
        Keybind(
            "deselect",
            globals_.trans.string("MenuItems", 24),
            "Ctrl+D",
        ),
        Keybind(
            "undo",
            globals_.trans.string("MenuItems", 124),
            QtGui.QKeySequence.StandardKey.Undo,
        ),
        Keybind(
            "redo",
            globals_.trans.string("MenuItems", 126),
            QtGui.QKeySequence.StandardKey.Redo,
        ),
        Keybind(
            "cut",
            globals_.trans.string("MenuItems", 26),
            QtGui.QKeySequence.StandardKey.Cut,
        ),
        Keybind(
            "copy",
            globals_.trans.string("MenuItems", 28),
            QtGui.QKeySequence.StandardKey.Copy,
        ),
        Keybind(
            "paste",
            globals_.trans.string("MenuItems", 30),
            QtGui.QKeySequence.StandardKey.Paste,
        ),
        Keybind(
            "shiftitems",
            globals_.trans.string("MenuItems", 32),
            "Ctrl+Alt+Shift+S",
        ),
        Keybind(
            "mergelocations",
            globals_.trans.string("MenuItems", 34),
            "Ctrl+Shift+E",
        ),
        Keybind(
            "swapobjectstilesets",
            globals_.trans.string("MenuItems", 104),
            "Ctrl+Shift+L",
        ),
        Keybind(
            "swapobjectstypes",
            globals_.trans.string("MenuItems", 106),
            "Ctrl+Shift+Y",
        ),
        Keybind(
            "switchsprites",
            globals_.trans.string("MenuItems", 142),
            None,
        ),
        Keybind(
            "diagnostic",
            globals_.trans.string("MenuItems", 36),
            "Ctrl+Shift+D",
        ),
        Keybind(
            "freezeobjects",
            globals_.trans.string("MenuItems", 38),
            "Ctrl+Shift+1",
        ),
        Keybind(
            "freezesprites",
            globals_.trans.string("MenuItems", 40),
            "Ctrl+Shift+2",
        ),
        Keybind(
            "freezeentrances",
            globals_.trans.string("MenuItems", 42),
            "Ctrl+Shift+3",
        ),
        Keybind(
            "freezelocations",
            globals_.trans.string("MenuItems", 44),
            "Ctrl+Shift+4",
        ),
        Keybind(
            "freezepaths",
            globals_.trans.string("MenuItems", 46),
            "Ctrl+Shift+5",
        ),
        Keybind(
            "freezecomments",
            globals_.trans.string("MenuItems", 114),
            "Ctrl+Shift+9",
        ),
    ]
    globals_.ViewKeybinds = [
        Keybind("showlay0", globals_.trans.string("MenuItems", 48), "Ctrl+1"),
        Keybind("showlay1", globals_.trans.string("MenuItems", 50), "Ctrl+2"),
        Keybind("showlay2", globals_.trans.string("MenuItems", 52), "Ctrl+3"),
        Keybind("tileanim", globals_.trans.string("MenuItems", 108), "Ctrl+7"),
        Keybind("collisions", globals_.trans.string("MenuItems", 110), "Ctrl+8"),
        Keybind("realview", globals_.trans.string("MenuItems", 118), "Ctrl+9"),
        Keybind("showsprites", globals_.trans.string("MenuItems", 54), "Ctrl+4"),
        Keybind("showspriteimages", globals_.trans.string("MenuItems", 56), "Ctrl+6"),
        Keybind("showentrances", globals_.trans.string("MenuItems", 144), None),
        Keybind("showlocations", globals_.trans.string("MenuItems", 58), "Ctrl+5"),
        Keybind("showcomments", globals_.trans.string("MenuItems", 116), None),
        Keybind("showpaths", globals_.trans.string("MenuItems", 130), "Ctrl"),
        Keybind("grid", globals_.trans.string("MenuItems", 60), "Ctrl+G"),
        Keybind("zoommax", globals_.trans.string("MenuItems", 62), "Ctrl+PgDown"),
        Keybind(
            "zoomin",
            globals_.trans.string("MenuItems", 64),
            QtGui.QKeySequence.StandardKey.ZoomIn,
        ),
        Keybind("zoomactual", globals_.trans.string("MenuItems", 66), "Ctrl+0"),
        Keybind(
            "zoomout",
            globals_.trans.string("MenuItems", 68),
            QtGui.QKeySequence.StandardKey.ZoomOut,
        ),
        Keybind("zoommin", globals_.trans.string("MenuItems", 70), "Ctrl+PgUp"),
        Keybind("leveloverview", globals_.trans.string("MenuItems", 94), "Ctrl+M"),
        Keybind("palette", globals_.trans.string("MenuItems", 96), "Ctrl+P"),
        Keybind("toolbar", globals_.trans.string("Menubar", 5), "Ctrl+T"),
    ]
    globals_.SettingsKeybinds = [
        Keybind("areaoptions", globals_.trans.string("MenuItems", 72), "Ctrl+Alt+A"),
        Keybind("zones", globals_.trans.string("MenuItems", 74), "Ctrl+Alt+Z"),
        Keybind("backgrounds", globals_.trans.string("MenuItems", 76), "Ctrl+Alt+B"),
        Keybind("camprofiles", globals_.trans.string("MenuItems", 140), "Ctrl+Alt+C"),
        Keybind("addarea", globals_.trans.string("MenuItems", 78), "Ctrl+Alt+N"),
        Keybind("importarea", globals_.trans.string("MenuItems", 80), "Ctrl+Alt+O"),
        Keybind("deletearea", globals_.trans.string("MenuItems", 82), "Ctrl+Alt+D"),
        Keybind("reloadgfx", globals_.trans.string("MenuItems", 84), "Ctrl+Shift+R"),
        Keybind("reloaddata", globals_.trans.string("MenuItems", 138), None),
    ]
    globals_.HelpKeybinds = [
        Keybind("infobox", globals_.trans.string("MenuItems", 86), "Ctrl+Shift+I"),
        Keybind("helpbox", globals_.trans.string("MenuItems", 88), "Ctrl+Shift+H"),
        Keybind("tipbox", globals_.trans.string("MenuItems", 90), "Ctrl+Shift+T"),
        Keybind("aboutqt", globals_.trans.string("MenuItems", 92), "Ctrl+Shift+Q"),
    ]


def GetKeybind(name: str):
    """
    Returns a QKeySequence from the settings, or a default keybind
    """
    groups = (
        globals_.FileKeybinds
        + globals_.EditKeybinds
        + globals_.ViewKeybinds
        + globals_.SettingsKeybinds
        + globals_.HelpKeybinds
    )


    for g in groups:
        if g.id == name:
            keySeq = setting('Keybind_' + name, g.key_sequence)
            return QtGui.QKeySequence(keySeq)

    print(f'GetKeybind(): Unknown identifier \'{name}\'!')
    return QtGui.QKeySequence(None)


def SetKeybind(name, sequence: QtCore.QKeyCombination | QtGui.QKeySequence.StandardKey | str | None):
    """
    Saves a QKeySequence keybind to the settings, and updates the relevant menubar action
    """
    groups = (
        globals_.FileKeybinds
        + globals_.EditKeybinds
        + globals_.ViewKeybinds
        + globals_.SettingsKeybinds
        + globals_.HelpKeybinds
    )

    # Fix issues with items that have no default keybind
    if sequence is None:
        sequence = QtGui.QKeySequence()

    # Update the action keybind
    if globals_.mainWindow is not None:
        globals_.mainWindow.action_list[name].setShortcut(sequence)

    # Check if the given keybind is identical to the default
    # If so, remove the keybind setting, no need to store it
    for g in groups:
        if g.id == name and QtGui.QKeySequence(g.key_sequence) == sequence:
            delSetting('Keybind_' + name)
            return

    # Convert QKeySequence to string for storage
    key_str = sequence.toString()
    setSetting('Keybind_' + name, key_str)


def CreateTilesets():
    """
    Blank out the tileset arrays
    """
    globals_.Tiles = [None] * 0x200 * 4
    globals_.Tiles += globals_.Overrides
    globals_.TilesetFilesLoaded = [None, None, None, None]
    globals_.TilesetAnimTimer = QtCore.QTimer()
    globals_.TilesetAnimTimer.timeout.connect(IncrementTilesetFrame)
    globals_.TilesetAnimTimer.start(90)
    globals_.ObjectDefinitions = [None] * 4
    SLib.Tiles = globals_.Tiles


def LoadTileset(idx, name, reload_=False):
    """
    Load in a tileset into a specific slot
    """
    if not name:
        return False

    # find the tileset path
    tileset_paths = reversed(globals_.gamedef.GetTexturePaths())

    found = False
    compressed = False
    arcname = ''
    for path in tileset_paths:
        if path is None: break

        arcname = os.path.join(path, name + ".arc.LH")

        # Prioritise .arc.LH over regular .arc, just like Newer does.
        if os.path.isfile(arcname):
            compressed = True
            found = True
            break

        # Now check for LZ compression
        arcname = os.path.join(path, name + ".arc.LZ")
        if os.path.isfile(arcname):
            compressed = True
            found = True
            break

        # Strip away the suffix (check for no compression)
        arcname = os.path.splitext(arcname)[0]
        if os.path.isfile(arcname):
            compressed = False
            found = True
            break

    # Warning if not found
    if not found:
        QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_MissingTileset', 0),
                                      globals_.trans.string('Err_MissingTileset', 1, '[file]', name))
        return False

    # If this file's already loaded, return
    if globals_.TilesetFilesLoaded[idx] == arcname and not reload_: return

    # Get the data
    with open(arcname, 'rb') as fileobj:
        arcdata = fileobj.read()

    if compressed:
        if (arcdata[0] & 0xF0) == 0x40:  # If LH-compressed
            try:
                arcdata = lh.UncompressLH(arcdata)
            except IndexError:
                QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_Decompress', 0),
                                              globals_.trans.string('Err_Decompress', 1, '[file]', name))
                return False
        elif not arcdata.startswith(b"U\xAA8-"):  # If LZ-compressed
            try:
                arcdata = lz77.UncompressLZ77(arcdata)
            except IndexError:
                QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_Decompress', 0),
                                                globals_.trans.string('Err_Decompress', 2, '[file]', name))
                return False

    arc = archive.U8.load(arcdata)

    def exists(fn):
        nonlocal arc
        try:
            arc[fn]
        except:
            return False
        return True

    # Decompress the textures
    found = exists('BG_tex/%s_tex.bin.LZ' % name)
    found2 = exists('BG_chk/d_bgchk_%s.bin' % name)

    if found and found2:
        comptiledata = arc['BG_tex/%s_tex.bin.LZ' % name]
        colldata = bytes(arc['BG_chk/d_bgchk_%s.bin' % name])
    else:
        QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_CorruptedTilesetData', 0),
                                      globals_.trans.string('Err_CorruptedTilesetData', 1, '[file]', name))
        return False

    # Load in the textures
    img = LoadTexture_NSMBW(lz77.UncompressLZ77(comptiledata))

    # Divide it into individual tiles and
    # add collisions at the same time
    dest = QtGui.QPixmap.fromImage(img)
    sourcex = 4
    sourcey = 4
    tileoffset = idx * 256
    for i in range(tileoffset, tileoffset + 256):
        T = TilesetTile(dest.copy(sourcex, sourcey, 24, 24))
        T.setCollisions(struct.unpack_from('>8B', colldata, (i - tileoffset) * 8))
        globals_.Tiles[i] = T
        sourcex += 32
        if sourcex >= 1024:
            sourcex = 4
            sourcey += 32

    # Load the tileset animations, if there are any
    tileoffset = idx * 256
    row = 0
    col = 0

    containsConveyor = ['Pa1_toride', 'Pa1_toride_sabaku', 'Pa1_toride_kori', 'Pa1_toride_yogan', 'Pa1_toride_soto']

    isAnimated, prefix = CheckTilesetAnimated(arc)

    for i in range(tileoffset, tileoffset + 256):
        if idx == 0:
            if globals_.Tiles[i].collData[3] == 5:
                fn = 'BG_tex/hatena_anime.bin'
                found = exists(fn)

                if found:
                    globals_.Tiles[i].addAnimationData(arc[fn])

            elif globals_.Tiles[i].collData[3] == 0x10:
                fn = 'BG_tex/block_anime.bin'
                found = exists(fn)

                if found:
                    globals_.Tiles[i].addAnimationData(arc[fn])

            elif globals_.Tiles[i].collData[7] == 0x28:
                fn = 'BG_tex/tuka_coin_anime.bin'
                found = exists(fn)

                if found:
                    globals_.Tiles[i].addAnimationData(arc[fn])

        # TODO: Dehardcode this?
        elif idx == 1 and name in containsConveyor:
            for x in range(2):
                if i == 320+x*16:
                    fn = 'BG_tex/belt_conveyor_L_anime.bin'
                    found = exists(fn)

                    if found:
                        globals_.Tiles[i].addAnimationData(arc[fn], True)

                elif i == 321+x*16:
                    fn = 'BG_tex/belt_conveyor_M_anime.bin'
                    found = exists(fn)

                    if found:
                        globals_.Tiles[i].addAnimationData(arc[fn], True)

                elif i == 322+x*16:
                    fn = 'BG_tex/belt_conveyor_R_anime.bin'
                    found = exists(fn)

                    if found:
                        globals_.Tiles[i].addAnimationData(arc[fn], True)

                elif i == 323+x*16:
                    fn = 'BG_tex/belt_conveyor_L_anime.bin'
                    found = exists(fn)

                    if found:
                        globals_.Tiles[i].addAnimationData(arc[fn])

                elif i == 324+x*16:
                    fn = 'BG_tex/belt_conveyor_M_anime.bin'
                    found = exists(fn)

                    if found:
                        globals_.Tiles[i].addAnimationData(arc[fn])

                elif i == 325+x*16:
                    fn = 'BG_tex/belt_conveyor_R_anime.bin'
                    found = exists(fn)
                    if found:
                        globals_.Tiles[i].addAnimationData(arc[fn])

        # Setup Newer-style animated tiles
        if isAnimated:
            filenames = []
            filenames.append('%s_%d%s%s.bin' % (prefix, idx, hex(row)[2].lower(), hex(col)[2].lower()))
            filenames.append('%s_%d%s%s.bin' % (prefix, idx, hex(row)[2].upper(), hex(col)[2].upper()))

            if filenames[0] == filenames[1]:
                item = filenames[0]
                filenames = []
                filenames.append(item)

            for fn in filenames:
                fn = 'BG_tex/' + fn
                found = exists(fn)

                if found:
                    globals_.Tiles[i].addAnimationData(arc[fn])

        col += 1

        if col == 16:
            col = 0
            row += 1

    # Load the object definitions
    defs = [None] * 256

    indexfile = bytes(arc['BG_unt/%s_hd.bin' % name])
    deffile = arc['BG_unt/%s.bin' % name]
    objcount = len(indexfile) // 4
    indexstruct = struct.Struct('>HBB')

    for i in range(objcount):
        data = indexstruct.unpack_from(indexfile, i << 2)
        obj = ObjectDef()
        obj.width = data[1]
        obj.height = data[2]
        obj.load(deffile, data[0], tileoffset)
        defs[i] = obj

    globals_.ObjectDefinitions[idx] = defs

    ProcessOverrides(idx, name)

    # Keep track of this filepath
    globals_.TilesetFilesLoaded[idx] = arcname

    # Add Tiles to spritelib
    SLib.Tiles = globals_.Tiles

    return True


def LoadTexture_NSMBW(tiledata):
    data = tpl.decodeRGB4A3(tiledata, 1024, 256, False)

    # nsmblib returns the image data with premultiplied alpha, while the cython
    # and python implementations do not. As such, we have to set the correct
    # format for Qt - ARGB32 premultiplied if nsmblib is used, and ARGB32 by
    # default.
    if lib_versions["nsmblib"] is not None:
        data_format = QtGui.QImage.Format.Format_ARGB32_Premultiplied
    else:
        data_format = QtGui.QImage.Format.Format_ARGB32

    return QtGui.QImage(data, 1024, 256, 4096, data_format)


def UnloadTileset(idx):
    """
    Unload the tileset from a specific slot
    """
    tileoffset = idx * 256
    globals_.Tiles[tileoffset:tileoffset + 256] = [None] * 256
    globals_.ObjectDefinitions[idx] = [None] * 256
    globals_.TilesetFilesLoaded[idx] = None


def ProcessOverrides(idx, name):
    """
    Load overridden tiles if there are any
    """
    tsOffs = idx * 256

    if globals_.OverriddenTilesets is None:
        raise ValueError("Overridden tilesets not yet initialised")

    def overlay(base, overlay):
        img = QtGui.QPixmap(base.width(), base.height())
        img.fill(QtCore.Qt.GlobalColor.transparent)

        p = QtGui.QPainter(img)
        p.drawPixmap(0, 0, base)
        p.drawPixmap(0, 0, overlay)

        return img

    tsidx = globals_.OverriddenTilesets

    # Automatically apply the Pa0 override if the tileset name starts with 'Pa0_'
    # and the tileset is not excluded by setting 'override="no-Pa0"'
    if name in tsidx["Pa0"] or (name.startswith("Pa0_") and name not in tsidx["no-Pa0"]):
        defs = globals_.ObjectDefinitions[idx]
        t = globals_.Tiles

        # 0: invisibg

        ## Items:
        # 1:coin, 2:fire, 3:star, 4:stoi, 5:vine,
        # 6:spri, 7:mini, 8:prop, 9:ping, 10:yosh,
        # 11:ice, 12:10c, 13:1up,

        # Invisible blocks
        invisiblocks = (3, 4, 5, 6, 7, 8, 9, 10, 13)
        replacement = (1, 2, 3, 13, 5, 7, 8, 9, 11)

        # coin, fire, star, 1up, vine, mini, prop, ping, ice
        baseblock = globals_.Overrides_safe[0].main
        for i, replace in zip(invisiblocks, replacement):
            t[i].main = overlay(baseblock, globals_.Overrides_safe[replace].main)

        # Question and brick blocks
        # these don't have their own tiles so we have to do them by objects
        rangeA, rangeB = range(39, 49), range(27, 38)
        replace = 2048 + 10
        baseblock = t[defs[39].rows[0][0][1]].main

        # question blocks
        for i, a in zip(rangeA, range(2, 12)):
            t[replace].main = overlay(baseblock, globals_.Overrides_safe[a].main)
            defs[i].rows[0][0] = (0, replace, 0)
            replace += 1

        replace += 1
        baseblock = t[defs[26].rows[0][0][1]].main
        # brick block
        for i, a in zip(rangeB, (1, 12, 2, 3, 13, 5, 7, 8, 9, 10, 11)):
            t[replace].main = overlay(baseblock, globals_.Overrides_safe[a].main)
            defs[i].rows[0][0] = (0, replace, 0)
            replace += 1

        # now the extra stuff (invisible collisions etc)
        # @ row i, col j => globals_.Overrides[26 * i + j]

        t[1].main = globals_.Overrides[26 * 4].main        # solid
        t[2].main = globals_.Overrides[26 + 10].main       # vine stopper
        t[11].main = globals_.Overrides[26 * 3 + 13].main  # jumpthrough platform
        t[12].main = globals_.Overrides[26 * 3 + 12].main  # mini mario passageway

        t[16].main = globals_.Overrides[26 * 4 + 11].main  # 1x1 slope going up
        t[17].main = globals_.Overrides[26 * 4 + 12].main  # 1x1 slope going down
        t[18].main = globals_.Overrides[26 * 4 + 1].main   # 2x1 slope going up (part 1)
        t[19].main = globals_.Overrides[26 * 4 + 2].main   # 2x1 slope going up (part 2)
        t[20].main = globals_.Overrides[26 * 4 + 3].main   # 2x1 slope going down (part 1)
        t[21].main = globals_.Overrides[26 * 4 + 4].main   # 2x1 slope going down (part 2)
        t[22].main = globals_.Overrides[26 * 4 + 21].main  # 4x1 slope going up (part 1)
        t[23].main = globals_.Overrides[26 * 4 + 22].main  # 4x1 slope going up (part 2)
        t[24].main = globals_.Overrides[26 * 4 + 23].main  # 4x1 slope going up (part 3)
        t[25].main = globals_.Overrides[26 * 4 + 24].main  # 4x1 slope going up (part 4)
        t[26].main = globals_.Overrides[26 * 4 + 25].main  # 4x1 slope going down (part 1)
        t[27].main = globals_.Overrides[26 * 4 - 3].main   # 4x1 slope going down (part 2)
        t[28].main = globals_.Overrides[26 * 4 - 2].main   # 4x1 slope going down (part 3)
        t[29].main = globals_.Overrides[26 * 4 - 1].main   # 4x1 slope going down (part 4)
        t[30].main = globals_.Overrides[1].main            # coin

        t[32].main = globals_.Overrides[26 * 4 + 9].main   # 1x1 roof going down
        t[33].main = globals_.Overrides[26 * 4 + 10].main  # 1x1 roof going up
        t[34].main = globals_.Overrides[26 * 4 + 5].main   # 2x1 roof going down (part 1)
        t[35].main = globals_.Overrides[26 * 4 + 6].main   # 2x1 roof going down (part 2)
        t[36].main = globals_.Overrides[26 * 4 + 7].main   # 2x1 roof going up (part 1)
        t[37].main = globals_.Overrides[26 * 4 + 8].main   # 2x1 roof going up (part 2)
        t[38].main = globals_.Overrides[26 * 4 + 13].main  # 4x1 roof going down (part 1)
        t[39].main = globals_.Overrides[26 * 4 + 14].main  # 4x1 roof going down (part 2)
        t[40].main = globals_.Overrides[26 * 4 + 15].main  # 4x1 roof going down (part 3)
        t[41].main = globals_.Overrides[26 * 4 + 16].main  # 4x1 roof going down (part 4)
        t[42].main = globals_.Overrides[26 * 4 + 17].main  # 4x1 roof going up (part 1)
        t[43].main = globals_.Overrides[26 * 4 + 18].main  # 4x1 roof going up (part 2)
        t[44].main = globals_.Overrides[26 * 4 + 19].main  # 4x1 roof going up (part 3)
        t[45].main = globals_.Overrides[26 * 4 + 20].main  # 4x1 roof going up (part 4)
        t[46].main = globals_.Overrides[26 + 11].main      # P-switch coin

        t[53].main = globals_.Overrides[26 + 12].main      # donut lift
        t[61].main = globals_.Overrides[26 + 9].main       # multiplayer coin
        t[63].main = globals_.Overrides[26 * 2 + 13].main  # invisible damage tile

    if name in tsidx["Flowers"] or name in tsidx["Forest Flowers"]:
        # flowers
        t = globals_.Tiles
        t[tsOffs + 0xA0].main = globals_.Overrides_safe[26 + 4].main     # grass
        t[tsOffs + 0xA1].main = globals_.Overrides_safe[26 + 5].main
        t[tsOffs + 0xA2].main = globals_.Overrides[26 + 6].main
        t[tsOffs + 0xA3].main = globals_.Overrides[26 + 7].main
        t[tsOffs + 0xA4].main = globals_.Overrides[26 + 8].main

        if name in tsidx["Flowers"]:
            t[tsOffs + 0xB0].main = globals_.Overrides[26 * 2 + 9].main  # flowers
            t[tsOffs + 0xB1].main = globals_.Overrides[26 * 2 + 10].main
            t[tsOffs + 0xB2].main = globals_.Overrides[26 * 2 + 11].main

            t[tsOffs + 0xC0].main = globals_.Overrides[26 * 2 + 6].main  # flowers on grass
            t[tsOffs + 0xC1].main = globals_.Overrides[26 * 2 + 7].main
            t[tsOffs + 0xC2].main = globals_.Overrides[26 * 2 + 8].main
        elif name in tsidx["Forest Flowers"]:
            # forest flowers
            t[tsOffs + 0xB0].main = globals_.Overrides[26 * 3 + 9].main  # flowers
            t[tsOffs + 0xB1].main = globals_.Overrides[26 * 3 + 10].main
            t[tsOffs + 0xB2].main = globals_.Overrides[26 * 3 + 11].main

            t[tsOffs + 0xC0].main = globals_.Overrides[26 * 3 + 6].main  # flowers on grass
            t[tsOffs + 0xC1].main = globals_.Overrides[26 * 3 + 7].main
            t[tsOffs + 0xC2].main = globals_.Overrides[26 * 3 + 8].main

    if name in tsidx["Conveyors"]:
        # Conveyor belts
        t = globals_.Tiles
        tiles = [0x40, 0x41, 0x42, 0x43, 0x44, 0x45, # Right (slow), Right (fast)
                 0x50, 0x51, 0x52, 0x53, 0x54, 0x55] # Left  (slow), Left  (fast)

        for i, tileNum in enumerate(tiles):
            t[tsOffs + tileNum].main = overlay(t[tsOffs + tileNum].main, globals_.Overrides[26 * 5 + i].main)

    if name in tsidx["Lines"] or name in tsidx["Full Lines"]:
        # These are the line guides
        # normal lines have fewer though

        t = globals_.Tiles

        # use Overrides_safe here because the beginning of Overrides is overwritten
        t[tsOffs].main = globals_.Overrides_safe[26].main             # horizontal line
        t[tsOffs + 1].main = globals_.Overrides_safe[26 + 1].main     # vertical line
        t[tsOffs + 2].main = globals_.Overrides_safe[26 + 2].main     # bottom-right corner
        t[tsOffs + 3].main = globals_.Overrides_safe[26 + 3].main     # top-left corner

        t[tsOffs + 0x10].main = globals_.Overrides[26 * 2].main       # left red blob (part 1)
        t[tsOffs + 0x11].main = globals_.Overrides[26 * 2 + 1].main   # top red blob (part 1)
        t[tsOffs + 0x12].main = globals_.Overrides[26 * 2 + 2].main   # top red blob (part 2)
        t[tsOffs + 0x13].main = globals_.Overrides[26 * 2 + 3].main   # right red blob (part 1)
        t[tsOffs + 0x14].main = globals_.Overrides[26 * 2 + 4].main   # top-left red blob
        t[tsOffs + 0x15].main = globals_.Overrides[26 * 2 + 5].main   # top-right red blob

        t[tsOffs + 0x20].main = globals_.Overrides[26 * 3].main       # left red blob (part 2)
        t[tsOffs + 0x21].main = globals_.Overrides[26 * 3 + 1].main   # bottom red blob (part 1)
        t[tsOffs + 0x22].main = globals_.Overrides[26 * 3 + 2].main   # bottom red blob (part 2)
        t[tsOffs + 0x23].main = globals_.Overrides[26 * 3 + 3].main   # right red blob (part 2)
        t[tsOffs + 0x24].main = globals_.Overrides[26 * 3 + 4].main   # bottom-left red blob
        t[tsOffs + 0x25].main = globals_.Overrides[26 * 3 + 5].main   # bottom-right red blob

        # Those are all for normal lines
        if name in tsidx["Lines"]: return

        t[tsOffs + 0x30].main = globals_.Overrides_safe[14].main      # 1x2 diagonal going up (top edge)
        t[tsOffs + 0x31].main = globals_.Overrides_safe[15].main      # 1x2 diagonal going down (top edge)

        t[tsOffs + 0x40].main = globals_.Overrides[26 + 14].main      # 1x2 diagonal going up (part 1)
        t[tsOffs + 0x41].main = globals_.Overrides[26 + 15].main      # 1x2 diagonal going down (part 1)
        t[tsOffs + 0x42].main = globals_.Overrides[26 * 2 + 19].main  # 1x1 diagonal going up
        t[tsOffs + 0x43].main = globals_.Overrides[26 * 2 + 20].main  # 1x1 diagonal going down
        #t[tsOffs + 0x44].main = globals_.Overrides[ + 1058].main     # 2x1 diagonal going up (part 1) nothing
        t[tsOffs + 0x45].main = globals_.Overrides[20].main           # 2x1 diagonal going up (part 2)
        t[tsOffs + 0x46].main = globals_.Overrides_safe[21].main      # 2x1 diagonal going down (part 1)
        #t[tsOffs + 0x47].main = globals_.Overrides[ + 1061].main     # 2x1 diagonal going down (part 2) nothing

        t[tsOffs + 0x50].main = globals_.Overrides[26 * 2 + 14].main  # 1x2 diagonal going up (part 2)
        t[tsOffs + 0x51].main = globals_.Overrides[26 * 2 + 15].main  # 1x2 diagonal going down (part 2)
        t[tsOffs + 0x52].main = globals_.Overrides[26 * 3 + 14].main  # 1x1 diagonal going up
        t[tsOffs + 0x53].main = globals_.Overrides[26 * 3 + 15].main  # 1x1 diagonal going down
        t[tsOffs + 0x54].main = globals_.Overrides[26 + 19].main      # 2x1 diagonal going up (part 1)
        t[tsOffs + 0x55].main = globals_.Overrides[26 + 20].main      # 2x1 diagonal going up (part 2)
        t[tsOffs + 0x56].main = globals_.Overrides[26 + 21].main      # 2x1 diagonal going down (part 1)
        t[tsOffs + 0x57].main = globals_.Overrides[26 + 22].main      # 2x1 diagonal going down (part 2)

        t[tsOffs + 0x62].main = globals_.Overrides[26 * 3 + 17].main  # big circle piece 1st row
        t[tsOffs + 0x63].main = globals_.Overrides[26 * 3 + 18].main  # big circle piece 1st row
        t[tsOffs + 0x66].main = globals_.Overrides_safe[17].main      # medium circle piece 1st row
        t[tsOffs + 0x67].main = globals_.Overrides_safe[18].main      # medium circle piece 1st row

        t[tsOffs + 0x71].main = globals_.Overrides[26 * 3 + 20].main  # big circle piece 2nd row
        t[tsOffs + 0x72].main = globals_.Overrides_safe[23].main      # big circle piece 2nd row
        t[tsOffs + 0x73].main = globals_.Overrides_safe[24].main      # big circle piece 2nd row
        t[tsOffs + 0x74].main = globals_.Overrides_safe[25].main      # big circle piece 2nd row
        t[tsOffs + 0x75].main = globals_.Overrides[26 + 16].main      # medium circle piece 2nd row
        t[tsOffs + 0x76].main = globals_.Overrides[26 + 17].main      # medium circle piece 2nd row
        t[tsOffs + 0x77].main = globals_.Overrides[26 + 18].main      # medium circle piece 2nd row
        t[tsOffs + 0x78].main = globals_.Overrides[26 + 13].main      # small circle

        t[tsOffs + 0x80].main = globals_.Overrides[26 * 2 + 21].main  # big circle piece 3rd row
        t[tsOffs + 0x81].main = globals_.Overrides[26 * 2 + 22].main  # big circle piece 3rd row
        t[tsOffs + 0x84].main = globals_.Overrides[26 * 2 + 24].main  # big circle piece 3rd row
        t[tsOffs + 0x85].main = globals_.Overrides[26 * 2 + 16].main  # medium circle piece 3rd row
        t[tsOffs + 0x86].main = globals_.Overrides[26 * 2 + 17].main  # medium circle piece 3rd row
        t[tsOffs + 0x87].main = globals_.Overrides[26 * 2 + 18].main  # medium circle piece 3rd row

        t[tsOffs + 0x90].main = globals_.Overrides[26 * 3 + 21].main  # big circle piece 4th row
        t[tsOffs + 0x91].main = globals_.Overrides[26 * 3 + 22].main  # big circle piece 4th row
        t[tsOffs + 0x94].main = globals_.Overrides[26 * 2 + 25].main  # big circle piece 4th row

        t[tsOffs + 0xA1].main = globals_.Overrides[26 * 2 + 23].main  # big circle piece 5th row
        t[tsOffs + 0xA2].main = globals_.Overrides[26 + 23].main      # big circle piece 5th row
        t[tsOffs + 0xA3].main = globals_.Overrides[26 + 24].main      # big circle piece 5th row
        t[tsOffs + 0xA4].main = globals_.Overrides[26 + 25].main      # big circle piece 5th row

    elif name in tsidx["Minigame Lines"]:
        t = globals_.Tiles

        t[tsOffs + 0x40].main = globals_.Overrides_safe[26].main      # horizontal line
        t[tsOffs + 0x41].main = globals_.Overrides_safe[26 + 2].main  # bottom-right corner
        t[tsOffs + 0x42].main = globals_.Overrides_safe[26].main      # horizontal line

        t[tsOffs + 0x50].main = globals_.Overrides_safe[26 + 1].main  # vertical line
        t[tsOffs + 0x51].main = globals_.Overrides_safe[26 + 1].main  # vertical line
        t[tsOffs + 0x52].main = globals_.Overrides_safe[26 + 3].main  # top-left corner

        t[tsOffs + 0x43].main = globals_.Overrides[26 * 2].main       # left red blob (part 1)
        t[tsOffs + 0x44].main = globals_.Overrides[26 * 2 + 1].main   # top red blob (part 1)
        t[tsOffs + 0x45].main = globals_.Overrides[26 * 2 + 2].main   # top red blob (part 2)
        t[tsOffs + 0x46].main = globals_.Overrides[26 * 2 + 3].main   # right red blob (part 1)

        t[tsOffs + 0x53].main = globals_.Overrides[26 * 3].main       # left red blob (part 2)
        t[tsOffs + 0x54].main = globals_.Overrides[26 * 3 + 1].main   # bottom red blob (part 1)
        t[tsOffs + 0x55].main = globals_.Overrides[26 * 3 + 2].main   # bottom red blob (part 2)
        t[tsOffs + 0x56].main = globals_.Overrides[26 * 3 + 3].main   # right red blob (part 2)

        t[tsOffs + 0x62].main = globals_.Overrides[26 * 3 + 17].main  # big circle piece 1st row
        t[tsOffs + 0x63].main = globals_.Overrides[26 * 3 + 18].main  # big circle piece 1st row
        t[tsOffs + 0x66].main = globals_.Overrides_safe[17].main      # medium circle piece 1st row
        t[tsOffs + 0x67].main = globals_.Overrides_safe[18].main      # medium circle piece 1st row

        t[tsOffs + 0x71].main = globals_.Overrides[26 * 3 + 20].main  # big circle piece 2nd row
        t[tsOffs + 0x72].main = globals_.Overrides_safe[23].main      # big circle piece 2nd row
        t[tsOffs + 0x73].main = globals_.Overrides_safe[24].main      # big circle piece 2nd row
        t[tsOffs + 0x74].main = globals_.Overrides_safe[25].main      # big circle piece 2nd row
        t[tsOffs + 0x75].main = globals_.Overrides[26 + 16].main      # medium circle piece 2nd row
        t[tsOffs + 0x76].main = globals_.Overrides[26 + 17].main      # medium circle piece 2nd row
        t[tsOffs + 0x77].main = globals_.Overrides[26 + 18].main      # medium circle piece 2nd row

        t[tsOffs + 0x80].main = globals_.Overrides[26 * 2 + 21].main  # big circle piece 3rd row
        t[tsOffs + 0x81].main = globals_.Overrides[26 * 2 + 22].main  # big circle piece 3rd row
        t[tsOffs + 0x84].main = globals_.Overrides[26 * 2 + 24].main  # big circle piece 3rd row
        t[tsOffs + 0x85].main = globals_.Overrides[26 * 2 + 16].main  # medium circle piece 3rd row
        t[tsOffs + 0x86].main = globals_.Overrides[26 * 2 + 17].main  # medium circle piece 3rd row
        t[tsOffs + 0x87].main = globals_.Overrides[26 * 2 + 18].main  # medium circle piece 3rd row

        t[tsOffs + 0x90].main = globals_.Overrides[26 * 3 + 21].main  # big circle piece 4th row
        t[tsOffs + 0x91].main = globals_.Overrides[26 * 3 + 22].main  # big circle piece 4th row
        t[tsOffs + 0x94].main = globals_.Overrides[26 * 2 + 25].main  # big circle piece 4th row

        t[tsOffs + 0xA1].main = globals_.Overrides[26 * 2 + 23].main  # big circle piece 5th row
        t[tsOffs + 0xA2].main = globals_.Overrides[26 + 23].main      # big circle piece 5th row
        t[tsOffs + 0xA3].main = globals_.Overrides[26 + 24].main      # big circle piece 5th row
        t[tsOffs + 0xA4].main = globals_.Overrides[26 + 25].main      # big circle piece 5th row


def LoadOverrides():
    """
    Load overrides
    """
    globals_.Overrides = [None] * (6 * 26)
    globals_.Overrides_safe = [None] * (6 * 26)
    globals_.OVERRIDE_UNKNOWN = 2 * 26 + 12

    OverrideBitmap = QtGui.QPixmap(os.path.join('reggiedata', 'overrides.png'))
    idx = 0
    xcount = OverrideBitmap.width() // 24
    ycount = OverrideBitmap.height() // 24
    sourcex = 0
    sourcey = 0

    for y in range(ycount):
        for x in range(xcount):
            bmp = OverrideBitmap.copy(sourcex, sourcey, 24, 24)
            globals_.Overrides[idx] = TilesetTile(bmp)
            globals_.Overrides_safe[idx] = TilesetTile(bmp)

            # Set collisions if it's a brick or question
            if y <= 4:
                if 8 < x < 20:
                    globals_.Overrides[idx].setQuestionCollisions()
                    globals_.Overrides_safe[idx].setQuestionCollisions()
                elif 20 <= x < 32:
                    globals_.Overrides[idx].setBrickCollisions()
                    globals_.Overrides_safe[idx].setBrickCollisions()

            idx += 1
            sourcex += 24
        sourcex = 0
        sourcey += 24


def CheckTilesetAnimated(tileset):
    """Checks if a tileset contains Newer-style animations, and if so, returns
    (True, prefix) where prefix is the animation prefix. If not, (False, None).
    tileset should be a Wii.py U8 object."""
    # Find the animation files, if any
    excludes = (
        'block_anime.bin',
        'hatena_anime.bin',
        'tuka_coin_anime.bin',
    )
    texFiles = tileset['BG_tex']
    animFiles = []
    for f in texFiles:
        # Determine if it's likely an animation file
        if f.lower() in excludes: continue
        if f[-4:].lower() != '.bin': continue
        namelen = len(f)
        if namelen == 9:
            if f[1] != '_': continue
            if f[2] not in '0123': continue
            if f[3].lower() not in '0123456789abcdef': continue
            if f[4].lower() not in '0123456789abcdef': continue
        elif namelen == 10:
            if f[2] != '_': continue
            if f[3] not in '0123': continue
            if f[4].lower() not in '0123456789abcdef': continue
            if f[5].lower() not in '0123456789abcdef': continue
        animFiles.append(f)

    # Quit if there's no animation
    if not animFiles:
        return False, None
    else:
        # This makes so many assumptions
        fn = animFiles[0]
        prefix = fn[0] if len(fn) == 9 else fn[:2]
        return True, prefix
