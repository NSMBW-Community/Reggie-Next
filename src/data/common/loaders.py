import collections
import itertools
import os
import struct
import sys
from xml.etree import ElementTree
from typing import TYPE_CHECKING

from PyQt6 import QtCore, QtGui, QtWidgets

import spritelib as SLib
from data import globals_
from data.common import archive
from data.common.gamedef_update import convert_txt_to_xml
from data.common.keybind import Keybind
from data.common.menu_action import MenuAction
from data.common.settings import delSetting, setSetting, setting
from data.common.toolbar_action import ToolbarAction
from data.common.utils import get_main_path, get_reggiedata_folder
from data.level.background_file import BackgroundFileEntry
from data.level.items.location import LocationItem
from data.level.sprite_definition import SpriteDefinition
from data.level.zone_theme import ZoneThemeEntry
from data.sprite.sprite_category import SpriteCategory, SpriteSubCategory
from data.tileset.object.object_def import ObjectDef
from data.tileset.object.renderers import IncrementTilesetFrame
from data.tileset.tile.rand_tile_selection import RandTileSelection
from data.tileset.tile.tile_def import TileDef
from data.tileset.tile.tileset_tile import TilesetTile
from data.tileset.tileset_category import TilesetCategory, TilesetFileEntry
from libs import lh, lib_versions, lz77, tpl
from data.common.translation import Translation
from ui.dialogs.about import AboutDialog
from ui.dialogs.diagnostic_tool import DiagnosticToolDialog
from ui.dialogs.object_swap import ObjectTypeSwapDialog
from ui.dialogs.sprite_switch import SpriteSwitchDialog
from ui.theme.reggie_theme import GetAppIcon, GetIcon, ReggieTheme

if TYPE_CHECKING:
    from ui.widgets.reggie_window import ReggieWindow

def getResourcePaths(res_name: str) -> list[str]:
    """
    Returns an iterable containing the paths that have the specified resource.
    The paths are included in order from general to specific. That is, the base
    comes before the patch.
    """
    # To make sure that the gamedef is translatable as well, we first need to
    # figure out what paths the gamedef loads its files from
    gamedef_files, _is_patch, gamedef_names = globals_.gamedef.recursiveFiles(res_name)

    # Then, we ask the current translation to give a path for each of those
    # gamedefs. If there is no translation for a specific resource and gamedef,
    # the corresponding entry will have the value 'None'.
    trans_files = globals_.trans.paths(res_name, gamedef_names)

    # Combine the gamedef_files and trans_files lists to get them in the right
    # order.
    #   [gamedef_files[0], trans_files[0], ..., gamedef[i], trans_files[i]]
    # If any entry (gamedef or translation) has no value, it will have None. As
    # such, we also need to filter out the None values from the final iterable.
    return [x for x in itertools.chain.from_iterable(zip(gamedef_files, trans_files)) if x is not None]


def LoadLevelNames() -> None:
    """
    Ensures that the level name info is loaded
    """
    for path in getResourcePaths('levelnames'):
        if path is None:
            continue

        tree = ElementTree.parse(path)
        root = tree.getroot()

        # Parse the nodes (root acts like a large category)
        globals_.LevelNames = LoadLevelNames_Category(root)


def LoadLevelNames_Category(node: ElementTree.Element) -> tuple[str, ...]:
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


def LoadTilesetNames(reload_: bool = False) -> None:
    """
    Ensures that the tileset name info is loaded
    """
    if not reload_: return

    # Get paths
    paths = getResourcePaths('tilesets')

    # Read each file
    globals_.TilesetNames = [TilesetCategory() for _ in range(4)]
    for path in paths:
        if path is None:
            continue

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
                    raise ValueError(f"Unknown override type '{type_}' for tileset '{fname}'")

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


def LoadObjDescriptions(reload_: bool = False) -> None:
    """
    Ensures that the object description is loaded
    """
    if globals_.ObjDesc and not reload_:
        return

    paths = getResourcePaths('ts1_descriptions')

    globals_.ObjDesc = {}
    for path in paths:
        # Check if a conversion needs to be done
        convert_txt_to_xml(path, '=', 'objects', 'object')

        if path is None:
            continue

        tree = ElementTree.parse(path)

        for node in tree.getroot():
            if node.tag.lower() == 'object':
                object_id = node.attrib['id']
                name = node.attrib['name']

                globals_.ObjDesc[int(object_id)] = name


def LoadBgFiles(reload_: bool = False) -> None:
    """
    Ensures that the background info is loaded
    """
    if globals_.BgAFiles and globals_.BgBFiles and not reload_:
        return

    globals_.BgAFiles = []
    globals_.BgBFiles = []

    res_name = ['bga', 'bgb']
    global_set = [globals_.BgAFiles, globals_.BgBFiles]

    # Needs to run twice for bgA and bgB
    for i in range(2):
        paths = getResourcePaths(res_name[i])

        for path in paths:
            # Before we begin, we might need to convert a txt file
            convert_txt_to_xml(path, '=', 'backgrounds', 'background')

            if path is None:
                continue

            tree = ElementTree.parse(path)

            for node in tree.getroot():
                if node.tag.lower() == 'background':
                    attribs = node.attrib

                    bg_id = attribs['id']
                    name = attribs['name']

                    if 'image' in attribs:
                        image = node.attrib['image']
                    else:
                        image = bg_id

                    background = BackgroundFileEntry(bg_id, name, image)

                    # Prevent adding duplicate BGs
                    exists = False
                    for file in global_set[i]:
                        # If two IDs repeat, override with the new data
                        if file.bg_id == background.bg_id:
                            file.name = background.name
                            file.image = background.image
                            exists = True

                    if not exists:
                        global_set[i].append(background)

            # Sort them by ID
            global_set[i].sort(key=lambda file: int(file.bg_id, 16))


def LoadZoneThemes(reload_: bool = False) -> None:
    """
    Ensures that custom zone themes get loaded
    """
    if globals_.ZoneThemes and not reload_:
        return

    paths = getResourcePaths('zonethemes')

    globals_.ZoneThemes = []

    for path in paths:
        # Before we begin, we might need to convert a txt file
        convert_txt_to_xml(path, '', 'themes', 'theme', False)

        if path is None:
            continue

        tree = ElementTree.parse(path)

        for node in tree.getroot():
            if node.tag.lower() == 'theme':
                attribs = node.attrib

                theme_id = attribs['id']
                name = attribs['name']
                desc = None

                if 'description' in attribs:
                    desc = node.attrib['description']

                new_theme = ZoneThemeEntry(theme_id, name, desc)

                # Avoid duplicates
                exists = False
                for theme in globals_.ZoneThemes:
                    # If two IDs repeat, override with the new data
                    if theme.idx == new_theme.idx:
                        theme.name = new_theme.name
                        theme.desc = new_theme.desc
                        exists = True

                if not exists:
                    globals_.ZoneThemes.append(new_theme)


def LoadConfig() -> None:
    """
    Ensures that gamedef-specific config info is loaded
    """
    for path in getResourcePaths('config'):
        if path is None:
            continue

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


def LoadSpriteData() -> None:
    """
    Ensures that the sprite data info is loaded
    """
    errors = []
    errortext = []
    sprite_ids = [-1]

    # Convert the iterable to list, because we need to iterate over it twice
    paths = list(getResourcePaths('spritedata'))

    for path in paths:
        if path is None:
            continue

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

        for sprite in tree.iter("sprite"):
            id_from_sprite = sprite.get("id")

            if id_from_sprite is None:
                continue

            spriteid = int(id_from_sprite)

            spritename = sprite.get("name")
            notes = None
            advNotes = None
            relatedObjFiles = None
            yoshiNotes = None

            attribs = sprite.keys()

            if 'notes' in attribs:
                notes = globals_.trans.string('dialog.sprite_data_editor.notes.text', ('[notes]', sprite.get('notes')))

            if 'advancednotes' in attribs:
                advNotes = globals_.trans.string('dialog.sprite_data_editor.advanced_notes.text', ('[notes]', sprite.get('advancednotes')))

            if 'files' in attribs:
                sprite_files = sprite.get('files')
                if sprite_files is None:
                    continue
                relatedObjFiles = globals_.trans.string('dialog.sprite_data_editor.object_files.text', ('[list]',
                    sprite_files.replace(';', '<br>* ')))

            if 'yoshinotes' in attribs:
                yoshiNotes = globals_.trans.string('dialog.sprite_data_editor.yoshi_notes.text', ('[notes]',
                    sprite.get('yoshinotes')))

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
            except ValueError as e:
                errors.append(str(spriteid))
                errortext.append(str(e))

            globals_.Sprites[spriteid] = sdef

    # Warn the user if errors occurred
    if errors:
        QtWidgets.QMessageBox.warning(None, globals_.trans.string('error.title.warning'),
                                      globals_.trans.string('error.broken_spritedata.description', ('[sprites]', ', '.join(errors))),
                                      QtWidgets.QMessageBox.StandardButton.Ok)
        QtWidgets.QMessageBox.warning(None, globals_.trans.string('error.title.error'), repr(errortext))


def ReloadSpritedata():
    """
    Reload the entire spritedata
    """
    LoadSpriteData()

    # Reload spritedata editor
    cur_sel_sprite = globals_.mainWindow.spriteDataEditor.spritetype
    globals_.mainWindow.spriteDataEditor.setSprite(cur_sel_sprite, True)

    # Update list
    globals_.mainWindow.palette_dock.sprite_tab.sprite_picker.UpdateSpriteNames()

    # Redo the search if a search was made
    search = globals_.mainWindow.palette_dock.sprite_tab.search_box.text()
    if search != "":
        globals_.mainWindow.palette_dock.sprite_tab.sprite_picker.SetSearchString(search)


def LoadSpriteCategories(reload_: bool = False) -> None:
    """
    Ensures that the sprite category info is loaded
    """
    if not globals_.SpriteCategories and not reload_:
        return

    paths = getResourcePaths('spritecategories')

    globals_.SpriteCategories = []
    # Add a Search category
    results_text = globals_.trans.string('palette.sprite.add.search_results')
    search_text = globals_.trans.string('common.search')

    globals_.SpriteCategories.append(SpriteCategory(search_text, [SpriteSubCategory(results_text, list(range(globals_.NumSprites)))], []))
    globals_.SpriteCategories[0].sub_categories[0].sprite_ids.append(9999)  # 'no results' special case
    for path in paths:
        if path is None:
            continue

        tree = ElementTree.parse(path)
        root = tree.getroot()

        CurrentView: list[SpriteSubCategory] | None = None
        for view in root:
            if view.tag.lower() != 'view':
                continue

            viewname = view.attrib['name']

            # See if it's in there already
            CurrentView = []
            for potentialview in globals_.SpriteCategories:
                if potentialview.name == viewname:
                    CurrentView = potentialview.sub_categories
            if CurrentView == []: globals_.SpriteCategories.append(SpriteCategory(viewname, CurrentView, []))

            CurrentCategory = None
            for category in view:
                if category.tag.lower() != 'category':
                    continue

                catname = category.attrib['name']

                # See if it's in there already
                CurrentCategory = []
                for potentialcat in CurrentView:
                    if potentialcat.name == catname: CurrentCategory = potentialcat.sprite_ids
                if CurrentCategory == []: CurrentView.append(SpriteSubCategory(catname, CurrentCategory))

                for attach in category:
                    if attach.tag.lower() != 'attach':
                        continue

                    sprite = attach.attrib['sprite']
                    if '-' not in sprite:
                        if int(sprite) not in CurrentCategory:
                            CurrentCategory.append(int(sprite))
                    else:
                        x = sprite.split('-')
                        for i in range(int(x[0]), int(x[1]) + 1):
                            if i not in CurrentCategory:
                                CurrentCategory.append(i)


def LoadEntranceNames(reload_: bool = False) -> None:
    """
    Ensures that the entrance names are loaded
    """
    if globals_.EntranceTypeNames and not reload_:
        return

    paths = getResourcePaths('entrancetypes')

    names = collections.OrderedDict()
    for path in paths:
        if path is None:
            continue

        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                id_, name = line.strip().split(':')
                names[int(id_)] = name

    globals_.EntranceTypeNames.clear()
    for idx in names:
        entrance_name = globals_.trans.string('dialog.entrance_data_editor.type_data', ('[id]', idx), ('[name]', names[idx]))
        if not entrance_name:
            continue

        globals_.EntranceTypeNames[idx] = entrance_name


def LoadTilesetInfo(reload_: bool = False) -> None:
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
        if path is None:
            continue

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
        if path is None:
            continue

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


def LoadMusicInfo(reload_: bool = False) -> None:
    """
    Uses the current gamedef + translation to load the music data, and saves it
    in the MusicInfo global.
    """
    if globals_.MusicInfo and not reload_:
        return

    paths = getResourcePaths('music')

    songs = {}
    for path in paths:
        # Check if we need to convert anything
        convert_txt_to_xml(path, ':', 'songs', 'song')

        if path is None:
            continue

        # Apply the data
        tree = ElementTree.parse(path)

        for node in tree.getroot():
            if node.tag.lower() == 'song':
                song_id = node.attrib['id']
                name = node.attrib['name']

                songs[song_id] = name

    globals_.MusicInfo = songs.items()

def LoadMenuActions(mw: "ReggieWindow") -> None:
    # TODO: Maybe make a proper Protocol type that has all methods from ReggieWindow which are referenced here
    # Define the global list of menu items, and their associated data
    # Some menu items are tied to docks or have special behavior, and thus are not defined here

    globals_.MenuActions = (
        MenuAction(
            'newlevel', mw.new_level, GetIcon('document'), globals_.trans.string_dict('menu_bar.file.item.new_level'), GetKeybind('newlevel')
        ),
        MenuAction(
            'openfromname', mw.open_from_name, GetIcon('folder-open-image'), globals_.trans.string_dict('menu_bar.file.item.open_by_name'), GetKeybind('openfromname')
        ),
        MenuAction(
            'openfromfile', mw.open_from_file, GetIcon('folder-open'), globals_.trans.string_dict('menu_bar.file.item.open_by_file'), GetKeybind('openfromfile')
        ),
        MenuAction(
            'openrecent', None, GetIcon('document-clock'), globals_.trans.string_dict('menu_bar.file.item.recent_files'), None
        ),
        MenuAction(
            'save', mw.save, GetIcon('disk-black'), globals_.trans.string_dict('menu_bar.file.item.save'), GetKeybind('save')
        ),
        MenuAction(
            'saveas', mw.save_as, GetIcon('disk-black-plus'), globals_.trans.string_dict('menu_bar.file.item.save_as'), GetKeybind('saveas')
        ),
        MenuAction(
            'savecopyas', lambda: mw.save_as(True), GetIcon('disks-black'), globals_.trans.string_dict('menu_bar.file.item.save_copy_as'), GetKeybind('savecopyas')
        ),
        MenuAction(
            'metainfo', mw.exec_meta_info, GetIcon('information-frame'), globals_.trans.string_dict('menu_bar.file.item.level_info'), GetKeybind('metainfo')
        ),
        MenuAction(
            'changegamedef', None, GetIcon('disc'), globals_.trans.string_dict('menu_bar.file.item.change_game_def'), None
        ),
        MenuAction(
            'screenshot', mw.exec_screenshots, GetIcon('camera'), globals_.trans.string_dict('menu_bar.file.item.screenshot'), GetKeybind('screenshot')
        ),
        MenuAction(
            'changegamepath', mw.change_game_path, GetIcon('folder--pencil'), globals_.trans.string_dict('menu_bar.file.item.change_game_path'), GetKeybind('changegamepath')
        ),
        MenuAction(
            'preferences', mw.exec_preferences, GetIcon('gear'), globals_.trans.string_dict('menu_bar.file.item.preferences'), GetKeybind('preferences')
        ),
        MenuAction(
            'exit', lambda: mw.close(), GetIcon('cross-circle-frame'), globals_.trans.string_dict('menu_bar.file.item.exit'), GetKeybind('exit')
        ),
        MenuAction(
            'selectall', mw.select_all, GetIcon('selection-select'), globals_.trans.string_dict('menu_bar.edit.item.select_all'), GetKeybind('selectall')
        ),
        MenuAction(
            'deselect', mw.deselect, GetIcon('selection'), globals_.trans.string_dict('menu_bar.edit.item.deselect'), GetKeybind('deselect')
        ),
        MenuAction(
            'undo', lambda: mw.undoStack.undo(), GetIcon('arrow-circle-225-left'), globals_.trans.string_dict('menu_bar.edit.item.undo'), GetKeybind('undo')
        ),
        MenuAction(
            'redo', lambda: mw.undoStack.redo(), GetIcon('arrow-circle-315'), globals_.trans.string_dict('menu_bar.edit.item.redo'), GetKeybind('redo')
        ),
        MenuAction(
            'cut', mw.cut, GetIcon('scissors-blue'), globals_.trans.string_dict('menu_bar.edit.item.cut'), GetKeybind('cut')
        ),
        MenuAction(
            'copy', mw.copy, GetIcon('document-copy'), globals_.trans.string_dict('menu_bar.edit.item.copy'), GetKeybind('copy')
        ),
        MenuAction(
            'paste', mw.paste, GetIcon('clipboard-paste-image'), globals_.trans.string_dict('menu_bar.edit.item.paste'), GetKeybind('paste')
        ),
        MenuAction(
            'shiftitems', mw.exec_item_shift, GetIcon('arrow-move'), globals_.trans.string_dict('menu_bar.edit.item.shift_items'), GetKeybind('shiftitems')
        ),
        MenuAction(
            'mergelocations', LocationItem.MergeLocations, GetIcon('layers-group'), globals_.trans.string_dict('menu_bar.edit.item.merge_locations'), GetKeybind('mergelocations')
        ),
        MenuAction(
            'swapobjectstilesets', mw.exec_tileset_swap, GetIcon('arrow-switch-block'), globals_.trans.string_dict('menu_bar.edit.item.swap_tilesets'), GetKeybind('swapobjectstilesets')
        ),
        MenuAction(
            'swapobjectstypes', lambda: ObjectTypeSwapDialog().exec(), GetIcon('arrow-switch-wooden-box'), globals_.trans.string_dict('menu_bar.edit.item.swap_objects'), GetKeybind('swapobjectstypes')
        ),
        MenuAction(
            'switchsprites', lambda: SpriteSwitchDialog().exec(), GetIcon('arrow-curve'), globals_.trans.string_dict('menu_bar.edit.item.switch_sprites'), GetKeybind('switchsprites')
        ),
        MenuAction(
            'diagnostic', lambda: DiagnosticToolDialog().exec(), GetIcon('wrench-screwdriver'), globals_.trans.string_dict('menu_bar.edit.item.diagnostic_tool'), GetKeybind('diagnostic')
        ),
        MenuAction(
            'freezeobjects', lambda _: globals_.Area.freeze_objects(_), GetIcon('block-freeze'), globals_.trans.string_dict('menu_bar.edit.item.freeze_objects'), GetKeybind('freezeobjects'), True
        ),
        MenuAction(
            'freezesprites', lambda _: globals_.Area.freeze_sprites(_), GetIcon('rocket-freeze'), globals_.trans.string_dict('menu_bar.edit.item.freeze_sprites'), GetKeybind('freezesprites'), True
        ),
        MenuAction(
            'freezeentrances', lambda _: globals_.Area.freeze_entrances(_), GetIcon('door-freeze'), globals_.trans.string_dict('menu_bar.edit.item.freeze_entrances'), GetKeybind('freezeentrances'), True
        ),
        MenuAction(
            'freezelocations', lambda _: globals_.Area.freeze_locations(_), GetIcon('layer-shape-purple-freeze'), globals_.trans.string_dict('menu_bar.edit.item.freeze_locations'), GetKeybind('freezelocations'), True
        ),
        MenuAction(
            'freezepaths', lambda _: globals_.Area.freeze_path_nodes(_), GetIcon('node-freeze'), globals_.trans.string_dict('menu_bar.edit.item.freeze_paths'), GetKeybind('freezepaths'), True
        ),
        MenuAction(
            'freezecomments', lambda _: globals_.Area.freeze_comments(_), GetIcon('balloon-freeze'), globals_.trans.string_dict('menu_bar.edit.item.freeze_comments'), GetKeybind('freezecomments'), True
        ),
        MenuAction(
            'showlay0', lambda _: globals_.Area.show_layer(0, _), GetIcon('layers-stack-number-0'), globals_.trans.string_dict('menu_bar.view.item.layer0'), GetKeybind('showlay0'), True
        ),
        MenuAction(
            'showlay1', lambda _: globals_.Area.show_layer(1, _), GetIcon('layers-stack-number-1'), globals_.trans.string_dict('menu_bar.view.item.layer1'), GetKeybind('showlay1'), True
        ),
        MenuAction(
            'showlay2', lambda _: globals_.Area.show_layer(2, _), GetIcon('layers-stack-number-2'), globals_.trans.string_dict('menu_bar.view.item.layer2'), GetKeybind('showlay2'), True
        ),
        MenuAction(
            'tileanim', mw.scene.play_tile_anim, GetIcon('film'), globals_.trans.string_dict('menu_bar.view.item.tile_animations'), GetKeybind('tileanim'), True
        ),
        MenuAction(
            'collisions', mw.scene.show_tile_collision, GetIcon('construction'), globals_.trans.string_dict('menu_bar.view.item.tile_collisions'), GetKeybind('collisions'), True
        ),
        MenuAction(
            'realview', mw.scene.show_real_view, GetIcon('eye'), globals_.trans.string_dict('menu_bar.view.item.real_view'), GetKeybind('realview'), True
        ),
        MenuAction(
            'showsprites', lambda _: globals_.Area.show_sprites(_), GetIcon('rocket'), globals_.trans.string_dict('menu_bar.view.item.sprites'), GetKeybind('showsprites'), True
        ),
        MenuAction(
            'showspriteimages', lambda _: globals_.Area.show_sprite_images(_), GetIcon('rocket-image'), globals_.trans.string_dict('menu_bar.view.item.sprite_images'), GetKeybind('showspriteimages'), True
        ),
        MenuAction(
            'showentrances', lambda _: globals_.Area.show_entrances(_), GetIcon('door'), globals_.trans.string_dict('menu_bar.view.item.entrances'), GetKeybind('showentrances'), True
        ),
        MenuAction(
            'showlocations', lambda _: globals_.Area.show_locations(_), GetIcon('layer-shape-purple'), globals_.trans.string_dict('menu_bar.view.item.locations'), GetKeybind('showlocations'), True
        ),
        MenuAction(
            'showcomments', lambda _: globals_.Area.show_comments(_), GetIcon('balloon'), globals_.trans.string_dict('menu_bar.view.item.comments'), GetKeybind('showcomments'), True
        ),
        MenuAction(
            'showpaths', lambda _: globals_.Area.show_path_nodes(_), GetIcon('node'), globals_.trans.string_dict('menu_bar.view.item.paths'), GetKeybind('showpaths'), True
        ),
        MenuAction(
            'grid', mw.scene.switch_grid, GetIcon('grid'), globals_.trans.string_dict('menu_bar.view.item.switch_grid'), GetKeybind('grid')
        ),
        MenuAction(
            'zoommax', mw.zoom_max, GetIcon('magnifier-zoom-maximum'), globals_.trans.string_dict('menu_bar.view.item.zoom_max'), GetKeybind('zoommax')
        ),
        MenuAction(
            'zoomin', mw.zoom_in, GetIcon('magnifier-zoom-in'), globals_.trans.string_dict('menu_bar.view.item.zoom_in'), GetKeybind('zoomin')
        ),
        MenuAction(
            'zoomactual', mw.zoom_default, GetIcon('magnifier-zoom-actual'), globals_.trans.string_dict('menu_bar.view.item.zoom_actual'), GetKeybind('zoomactual')
        ),
        MenuAction(
            'zoomout', mw.zoom_out, GetIcon('magnifier-zoom-out'), globals_.trans.string_dict('menu_bar.view.item.zoom_out'), GetKeybind('zoomout')
        ),
        MenuAction(
            'zoommin', mw.zoom_min, GetIcon('magnifier-zoom-minimum'), globals_.trans.string_dict('menu_bar.view.item.zoom_in'), GetKeybind('zoommin')
        ),
        MenuAction(
            'areaoptions', mw.exec_area_options, GetIcon('wooden-box'), globals_.trans.string_dict('menu_bar.settings.item.area_options'), GetKeybind('areaoptions')
        ),
        MenuAction(
            'zones', mw.exec_zones, GetIcon('zone'), globals_.trans.string_dict('menu_bar.settings.item.zone_settings'), GetKeybind('zones')
        ),
        MenuAction(
            'backgrounds', mw.exec_backgrounds, GetIcon('pictures'), globals_.trans.string_dict('menu_bar.settings.item.backgrounds'), GetKeybind('backgrounds')
        ),
        MenuAction(
            'camprofiles', mw.exec_camera_profiles, GetIcon('surveillance-camera'), globals_.trans.string_dict('menu_bar.settings.item.camera_profiles'), GetKeybind('camprofiles')
        ),
        MenuAction(
            'addarea', mw.add_new_area, GetIcon('wooden-box--plus'), globals_.trans.string_dict('menu_bar.settings.item.add_area'), GetKeybind('addarea')
        ),
        MenuAction(
            'importarea', mw.exec_area_import, GetIcon('wooden-box--arrow'), globals_.trans.string_dict('menu_bar.settings.item.import_area'), GetKeybind('importarea')
        ),
        MenuAction(
            'deletearea', mw.exec_area_delete, GetIcon('wooden-box--minus'), globals_.trans.string_dict('menu_bar.settings.item.delete_area'), GetKeybind('deletearea')
        ),
        MenuAction(
            'reloadgfx', ReloadTilesets, GetIcon('arrow-circle-double-135-block'), globals_.trans.string_dict('menu_bar.settings.item.reload_tilesets'), GetKeybind('reloadgfx')
        ),
        MenuAction(
            'reloaddata', ReloadSpritedata, GetIcon('arrow-circle-double-135-rocket'), globals_.trans.string_dict('menu_bar.settings.item.reload_spritedata'), GetKeybind('reloaddata')
        ),
        MenuAction(
            'infobox', lambda: AboutDialog().exec(), GetAppIcon(), globals_.trans.string_dict('menu_bar.help.item.about_reggie'), GetKeybind('infobox')
        ),
        MenuAction(
            'helpbox', mw.open_help_contents, GetIcon('book-open-bookmark'), globals_.trans.string_dict('menu_bar.help.item.help_contents'), GetKeybind('helpbox')
        ),
        MenuAction(
            'tipbox', mw.open_tips, GetIcon('light-bulb'), globals_.trans.string_dict('menu_bar.help.item.tips'), GetKeybind('tipbox')
        ),
        MenuAction(
            'aboutqt', lambda: QtWidgets.QMessageBox.aboutQt(None), GetIcon('qt'), globals_.trans.string_dict('menu_bar.help.item.about_qt'), GetKeybind('aboutqt')
        ),
    )


def LoadToolbarActionsLists() -> None:
    # Define the menu items present on the toolbar, their default settings and their globals_.mainWindow.actions keys
    # These are used both in the Preferences Dialog and when init'ing the toolbar.

    globals_.FileActions = (
        ToolbarAction('newlevel', globals_.trans.string('menu_bar.file.item.new_level.label'), True),
        ToolbarAction('openfromname', globals_.trans.string('menu_bar.file.item.open_by_name.label'), True),
        ToolbarAction('openfromfile', globals_.trans.string('menu_bar.file.item.open_by_file.label'), False),
        ToolbarAction('openrecent', globals_.trans.string('menu_bar.file.item.recent_files.label'), False),
        ToolbarAction('save', globals_.trans.string('menu_bar.file.item.save.label'), True),
        ToolbarAction('saveas', globals_.trans.string('menu_bar.file.item.save_as.label'), False),
        ToolbarAction('savecopyas', globals_.trans.string('menu_bar.file.item.save_copy_as.label'), False),
        ToolbarAction('metainfo', globals_.trans.string('menu_bar.file.item.level_info.label'), False),
        ToolbarAction('changegamedef', globals_.trans.string('menu_bar.file.item.change_game_def.label'), False),
        ToolbarAction('screenshot', globals_.trans.string('menu_bar.file.item.screenshot.label'), True),
        ToolbarAction('changegamepath', globals_.trans.string('menu_bar.file.item.change_game_path.label'), False),
        ToolbarAction('preferences', globals_.trans.string('menu_bar.file.item.preferences.label'), False),
        ToolbarAction('exit', globals_.trans.string('menu_bar.file.item.exit.label'), False),
    )
    globals_.EditActions = (
        ToolbarAction('selectall', globals_.trans.string('menu_bar.edit.item.select_all.label'), False),
        ToolbarAction('deselect', globals_.trans.string('menu_bar.edit.item.deselect.label'), False),
        ToolbarAction('cut', globals_.trans.string('menu_bar.edit.item.cut.label'), True),
        ToolbarAction('copy', globals_.trans.string('menu_bar.edit.item.copy.label'), True),
        ToolbarAction('paste', globals_.trans.string('menu_bar.edit.item.paste.label'), True),
        ToolbarAction('shiftitems', globals_.trans.string('menu_bar.edit.item.shift_items.label'), False),
        ToolbarAction('mergelocations', globals_.trans.string('menu_bar.edit.item.merge_locations.label'), False),
        ToolbarAction('swapobjectstilesets', globals_.trans.string('menu_bar.edit.item.swap_tilesets.label'), False),
        ToolbarAction('swapobjectstypes', globals_.trans.string('menu_bar.edit.item.swap_objects.label'), False),
        ToolbarAction('switchsprites', globals_.trans.string('menu_bar.edit.item.switch_sprites.label'), False),
        ToolbarAction('diagnostic', globals_.trans.string('menu_bar.edit.item.diagnostic_tool.label'), False),
        ToolbarAction('freezeobjects', globals_.trans.string('menu_bar.edit.item.freeze_objects.label'), False),
        ToolbarAction('freezesprites', globals_.trans.string('menu_bar.edit.item.freeze_sprites.label'), False),
        ToolbarAction('freezeentrances', globals_.trans.string('menu_bar.edit.item.freeze_entrances.label'), False),
        ToolbarAction('freezelocations', globals_.trans.string('menu_bar.edit.item.freeze_locations.label'), False),
        ToolbarAction('freezepaths', globals_.trans.string('menu_bar.edit.item.freeze_paths.label'), False),
    )
    globals_.ViewActions = (
        ToolbarAction('showlay0', globals_.trans.string('menu_bar.view.item.layer0.label'), True),
        ToolbarAction('showlay1', globals_.trans.string('menu_bar.view.item.layer1.label'), True),
        ToolbarAction('showlay2', globals_.trans.string('menu_bar.view.item.layer2.label'), True),
        ToolbarAction('tileanim', globals_.trans.string('menu_bar.view.item.tile_animations.label'), False),
        ToolbarAction('collisions', globals_.trans.string('menu_bar.view.item.tile_collisions.label'), False),
        ToolbarAction('realview', globals_.trans.string('menu_bar.view.item.real_view.label'), False),
        ToolbarAction('showsprites', globals_.trans.string('menu_bar.view.item.sprites.label'), True),
        ToolbarAction('showspriteimages', globals_.trans.string('menu_bar.view.item.sprite_images.label'), False),
        ToolbarAction('showentrances', globals_.trans.string('menu_bar.view.item.entrances.label'), False),
        ToolbarAction('showlocations', globals_.trans.string('menu_bar.view.item.locations.label'), True),
        ToolbarAction('showpaths', globals_.trans.string('menu_bar.view.item.paths.label'), True),
        ToolbarAction('grid', globals_.trans.string('menu_bar.view.item.switch_grid.label'), True),
        ToolbarAction('zoommax', globals_.trans.string('menu_bar.view.item.zoom_max.label'), True),
        ToolbarAction('zoomin', globals_.trans.string('menu_bar.view.item.zoom_in.label'), True),
        ToolbarAction('zoomactual', globals_.trans.string('menu_bar.view.item.zoom_actual.label'), True),
        ToolbarAction('zoomout', globals_.trans.string('menu_bar.view.item.zoom_out.label'), True),
        ToolbarAction('zoommin', globals_.trans.string('menu_bar.view.item.zoom_in.label'), True),
    )
    globals_.SettingsActions = (
        ToolbarAction('areaoptions', globals_.trans.string('menu_bar.settings.item.area_options.label'), True),
        ToolbarAction('camprofiles', globals_.trans.string('menu_bar.settings.item.camera_profiles.label'), False),
        ToolbarAction('zones', globals_.trans.string('menu_bar.settings.item.zone_settings.label'), True),
        ToolbarAction('backgrounds', globals_.trans.string('menu_bar.settings.item.backgrounds.label'), True),
        ToolbarAction('addarea', globals_.trans.string('menu_bar.settings.item.add_area.label'), False),
        ToolbarAction('importarea', globals_.trans.string('menu_bar.settings.item.import_area.label'), False),
        ToolbarAction('deletearea', globals_.trans.string('menu_bar.settings.item.delete_area.label'), False),
        ToolbarAction('reloadgfx', globals_.trans.string('menu_bar.settings.item.reload_tilesets.label'), False),
        ToolbarAction('reloaddata', globals_.trans.string('menu_bar.settings.item.reload_spritedata.label'), False),
    )
    globals_.HelpActions = (
        ToolbarAction('infobox', globals_.trans.string('menu_bar.help.item.about_reggie.label'), False),
        ToolbarAction('helpbox', globals_.trans.string('menu_bar.help.item.help_contents.label'), False),
        ToolbarAction('tipbox', globals_.trans.string('menu_bar.help.item.tips.label'), False),
        ToolbarAction('aboutqt', globals_.trans.string('menu_bar.help.item.about_qt.label'), False),
    )

def LoadDefaultKeybinds() -> None:
    """
    Defines the default keybinds (and display strings) for each menu item
    """
    globals_.FileKeybinds = [
        Keybind(
            "newlevel",
            globals_.trans.string("menu_bar.file.item.new_level.label"),
            QtGui.QKeySequence.StandardKey.New,
        ),
        Keybind(
            "openfromname",
            globals_.trans.string("menu_bar.file.item.open_by_name.label"),
            QtGui.QKeySequence.StandardKey.Open,
        ),
        Keybind(
            "openfromfile",
            globals_.trans.string("menu_bar.file.item.open_by_file.label"),
            "Ctrl+Shift+O",
        ),
        Keybind(
            "save",
            globals_.trans.string("menu_bar.file.item.save.label"),
            QtGui.QKeySequence.StandardKey.Save,
        ),
        Keybind(
            "saveas",
            globals_.trans.string("menu_bar.file.item.save_as.label"),
            QtGui.QKeySequence.StandardKey.SaveAs,
        ),
        Keybind(
            "savecopyas",
            globals_.trans.string("menu_bar.file.item.save_copy_as.label"),
            None,
        ),
        Keybind(
            "metainfo",
            globals_.trans.string("menu_bar.file.item.level_info.label"),
            "Ctrl+Alt+I",
        ),
        Keybind(
            "screenshot",
            globals_.trans.string("menu_bar.file.item.screenshot.label"),
            "Ctrl+Alt+S",
        ),
        Keybind(
            "changegamepath",
            globals_.trans.string("menu_bar.file.item.change_game_path.label"),
            "Ctrl+Alt+G",
        ),
        Keybind(
            "preferences",
            globals_.trans.string("menu_bar.file.item.preferences.label"),
            "Ctrl+Alt+P",
        ),
        Keybind(
            "exit",
            globals_.trans.string("menu_bar.file.item.exit.label"),
            "Ctrl+Q",
        ),
    ]
    globals_.EditKeybinds = [
        Keybind(
            "selectall",
            globals_.trans.string("menu_bar.edit.item.select_all.label"),
            QtGui.QKeySequence.StandardKey.SelectAll,
        ),
        Keybind(
            "deselect",
            globals_.trans.string("menu_bar.edit.item.deselect.label"),
            "Ctrl+D",
        ),
        Keybind(
            "undo",
            globals_.trans.string("menu_bar.edit.item.undo.label"),
            QtGui.QKeySequence.StandardKey.Undo,
        ),
        Keybind(
            "redo",
            globals_.trans.string("menu_bar.edit.item.redo.label"),
            QtGui.QKeySequence.StandardKey.Redo,
        ),
        Keybind(
            "cut",
            globals_.trans.string("menu_bar.edit.item.cut.label"),
            QtGui.QKeySequence.StandardKey.Cut,
        ),
        Keybind(
            "copy",
            globals_.trans.string("menu_bar.edit.item.copy.label"),
            QtGui.QKeySequence.StandardKey.Copy,
        ),
        Keybind(
            "paste",
            globals_.trans.string("menu_bar.edit.item.paste.label"),
            QtGui.QKeySequence.StandardKey.Paste,
        ),
        Keybind(
            "shiftitems",
            globals_.trans.string("menu_bar.edit.item.shift_items.label"),
            "Ctrl+Alt+Shift+S",
        ),
        Keybind(
            "mergelocations",
            globals_.trans.string("menu_bar.edit.item.merge_locations.label"),
            "Ctrl+Shift+E",
        ),
        Keybind(
            "swapobjectstilesets",
            globals_.trans.string("menu_bar.edit.item.swap_tilesets.label"),
            "Ctrl+Shift+L",
        ),
        Keybind(
            "swapobjectstypes",
            globals_.trans.string("menu_bar.edit.item.swap_objects.label"),
            "Ctrl+Shift+Y",
        ),
        Keybind(
            "switchsprites",
            globals_.trans.string("menu_bar.edit.item.switch_sprites.label"),
            None,
        ),
        Keybind(
            "diagnostic",
            globals_.trans.string("menu_bar.edit.item.diagnostic_tool.label"),
            "Ctrl+Shift+D",
        ),
        Keybind(
            "freezeobjects",
            globals_.trans.string("menu_bar.edit.item.freeze_objects.label"),
            "Ctrl+Shift+1",
        ),
        Keybind(
            "freezesprites",
            globals_.trans.string("menu_bar.edit.item.freeze_sprites.label"),
            "Ctrl+Shift+2",
        ),
        Keybind(
            "freezeentrances",
            globals_.trans.string("menu_bar.edit.item.freeze_entrances.label"),
            "Ctrl+Shift+3",
        ),
        Keybind(
            "freezelocations",
            globals_.trans.string("menu_bar.edit.item.freeze_locations.label"),
            "Ctrl+Shift+4",
        ),
        Keybind(
            "freezepaths",
            globals_.trans.string("menu_bar.edit.item.freeze_paths.label"),
            "Ctrl+Shift+5",
        ),
        Keybind(
            "freezecomments",
            globals_.trans.string("menu_bar.edit.item.freeze_comments.label"),
            "Ctrl+Shift+9",
        ),
    ]
    globals_.ViewKeybinds = [
        Keybind("showlay0", globals_.trans.string("menu_bar.view.item.layer0.label"), "Ctrl+1"),
        Keybind("showlay1", globals_.trans.string("menu_bar.view.item.layer1.label"), "Ctrl+2"),
        Keybind("showlay2", globals_.trans.string("menu_bar.view.item.layer2.label"), "Ctrl+3"),
        Keybind("tileanim", globals_.trans.string("menu_bar.view.item.tile_animations.label"), "Ctrl+7"),
        Keybind("collisions", globals_.trans.string("menu_bar.view.item.tile_collisions.label"), "Ctrl+8"),
        Keybind("realview", globals_.trans.string("menu_bar.view.item.real_view.label"), "Ctrl+9"),
        Keybind("showsprites", globals_.trans.string("menu_bar.view.item.sprites.label"), "Ctrl+4"),
        Keybind("showspriteimages", globals_.trans.string("menu_bar.view.item.sprite_images.label"), "Ctrl+6"),
        Keybind("showentrances", globals_.trans.string("menu_bar.view.item.entrances.label"), None),
        Keybind("showlocations", globals_.trans.string("menu_bar.view.item.locations.label"), "Ctrl+5"),
        Keybind("showcomments", globals_.trans.string("menu_bar.view.item.comments.label"), None),
        Keybind("showpaths", globals_.trans.string("menu_bar.view.item.paths.label"), "Ctrl"),
        Keybind("grid", globals_.trans.string("menu_bar.view.item.switch_grid.label"), "Ctrl+G"),
        Keybind("zoommax", globals_.trans.string("menu_bar.view.item.zoom_max.label"), "Ctrl+PgDown"),
        Keybind(
            "zoomin",
            globals_.trans.string("menu_bar.view.item.zoom_in.label"),
            QtGui.QKeySequence.StandardKey.ZoomIn,
        ),
        Keybind("zoomactual", globals_.trans.string("menu_bar.view.item.zoom_out.label"), "Ctrl+0"),
        Keybind(
            "zoomout",
            globals_.trans.string("menu_bar.view.item.zoom_out.label"),
            QtGui.QKeySequence.StandardKey.ZoomOut,
        ),
        Keybind("zoommin", globals_.trans.string("menu_bar.view.item.zoom_min.label"), "Ctrl+PgUp"),
        Keybind("leveloverview", globals_.trans.string("menu_bar.view.item.level_overview.label"), "Ctrl+M"),
        Keybind("palette", globals_.trans.string("menu_bar.view.item.palette.label"), "Ctrl+P"),
        Keybind("toolbar", globals_.trans.string("menu_bar.editor_toolbar.label"), "Ctrl+T"),
    ]
    globals_.SettingsKeybinds = [
        Keybind("areaoptions", globals_.trans.string("menu_bar.settings.item.area_options.label"), "Ctrl+Alt+A"),
        Keybind("zones", globals_.trans.string("menu_bar.settings.item.zone_settings.label"), "Ctrl+Alt+Z"),
        Keybind("backgrounds", globals_.trans.string("menu_bar.settings.item.backgrounds.label"), "Ctrl+Alt+B"),
        Keybind("camprofiles", globals_.trans.string("menu_bar.settings.item.camera_profiles.label"), "Ctrl+Alt+C"),
        Keybind("addarea", globals_.trans.string("menu_bar.settings.item.add_area.label"), "Ctrl+Alt+N"),
        Keybind("importarea", globals_.trans.string("menu_bar.settings.item.import_area.label"), "Ctrl+Alt+O"),
        Keybind("deletearea", globals_.trans.string("menu_bar.settings.item.delete_area.label"), "Ctrl+Alt+D"),
        Keybind("reloadgfx", globals_.trans.string("menu_bar.settings.item.reload_tilesets.label"), "Ctrl+Shift+R"),
        Keybind("reloaddata", globals_.trans.string("menu_bar.settings.item.reload_spritedata.label"), None),
    ]
    globals_.HelpKeybinds = [
        Keybind("infobox", globals_.trans.string("menu_bar.help.item.about_reggie.label"), "Ctrl+Shift+I"),
        Keybind("helpbox", globals_.trans.string("menu_bar.help.item.help_contents.label"), "Ctrl+Shift+H"),
        Keybind("tipbox", globals_.trans.string("menu_bar.help.item.tips.label"), "Ctrl+Shift+T"),
        Keybind("aboutqt", globals_.trans.string("menu_bar.help.item.about_qt.label"), "Ctrl+Shift+Q"),
    ]


def GetKeybind(name: str) -> QtGui.QKeySequence | None:
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


def SetKeybind(name: str, sequence: QtGui.QKeySequence | None) -> None:
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


def CreateTilesets() -> None:
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


def LoadTileset(idx: int, name: str, reload_: bool = False) -> None:
    """
    Load in a tileset into a specific slot
    """
    if not name:
        return

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
        QtWidgets.QMessageBox.warning(None, globals_.trans.string('error.title.error'),
                                      globals_.trans.string('error.file_not_found.tileset', ('[file]', name)))
        return

    # If this file's already loaded, return
    if globals_.TilesetFilesLoaded[idx] == arcname and not reload_:
        return

    # Get the data
    with open(arcname, 'rb') as fileobj:
        arcdata = fileobj.read()

    if compressed:
        arcdata = DecompressLevel(arcdata, name)

    arc = archive.U8.load(arcdata)

    def exists(fn: str) -> bool:
        nonlocal arc
        try:
            arc[fn]
        except (IndexError, KeyError):
            return False
        return True

    # Decompress the textures
    found = exists(f'BG_tex/{name}_tex.bin.LZ')
    found2 = exists(f'BG_chk/d_bgchk_{name}.bin')

    if found and found2:
        comptiledata = arc[f'BG_tex/{name}_tex.bin.LZ']
        colldata = bytes(arc[f'BG_chk/d_bgchk_{name}.bin'])
    else:
        QtWidgets.QMessageBox.warning(None, globals_.trans.string('error.title.error'),
                                      globals_.trans.string('error.file_not_found.tileset_texture', ('[file]', name)))
        return

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
        current_tile = globals_.Tiles[i]
        if current_tile is None:
            continue

        if idx == 0:
            if current_tile.collData[3] == 5:
                fn = 'BG_tex/hatena_anime.bin'
                found = exists(fn)

                if found:
                    current_tile.addAnimationData(arc[fn])

            elif current_tile.collData[3] == 0x10:
                fn = 'BG_tex/block_anime.bin'
                found = exists(fn)

                if found:
                    current_tile.addAnimationData(arc[fn])

            elif current_tile.collData[7] == 0x28:
                fn = 'BG_tex/tuka_coin_anime.bin'
                found = exists(fn)

                if found:
                    current_tile.addAnimationData(arc[fn])

        # TODO: Dehardcode this?
        elif idx == 1 and name in containsConveyor:
            for x in range(2):
                if i == 320+x*16:
                    fn = 'BG_tex/belt_conveyor_L_anime.bin'
                    found = exists(fn)

                    if found:
                        current_tile.addAnimationData(arc[fn], True)

                elif i == 321+x*16:
                    fn = 'BG_tex/belt_conveyor_M_anime.bin'
                    found = exists(fn)

                    if found:
                        current_tile.addAnimationData(arc[fn], True)

                elif i == 322+x*16:
                    fn = 'BG_tex/belt_conveyor_R_anime.bin'
                    found = exists(fn)

                    if found:
                        current_tile.addAnimationData(arc[fn], True)

                elif i == 323+x*16:
                    fn = 'BG_tex/belt_conveyor_L_anime.bin'
                    found = exists(fn)

                    if found:
                        current_tile.addAnimationData(arc[fn])

                elif i == 324+x*16:
                    fn = 'BG_tex/belt_conveyor_M_anime.bin'
                    found = exists(fn)

                    if found:
                        current_tile.addAnimationData(arc[fn])

                elif i == 325+x*16:
                    fn = 'BG_tex/belt_conveyor_R_anime.bin'
                    found = exists(fn)
                    if found:
                        current_tile.addAnimationData(arc[fn])

        # Setup Newer-style animated tiles
        if isAnimated:
            filenames = []
            filenames.append(f'{prefix}_{idx}{hex(row)[2].lower()}{hex(col)[2].lower()}.bin')
            filenames.append(f'{prefix}_{idx}{hex(row)[2].upper()}{hex(col)[2].upper()}.bin')

            if filenames[0] == filenames[1]:
                item = filenames[0]
                filenames = []
                filenames.append(item)

            for fn in filenames:
                fn = 'BG_tex/' + fn
                found = exists(fn)

                if found:
                    current_tile.addAnimationData(arc[fn])

        col += 1

        if col == 16:
            col = 0
            row += 1

    # Load the object definitions
    defs: list[ObjectDef | None] = [None] * 256

    indexfile = bytes(arc[f'BG_unt/{name}_hd.bin'])
    deffile = arc[f'BG_unt/{name}.bin']
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

    return


def LoadTexture_NSMBW(tiledata: bytes) -> QtGui.QImage:
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


def UnloadTileset(idx: int) -> None:
    """
    Unload the tileset from a specific slot
    """
    tileoffset = idx * 256
    globals_.Tiles[tileoffset:tileoffset + 256] = [None] * 256
    globals_.ObjectDefinitions[idx] = [None] * 256
    globals_.TilesetFilesLoaded[idx] = None


def ReloadTilesets(soft=False):
    """
    Reloads all the tilesets. If soft is True, they will not be reloaded if the filepaths have not changed.
    """
    if not hasattr(globals_, 'mainWindow'):
        return

    LoadTilesetInfo(True)

    for idx, name in enumerate(globals_.Area.tilesets):
        if (name is not None) and (name != ''):
            LoadTileset(idx, name, not soft)

    globals_.mainWindow.palette_dock.object_tab.object_picker.LoadFromTilesets()

    for layer in globals_.Area.layers:
        for obj in layer:
            obj.updateObjCache()

    globals_.mainWindow.scene.update()


def ProcessOverrides(idx: int, name: str) -> None:
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
        if globals_.Overrides_safe[0] is not None:
            baseblock = globals_.Overrides_safe[0].main
            for i, replace in zip(invisiblocks, replacement):
                current_tile = t[i]
                override_tile = globals_.Overrides_safe[replace]
                if current_tile is not None and override_tile is not None:
                    current_tile.main = overlay(baseblock, override_tile.main)

            # Question and brick blocks
            # these don't have their own tiles so we have to do them by objects
            rangeA, rangeB = range(39, 49), range(27, 38)
            replace = 2048 + 10
            question_block_def = defs[39]
            if question_block_def is not None:
                baseblock = t[question_block_def.rows[0][0].tilenum].main

            # question blocks
            for i, a in zip(rangeA, range(2, 12)):
                current_tile = t[replace]
                override_tile = globals_.Overrides_safe[a]
                if current_tile is not None and override_tile is not None:
                    current_tile.main = overlay(baseblock, override_tile.main)
                current_def = defs[i]
                if current_def is not None:
                    current_def.rows[0][0] = TileDef(0, replace, 0)
                    replace += 1

            replace += 1
            brick_block_def = defs[26]
            if brick_block_def is not None:
                baseblock = t[brick_block_def.rows[0][0].tilenum].main
            # brick block
            for i, a in zip(rangeB, (1, 12, 2, 3, 13, 5, 7, 8, 9, 10, 11)):
                current_tile = t[replace]
                override_tile = globals_.Overrides_safe[a]
                if current_tile is not None and override_tile is not None:
                    current_tile.main = overlay(baseblock, override_tile.main)
                current_def = defs[i]
                if current_def is not None:
                    current_def.rows[0][0] = TileDef(0, replace, 0)
                replace += 1

        # now the extra stuff (invisible collisions etc)
        # @ row i, col j => globals_.Overrides[26 * i + j]

        assign_override(t[1], globals_.Overrides[26 * 4])        # solid
        assign_override(t[2], globals_.Overrides[26 + 10])       # vine stopper
        assign_override(t[11], globals_.Overrides[26 * 3 + 13])  # jumpthrough platform
        assign_override(t[12], globals_.Overrides[26 * 3 + 12])  # mini mario passageway

        assign_override(t[16], globals_.Overrides[26 * 4 + 11])  # 1x1 slope going up
        assign_override(t[17], globals_.Overrides[26 * 4 + 12])  # 1x1 slope going down
        assign_override(t[18], globals_.Overrides[26 * 4 + 1])   # 2x1 slope going up (part 1)
        assign_override(t[19], globals_.Overrides[26 * 4 + 2])   # 2x1 slope going up (part 2)
        assign_override(t[20], globals_.Overrides[26 * 4 + 3])   # 2x1 slope going down (part 1)
        assign_override(t[21], globals_.Overrides[26 * 4 + 4])   # 2x1 slope going down (part 2)
        assign_override(t[22], globals_.Overrides[26 * 4 + 21])  # 4x1 slope going up (part 1)
        assign_override(t[23], globals_.Overrides[26 * 4 + 22])  # 4x1 slope going up (part 2)
        assign_override(t[24], globals_.Overrides[26 * 4 + 23])  # 4x1 slope going up (part 3)
        assign_override(t[25], globals_.Overrides[26 * 4 + 24])  # 4x1 slope going up (part 4)
        assign_override(t[26], globals_.Overrides[26 * 4 + 25])  # 4x1 slope going down (part 1)
        assign_override(t[27], globals_.Overrides[26 * 4 - 3])   # 4x1 slope going down (part 2)
        assign_override(t[28], globals_.Overrides[26 * 4 - 2])   # 4x1 slope going down (part 3)
        assign_override(t[29], globals_.Overrides[26 * 4 - 1])   # 4x1 slope going down (part 4)
        assign_override(t[30], globals_.Overrides[1])            # coin

        assign_override(t[32], globals_.Overrides[26 * 4 + 9])   # 1x1 roof going down
        assign_override(t[33], globals_.Overrides[26 * 4 + 10])  # 1x1 roof going up
        assign_override(t[34], globals_.Overrides[26 * 4 + 5])   # 2x1 roof going down (part 1)
        assign_override(t[35], globals_.Overrides[26 * 4 + 6])   # 2x1 roof going down (part 2)
        assign_override(t[36], globals_.Overrides[26 * 4 + 7])   # 2x1 roof going up (part 1)
        assign_override(t[37], globals_.Overrides[26 * 4 + 8])   # 2x1 roof going up (part 2)
        assign_override(t[38], globals_.Overrides[26 * 4 + 13])  # 4x1 roof going down (part 1)
        assign_override(t[39], globals_.Overrides[26 * 4 + 14])  # 4x1 roof going down (part 2)
        assign_override(t[40], globals_.Overrides[26 * 4 + 15])  # 4x1 roof going down (part 3)
        assign_override(t[41], globals_.Overrides[26 * 4 + 16])  # 4x1 roof going down (part 4)
        assign_override(t[42], globals_.Overrides[26 * 4 + 17])  # 4x1 roof going up (part 1)
        assign_override(t[43], globals_.Overrides[26 * 4 + 18])  # 4x1 roof going up (part 2)
        assign_override(t[44], globals_.Overrides[26 * 4 + 19])  # 4x1 roof going up (part 3)
        assign_override(t[45], globals_.Overrides[26 * 4 + 20])  # 4x1 roof going up (part 4)
        assign_override(t[46], globals_.Overrides[26 + 11])      # P-switch coin

        assign_override(t[53], globals_.Overrides[26 + 12])      # donut lift
        assign_override(t[61], globals_.Overrides[26 + 9])       # multiplayer coin
        assign_override(t[63], globals_.Overrides[26 * 2 + 13])  # invisible damage tile

    if name in tsidx["Flowers"] or name in tsidx["Forest Flowers"]:
        # flowers
        t = globals_.Tiles
        assign_override(t[tsOffs + 0xA0], globals_.Overrides_safe[26 + 4])     # grass
        assign_override(t[tsOffs + 0xA1], globals_.Overrides_safe[26 + 5])
        assign_override(t[tsOffs + 0xA2], globals_.Overrides[26 + 6])
        assign_override(t[tsOffs + 0xA3], globals_.Overrides[26 + 7])
        assign_override(t[tsOffs + 0xA4], globals_.Overrides[26 + 8])

        if name in tsidx["Flowers"]:
            assign_override(t[tsOffs + 0xB0], globals_.Overrides[26 * 2 + 9])  # flowers
            assign_override(t[tsOffs + 0xB1], globals_.Overrides[26 * 2 + 10])
            assign_override(t[tsOffs + 0xB2], globals_.Overrides[26 * 2 + 11])

            assign_override(t[tsOffs + 0xC0], globals_.Overrides[26 * 2 + 6])  # flowers on grass
            assign_override(t[tsOffs + 0xC1], globals_.Overrides[26 * 2 + 7])
            assign_override(t[tsOffs + 0xC2], globals_.Overrides[26 * 2 + 8])
        elif name in tsidx["Forest Flowers"]:
            # forest flowers
            assign_override(t[tsOffs + 0xB0], globals_.Overrides[26 * 3 + 9])  # flowers
            assign_override(t[tsOffs + 0xB1], globals_.Overrides[26 * 3 + 10])
            assign_override(t[tsOffs + 0xB2], globals_.Overrides[26 * 3 + 11])

            assign_override(t[tsOffs + 0xC0], globals_.Overrides[26 * 3 + 6])  # flowers on grass
            assign_override(t[tsOffs + 0xC1], globals_.Overrides[26 * 3 + 7])
            assign_override(t[tsOffs + 0xC2], globals_.Overrides[26 * 3 + 8])

    if name in tsidx["Conveyors"]:
        # Conveyor belts
        t = globals_.Tiles
        tiles = [0x40, 0x41, 0x42, 0x43, 0x44, 0x45, # Right (slow), Right (fast)
                 0x50, 0x51, 0x52, 0x53, 0x54, 0x55] # Left  (slow), Left  (fast)

        for i, tileNum in enumerate(tiles):
            current_tile = t[tsOffs + tileNum]
            override_tile = globals_.Overrides[26 * 5 + i]
            if current_tile is not None and override_tile is not None:
                current_tile.main = overlay(current_tile.main, override_tile.main)

    if name in tsidx["Lines"] or name in tsidx["Full Lines"]:
        # These are the line guides
        # normal lines have fewer though

        t = globals_.Tiles

        # use Overrides_safe here because the beginning of Overrides is overwritten
        assign_override(t[tsOffs], globals_.Overrides_safe[26])             # horizontal line
        assign_override(t[tsOffs + 1], globals_.Overrides_safe[26 + 1])     # vertical line
        assign_override(t[tsOffs + 2], globals_.Overrides_safe[26 + 2])     # bottom-right corner
        assign_override(t[tsOffs + 3], globals_.Overrides_safe[26 + 3])     # top-left corner

        assign_override(t[tsOffs + 0x10], globals_.Overrides[26 * 2])       # left red blob (part 1)
        assign_override(t[tsOffs + 0x11], globals_.Overrides[26 * 2 + 1])   # top red blob (part 1)
        assign_override(t[tsOffs + 0x12], globals_.Overrides[26 * 2 + 2])   # top red blob (part 2)
        assign_override(t[tsOffs + 0x13], globals_.Overrides[26 * 2 + 3])   # right red blob (part 1)
        assign_override(t[tsOffs + 0x14], globals_.Overrides[26 * 2 + 4])   # top-left red blob
        assign_override(t[tsOffs + 0x15], globals_.Overrides[26 * 2 + 5])   # top-right red blob

        assign_override(t[tsOffs + 0x20], globals_.Overrides[26 * 3])       # left red blob (part 2)
        assign_override(t[tsOffs + 0x21], globals_.Overrides[26 * 3 + 1])   # bottom red blob (part 1)
        assign_override(t[tsOffs + 0x22], globals_.Overrides[26 * 3 + 2])   # bottom red blob (part 2)
        assign_override(t[tsOffs + 0x23], globals_.Overrides[26 * 3 + 3])   # right red blob (part 2)
        assign_override(t[tsOffs + 0x24], globals_.Overrides[26 * 3 + 4])   # bottom-left red blob
        assign_override(t[tsOffs + 0x25], globals_.Overrides[26 * 3 + 5])   # bottom-right red blob

        # Those are all for normal lines
        if name in tsidx["Lines"]: return

        assign_override(t[tsOffs + 0x30], globals_.Overrides_safe[14])      # 1x2 diagonal going up (top edge)
        assign_override(t[tsOffs + 0x31], globals_.Overrides_safe[15])      # 1x2 diagonal going down (top edge)

        assign_override(t[tsOffs + 0x40], globals_.Overrides[26 + 14])      # 1x2 diagonal going up (part 1)
        assign_override(t[tsOffs + 0x41], globals_.Overrides[26 + 15])      # 1x2 diagonal going down (part 1)
        assign_override(t[tsOffs + 0x42], globals_.Overrides[26 * 2 + 19])  # 1x1 diagonal going up
        assign_override(t[tsOffs + 0x43], globals_.Overrides[26 * 2 + 20])  # 1x1 diagonal going down
        #assign_override(t[tsOffs + 0x44], globals_.Overrides[ + 1058])     # 2x1 diagonal going up (part 1) nothing
        assign_override(t[tsOffs + 0x45], globals_.Overrides[20])           # 2x1 diagonal going up (part 2)
        assign_override(t[tsOffs + 0x46], globals_.Overrides_safe[21])      # 2x1 diagonal going down (part 1)
        #assign_override(t[tsOffs + 0x47], globals_.Overrides[ + 1061])     # 2x1 diagonal going down (part 2) nothing

        assign_override(t[tsOffs + 0x50], globals_.Overrides[26 * 2 + 14])  # 1x2 diagonal going up (part 2)
        assign_override(t[tsOffs + 0x51], globals_.Overrides[26 * 2 + 15])  # 1x2 diagonal going down (part 2)
        assign_override(t[tsOffs + 0x52], globals_.Overrides[26 * 3 + 14])  # 1x1 diagonal going up
        assign_override(t[tsOffs + 0x53], globals_.Overrides[26 * 3 + 15])  # 1x1 diagonal going down
        assign_override(t[tsOffs + 0x54], globals_.Overrides[26 + 19])      # 2x1 diagonal going up (part 1)
        assign_override(t[tsOffs + 0x55], globals_.Overrides[26 + 20])      # 2x1 diagonal going up (part 2)
        assign_override(t[tsOffs + 0x56], globals_.Overrides[26 + 21])      # 2x1 diagonal going down (part 1)
        assign_override(t[tsOffs + 0x57], globals_.Overrides[26 + 22])      # 2x1 diagonal going down (part 2)

        assign_override(t[tsOffs + 0x62], globals_.Overrides[26 * 3 + 17])  # big circle piece 1st row
        assign_override(t[tsOffs + 0x63], globals_.Overrides[26 * 3 + 18])  # big circle piece 1st row
        assign_override(t[tsOffs + 0x66], globals_.Overrides_safe[17])      # medium circle piece 1st row
        assign_override(t[tsOffs + 0x67], globals_.Overrides_safe[18])      # medium circle piece 1st row

        assign_override(t[tsOffs + 0x71], globals_.Overrides[26 * 3 + 20])  # big circle piece 2nd row
        assign_override(t[tsOffs + 0x72], globals_.Overrides_safe[23])      # big circle piece 2nd row
        assign_override(t[tsOffs + 0x73], globals_.Overrides_safe[24])      # big circle piece 2nd row
        assign_override(t[tsOffs + 0x74], globals_.Overrides_safe[25])      # big circle piece 2nd row
        assign_override(t[tsOffs + 0x75], globals_.Overrides[26 + 16])      # medium circle piece 2nd row
        assign_override(t[tsOffs + 0x76], globals_.Overrides[26 + 17])      # medium circle piece 2nd row
        assign_override(t[tsOffs + 0x77], globals_.Overrides[26 + 18])      # medium circle piece 2nd row
        assign_override(t[tsOffs + 0x78], globals_.Overrides[26 + 13])      # small circle

        assign_override(t[tsOffs + 0x80], globals_.Overrides[26 * 2 + 21])  # big circle piece 3rd row
        assign_override(t[tsOffs + 0x81], globals_.Overrides[26 * 2 + 22])  # big circle piece 3rd row
        assign_override(t[tsOffs + 0x84], globals_.Overrides[26 * 2 + 24])  # big circle piece 3rd row
        assign_override(t[tsOffs + 0x85], globals_.Overrides[26 * 2 + 16])  # medium circle piece 3rd row
        assign_override(t[tsOffs + 0x86], globals_.Overrides[26 * 2 + 17])  # medium circle piece 3rd row
        assign_override(t[tsOffs + 0x87], globals_.Overrides[26 * 2 + 18])  # medium circle piece 3rd row

        assign_override(t[tsOffs + 0x90], globals_.Overrides[26 * 3 + 21])  # big circle piece 4th row
        assign_override(t[tsOffs + 0x91], globals_.Overrides[26 * 3 + 22])  # big circle piece 4th row
        assign_override(t[tsOffs + 0x94], globals_.Overrides[26 * 2 + 25])  # big circle piece 4th row

        assign_override(t[tsOffs + 0xA1], globals_.Overrides[26 * 2 + 23])  # big circle piece 5th row
        assign_override(t[tsOffs + 0xA2], globals_.Overrides[26 + 23])      # big circle piece 5th row
        assign_override(t[tsOffs + 0xA3], globals_.Overrides[26 + 24])      # big circle piece 5th row
        assign_override(t[tsOffs + 0xA4], globals_.Overrides[26 + 25])      # big circle piece 5th row

    elif name in tsidx["Minigame Lines"]:
        t = globals_.Tiles

        assign_override(t[tsOffs + 0x40], globals_.Overrides_safe[26])      # horizontal line
        assign_override(t[tsOffs + 0x41], globals_.Overrides_safe[26 + 2])  # bottom-right corner
        assign_override(t[tsOffs + 0x42], globals_.Overrides_safe[26])      # horizontal line

        assign_override(t[tsOffs + 0x50], globals_.Overrides_safe[26 + 1])  # vertical line
        assign_override(t[tsOffs + 0x51], globals_.Overrides_safe[26 + 1])  # vertical line
        assign_override(t[tsOffs + 0x52], globals_.Overrides_safe[26 + 3])  # top-left corner

        assign_override(t[tsOffs + 0x43], globals_.Overrides[26 * 2])       # left red blob (part 1)
        assign_override(t[tsOffs + 0x44], globals_.Overrides[26 * 2 + 1])   # top red blob (part 1)
        assign_override(t[tsOffs + 0x45], globals_.Overrides[26 * 2 + 2])   # top red blob (part 2)
        assign_override(t[tsOffs + 0x46], globals_.Overrides[26 * 2 + 3])   # right red blob (part 1)

        assign_override(t[tsOffs + 0x53], globals_.Overrides[26 * 3])       # left red blob (part 2)
        assign_override(t[tsOffs + 0x54], globals_.Overrides[26 * 3 + 1])   # bottom red blob (part 1)
        assign_override(t[tsOffs + 0x55], globals_.Overrides[26 * 3 + 2])   # bottom red blob (part 2)
        assign_override(t[tsOffs + 0x56], globals_.Overrides[26 * 3 + 3])   # right red blob (part 2)

        assign_override(t[tsOffs + 0x62], globals_.Overrides[26 * 3 + 17])  # big circle piece 1st row
        assign_override(t[tsOffs + 0x63], globals_.Overrides[26 * 3 + 18])  # big circle piece 1st row
        assign_override(t[tsOffs + 0x66], globals_.Overrides_safe[17])      # medium circle piece 1st row
        assign_override(t[tsOffs + 0x67], globals_.Overrides_safe[18])      # medium circle piece 1st row

        assign_override(t[tsOffs + 0x71], globals_.Overrides[26 * 3 + 20])  # big circle piece 2nd row
        assign_override(t[tsOffs + 0x72], globals_.Overrides_safe[23])      # big circle piece 2nd row
        assign_override(t[tsOffs + 0x73], globals_.Overrides_safe[24])      # big circle piece 2nd row
        assign_override(t[tsOffs + 0x74], globals_.Overrides_safe[25])      # big circle piece 2nd row
        assign_override(t[tsOffs + 0x75], globals_.Overrides[26 + 16])      # medium circle piece 2nd row
        assign_override(t[tsOffs + 0x76], globals_.Overrides[26 + 17])      # medium circle piece 2nd row
        assign_override(t[tsOffs + 0x77], globals_.Overrides[26 + 18])      # medium circle piece 2nd row

        assign_override(t[tsOffs + 0x80], globals_.Overrides[26 * 2 + 21])  # big circle piece 3rd row
        assign_override(t[tsOffs + 0x81], globals_.Overrides[26 * 2 + 22])  # big circle piece 3rd row
        assign_override(t[tsOffs + 0x84], globals_.Overrides[26 * 2 + 24])  # big circle piece 3rd row
        assign_override(t[tsOffs + 0x85], globals_.Overrides[26 * 2 + 16])  # medium circle piece 3rd row
        assign_override(t[tsOffs + 0x86], globals_.Overrides[26 * 2 + 17])  # medium circle piece 3rd row
        assign_override(t[tsOffs + 0x87], globals_.Overrides[26 * 2 + 18])  # medium circle piece 3rd row

        assign_override(t[tsOffs + 0x90], globals_.Overrides[26 * 3 + 21])  # big circle piece 4th row
        assign_override(t[tsOffs + 0x91], globals_.Overrides[26 * 3 + 22])  # big circle piece 4th row
        assign_override(t[tsOffs + 0x94], globals_.Overrides[26 * 2 + 25])  # big circle piece 4th row

        assign_override(t[tsOffs + 0xA1], globals_.Overrides[26 * 2 + 23])  # big circle piece 5th row
        assign_override(t[tsOffs + 0xA2], globals_.Overrides[26 + 23])      # big circle piece 5th row
        assign_override(t[tsOffs + 0xA3], globals_.Overrides[26 + 24])      # big circle piece 5th row
        assign_override(t[tsOffs + 0xA4], globals_.Overrides[26 + 25])      # big circle piece 5th row


def assign_override(tile: TilesetTile | None, override: TilesetTile | None) -> None:
    """
    Assigns an override to a tile, if both are not None.
    """
    if tile is not None and override is not None:
        tile.main = override.main

def LoadOverrides() -> None:
    """
    Load overrides
    """
    globals_.Overrides = [None] * (6 * 26)
    globals_.Overrides_safe = [None] * (6 * 26)
    globals_.OVERRIDE_UNKNOWN = 2 * 26 + 12

    OverrideBitmap = QtGui.QPixmap(os.path.join(get_reggiedata_folder(), 'overrides.png'))
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
                override_tile = globals_.Overrides[idx]
                override_tile_safe = globals_.Overrides_safe[idx]
                if override_tile is not None and override_tile_safe is not None:
                    if 8 < x < 20:
                        override_tile.setQuestionCollisions()
                        override_tile_safe.setQuestionCollisions()
                    elif 20 <= x < 32:
                        override_tile.setBrickCollisions()
                        override_tile_safe.setBrickCollisions()

            idx += 1
            sourcex += 24
        sourcex = 0
        sourcey += 24


def CheckTilesetAnimated(tileset: archive.U8) -> tuple[bool, str | None]:
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


def LoadTheme() -> None:
    """
    Loads the theme
    """
    globals_.theme = ReggieTheme(setting("Theme", "Classic"))


def LoadTranslation() -> None:
    """
    Loads the translation
    """
    name = setting('Translation')

    # The default value is English and can be represented in the settings in
    # several ways.
    if name in (None, 'None', 'English', '', 0):
        return

    globals_.trans |= Translation.from_xml(name)

def DecompressLevel(data: bytes, name: str) -> bytes | None:
    """
    Handles decompressing an LZ/LH compressed file.
    Returns a decompressed file (original if input was uncompressed), or None if failed.
    """
    # LH-compressed
    if (data[0] & 0xF0) == 0x40:
        try:
            data = lh.UncompressLH(data)
        except IndexError:
            QtWidgets.QMessageBox.warning(None, globals_.trans.string('error.title.error'),
                                            globals_.trans.string('error.decompress.lh', ('[file]', name)))
            return None

    # LZ-compressed
    elif not data.startswith(b"U\xAA8-"):
        try:
            data = lz77.UncompressLZ77(data)
        except IndexError:
            QtWidgets.QMessageBox.warning(None, globals_.trans.string('error.title.error'),
                                            globals_.trans.string('error.decompress.lz', ('[file]', name)))
            return None

    return data
