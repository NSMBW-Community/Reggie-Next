import functools
import importlib.util
import os
import sys
from xml.etree import ElementTree as etree

from PyQt6 import QtWidgets

import globals_
import spritelib as SLib
import sprites
from dirty import setSetting, setting
from sprites_common import LoadBasics
from src.data.common.loaders import (
    LoadBgANames,
    LoadBgBNames,
    LoadConfig,
    LoadEntranceNames,
    LoadMusicInfo,
    LoadObjDescriptions,
    LoadSpriteCategories,
    LoadSpriteData,
    LoadTilesetInfo,
    LoadTilesetNames,
    LoadZoneThemes,
)


# Gamedef File - has 2 values: name (str) and patch (bool)
class GameDefinitionFile:
    """
    A class that defines a filepath, and some options
    """

    def __init__(self, path: str | None, patch: bool):
        """
        Initializes the GameDefinitionFile
        """
        self.path = path or ''
        self.patch = patch


class ReggieGameDefinition:
    """
    A class that defines a NSMBW hack: songs, tilesets, sprites, etc.
    """

    def __init__(self, name: str | None = None):
        """
        Initializes the ReggieGameDefinition
        """
        self.InitAsEmpty()

        # Try to init it from name if possible
        NoneTypes = (None, 'None', 0, '', True, False)
        if name in NoneTypes:
            return

        result = self.InitFromName(name)
        if not result:
            self.InitAsEmpty()
            setSetting('LastGameDef', None)

    def InitAsEmpty(self):
        """
        Sets all properties to their default values
        """
        gdf = GameDefinitionFile

        self.custom = False
        self.base = None  # gamedef to use as a base
        self.gamepath = None
        self.name = globals_.trans.string('Gamedefs', 13)  # 'New Super Mario Bros. Wii'
        self.description = globals_.trans.string('Gamedefs', 14)  # 'A new Mario adventure!<br>' and the date
        self.version = '2'

        self.sprites = sprites

        self.files = {
            'bga': gdf(os.path.join('reggiedata', 'bga.txt'), False),
            'bgb': gdf(os.path.join('reggiedata', 'bgb.txt'), False),
            'config': gdf(os.path.join('reggiedata', 'config.xml'), False),
            'entrancetypes': gdf(os.path.join('reggiedata', 'entrancetypes.txt'), False),
            'levelnames': gdf(os.path.join('reggiedata', 'levelnames.xml'), False),
            'music': gdf(os.path.join('reggiedata', 'music.txt'), False),
            'spritecategories': gdf(os.path.join('reggiedata', 'spritecategories.xml'), False),
            'spritedata': gdf(os.path.join('reggiedata', 'spritedata.xml'), False),
            'tilesetinfo': gdf(os.path.join('reggiedata', 'tilesetinfo.xml'), False),
            'tilesets': gdf(os.path.join('reggiedata', 'tilesets.xml'), False),
            'ts1_descriptions': gdf(os.path.join('reggiedata', 'ts1_descriptions.txt'), False),
            'zonethemes': gdf(os.path.join('reggiedata', 'zonethemes.txt'), False),
        }
        self.folders = {
            'bga': gdf(None, False),
            'bgb': gdf(None, False),
            'sprites': gdf(None, False),
            'external': gdf(None, False),
        }

    def InitFromName(self, name: str):
        """
        Attempts to open/load a Game Definition from a name string. Just loads
        the name and description to avoid referring to other game definitions.
        """
        self.custom = True
        name = str(name)
        self.gamepath = name

        # Parse the file (errors are handled by __init__())
        path = os.path.join("reggiedata", "patches", name, "main.xml")
        try:
            tree = etree.parse(path)
        except FileNotFoundError:
            return False
        root = tree.getroot()

        # Add the attributes of root: name, description and version.
        # base is added in __init2__, only when needed.
        self.name = root.get('name')

        if self.name is None:
            raise ValueError("Game definition XML %r has no 'name' attribute on the root node." % path)

        default = globals_.trans.string('Gamedefs', 15)

        desc = root.get('description', default)
        if desc is not None:
            self.description = desc.replace('[', '<').replace(']', '>')
        self.version = root.get('version')
        return True

    def __init2__(self):
        """
        Finishes up initialisation of custom gamedefs. This avoids infinite
        recursion with gamedefs referring to other gamedefs.
        """
        if not self.custom or not isinstance(self.gamepath, str):
            return

        path = os.path.join("reggiedata", "patches", self.gamepath, "main.xml")
        try:
            tree = etree.parse(path)
        except FileNotFoundError:
            return
        root = tree.getroot()

        self.base = None
        if 'base' in root.attrib:
            self.base = FindGameDef(root.attrib['base'], self.gamepath)
        else:
            self.base = ReggieGameDefinition()

        # Parse the nodes
        addpath = os.path.join("reggiedata", "patches", self.gamepath)
        for node in root:
            n = node.tag.lower()
            if n not in ('file', 'folder'):
                continue

            patch = node.get('patch', 'true').lower() == 'true'
            node_path = node.get('path')
            if node_path is not None:
                game = node.get('game')
                if game is None:
                    path = os.path.join(addpath, node_path)
                elif game == globals_.trans.string('Gamedefs', 13):  # 'New Super Mario Bros. Wii'
                    path = os.path.join('reggiedata', node_path)
                else:
                    def_ = FindGameDef(game, self.gamepath)
                    if def_ is not None and def_.gamepath is not None:
                        path = os.path.join('reggiedata', 'patches', def_.gamepath, node_path)

                node_name = node.get('name')
                dict_type = self.files if n == 'file' else self.folders  # self.files or self.folders
                if node_name is not None:
                    dict_type[node_name] = GameDefinitionFile(path, patch)

        # Get rid of the XML stuff
        del tree, root

        # Load sprites.py if provided
        if 'sprites' in self.files:
            # Check if sprites.py has anything that won't work in PyQt6
            FixSpritesModule(self.files['sprites'].path)

            with open(self.files['sprites'].path, 'r', encoding='utf-8') as f:
                filedata = f.read()

            # https://stackoverflow.com/a/53080237 with modifications
            if self.name is None:
                return

            spec = importlib.util.spec_from_loader(self.name + "->sprites", loader=None)
            if spec is not None:
                new_module = importlib.util.module_from_spec(spec)

                exec(filedata, new_module.__dict__)
                sys.modules[new_module.__name__] = new_module
                self.sprites = new_module

    def bgFile(self, name: str, layer: str):
        """
        Returns the folder to a bg image. Layer must be 'a' or 'b'
        """
        # Name will be of the format '0000.png'
        fallback = os.path.join('reggiedata', 'bg' + layer, name)
        filename = os.path.join('bg' + layer, name)

        # See if it was defined specifically
        if filename in self.files:
            path = self.files[filename].path
            if os.path.isfile(path):
                return path

        # See if it's in one of self.folders
        if self.folders['bg%s' % layer].path is not None:
            if not name:
                trypath = os.path.join(self.folders[f'bg{layer}'].path, name)
                if os.path.isfile(trypath):
                    return trypath

        # If there's a base, return self.base.bgFile
        if self.base is not None:
            return self.base.bgFile(name, layer)

        # If not, return fallback
        return fallback

    def externalFile(self, name):
        """
        Returns the filename to the external xml.
        """
        # Name is of the format 'something.xml'
        filename = os.path.join('external', name)
        fallback = os.path.join('reggiedata', filename)

        # check if it's in self.files
        if filename in self.files:
            path = self.files[filename].path
            if os.path.isfile(path):
                return path

        # check if it's in self.folders
        if self.folders['external'].path is not None:
            path = os.path.join(self.folders['external'].path, name)
            if os.path.isfile(path):
                return path

        # No luck so far. If we have a base, use that
        if self.base is not None:
            return self.base.externalFile(name)

        # Use the fallback
        return fallback

    def GetTextureGamePath(self):
        """
        Returns the texture game path
        """
        if not self.custom:
            return setting('TextureGamePath')

        name = f'TextureGamePath_{self.name}'
        setname = setting(name)

        # Use the default if there are no settings for this yet
        if setname is None:
            return setting('TextureGamePath')
        else:
            return str(setname)

    def SetTextureGamePath(self, path: str):
        """
        Sets the texture game path
        """
        if not self.custom:
            setSetting('TextureGamePath', path)
        else:
            name = f'TextureGamePath_{self.name}'
            setSetting(name, path)

    def GetStageGamePath(self):
        """
        Returns the stage game path
        """
        if not self.custom:
            return setting('StageGamePath')

        name = f'StageGamePath_{self.name}'
        setname = setting(name)

        # Use the default if there are no settings for this yet
        if setname is None:
            return setting('StageGamePath')
        else:
            return str(setname)

    def SetStageGamePath(self, path: str):
        """
        Sets the stage game path
        """
        if not self.custom:
            setSetting('StageGamePath', path)
        else:
            name = f'StageGamePath_{self.name}'
            setSetting(name, path)

    def GetTexturePaths(self):
        """
        Returns the texture game paths of this globals_.gamedef and its bases
        """
        paths = [setting('TextureGamePath')]

        if not self.custom:
            return paths

        stg = setting(f'TextureGamePath_{self.name}')

        if self.base is not None:
            paths = self.base.GetTexturePaths()

        paths.append(stg)

        return paths

    def GetLastLevel(self):
        """
        Returns the last loaded level
        """
        if not self.custom:
            return setting('LastLevel')

        name = f'LastLevel_{self.name}'
        stg = setting(name)

        # Use the default if there are no settings for this yet
        if stg is None:
            return setting('LastLevel')

        return stg

    def SetLastLevel(self, path: str):
        """
        Sets the last loaded level
        """
        if path in {None, 'None', 'none', True, 'True', 'true', False, 'False', 'false', 0, 1, ''}:
            return

        if not self.custom:
            setSetting('LastLevel', path)
        else:
            name = f'LastLevel_{self.name}'
            setSetting(name, path)

    def recursiveFiles(self, name: str, is_folder=False):
        """
        Checks each base of this globals_.gamedef and returns a list of successive file paths
        """
        if is_folder:
            entry = self.folders[name]
        else:
            entry = self.files[name]

        if self.base is None or not entry.patch:
            # We don't have a base to fall back to, so we need to provide the
            # file ourselves.
            was_patch = False

            if entry.path is None:
                current_list = []
                names = []
            else:
                current_list = [entry.path]
                names = [self.name]

        else:
            # We do have a base to fall back to - we know that the last step
            # came from a patch, so we set 'was_patch' to True and we set 'isPatch'
            # in the recursive call to False - it doesn't matter whether the
            # previous recursive step was a patch or not.
            was_patch = True
            current_list, _, names = self.base.recursiveFiles(name, is_folder)

            if entry.path is not None:
                # We have something to add to the base
                current_list.append(entry.path)
                names.append(self.name)

        return current_list, was_patch, names

    def file(self, name: str):
        """
        Returns a file by recursively checking successive globals_.gamedef bases
        """
        if name not in self.files:
            return

        if self.files[name].path is not None:
            return self.files[name].path
        else:
            if self.base is None:
                return

            return self.base.file(name)  # It can recursively check its base, too

    def getImageClasses(self):
        """
        Gets all image classes
        """
        if not self.custom:
            return self.sprites.ImageClasses

        if self.base is not None:
            images = dict(self.base.getImageClasses())
        else:
            images = {}

        if hasattr(self.sprites, 'ImageClasses'):
            images.update(self.sprites.ImageClasses)
        return images


def getAvailableGameDefs():
    game_defs: list[tuple[str | None, str]] = []

    # Add them
    folders = os.listdir(os.path.join('reggiedata', 'patches'))
    for folder in folders:
        if not os.path.isfile(os.path.join('reggiedata', 'patches', folder, 'main.xml')):
            continue

        def_ = ReggieGameDefinition(folder)
        if def_.custom:
            game_defs.append((def_.name, folder))

    # Alphabetize them, and then add the default
    game_defs.sort()

    return [None] + [folder for _, folder in game_defs]


def loadNewGameDef(def_: str):
    """
    Loads ReggieGameDefinition def_, and displays a progress dialog
    """
    dlg = QtWidgets.QProgressDialog()
    dlg.setAutoClose(True)
    btn = QtWidgets.QPushButton('Cancel')
    btn.setEnabled(False)
    dlg.setCancelButton(btn)
    dlg.show()
    dlg.setValue(0)

    res = LoadGameDef(def_, dlg)

    dlg.setValue(100)
    return res

# Game Definitions
def LoadGameDef(name: str | None = None, dlg: QtWidgets.QProgressDialog | None = None):
    """
    Loads a game definition
    """
    if dlg:
        dlg.setMaximum(7)

    # Put the whole thing into a try-except clause
    # to catch whatever errors may happen
    try:

        # Load the globals_.gamedef
        if dlg:
            dlg.setLabelText(globals_.trans.string('Gamedefs', 1))  # Loading game patch...

        globals_.gamedef = ReggieGameDefinition(name)
        globals_.gamedef.__init2__()

        if globals_.gamedef.custom and (not globals_.settings.contains(f'StageGamePath_{globals_.gamedef.name}')):
            # First-time usage of this globals_.gamedef. Have the
            # user pick a stage folder so we can load stages
            # and tilesets from there
            pressed_button = QtWidgets.QMessageBox.information(None,
                globals_.trans.string('Gamedefs', 2),
                globals_.trans.string('Gamedefs', 3, '[game]', globals_.gamedef.name),
                QtWidgets.QMessageBox.StandardButton.Ok | QtWidgets.QMessageBox.StandardButton.Cancel
            )

            if pressed_button == QtWidgets.QMessageBox.StandardButton.Cancel:
                return False

            if globals_.mainWindow is None:
                # This check avoids an error because globals_.mainWindow is None
                # when first loading the editor. Returning False here avoids a
                # loop where the user cannot open the editor because the program
                # closes after returning the error.
                return False

            result = globals_.mainWindow.HandleChangeGamePath(True)

            if result:
                msg_ids = (6, 7)
            else:
                msg_ids = (4, 5)

            QtWidgets.QMessageBox.information(None,
                globals_.trans.string('Gamedefs', msg_ids[0]),
                globals_.trans.string('Gamedefs', msg_ids[1], '[game]', globals_.gamedef.name),
                QtWidgets.QMessageBox.StandardButton.Ok
            )

            if not result:
                # If the user refused to select a game path, abort the patch
                # switching process.
                return False

        if dlg:
            dlg.setValue(1)

        # Load spritedata.xml and spritecategories.xml
        if dlg:
            dlg.setLabelText(globals_.trans.string('Gamedefs', 8))  # Loading sprite data...

        LoadSpriteData()
        LoadSpriteCategories(True)

        # Reload all of the spritedata ID types in the area
        # Fixes bugs related to these being outdated when switching game patches
        if globals_.Area.areanum != -1:
            globals_.Area.InitialiseIdTypes()

        if globals_.mainWindow is not None:
            globals_.mainWindow.spriteViewPicker.clear()

            for cat in globals_.SpriteCategories:
                globals_.mainWindow.spriteViewPicker.addItem(cat.name)

            globals_.mainWindow.sprPicker.LoadItems()  # Reloads the sprite picker list items
            globals_.mainWindow.spriteViewPicker.setCurrentIndex(0)  # Sets the sprite picker to category 0 (enemies)
            globals_.mainWindow.spriteDataEditor.setSprite(globals_.mainWindow.spriteDataEditor.spritetype,
                                                  True)  # Reloads the sprite data editor fields

        if dlg:
            dlg.setValue(2)

        # Load BgA/BgB names
        if dlg:
            dlg.setLabelText(globals_.trans.string('Gamedefs', 9))  # Loading background names...

        LoadBgANames(True)
        LoadBgBNames(True)
        LoadZoneThemes(True)
        LoadMusicInfo(True)  # reloads the music names
        LoadConfig()

        if dlg:
            dlg.setValue(3)

        # Reload tilesets
        if dlg:
            dlg.setLabelText(globals_.trans.string('Gamedefs', 10))  # Reloading tilesets...

        LoadObjDescriptions(True)  # reloads ts1_descriptions
        if globals_.mainWindow is not None:
            globals_.mainWindow.ReloadTilesets(True)
        LoadTilesetNames(True)  # reloads tileset names
        LoadTilesetInfo(True)  # reloads tileset info

        if dlg:
            dlg.setValue(4)

        # Load sprites.py
        if dlg:
            dlg.setLabelText(globals_.trans.string('Gamedefs', 11))  # Loading sprite image data...

        # Always load the sprites folders so the correct sprite images can be
        # loaded when Reggie is started. This avoids loading all sprite images
        # again and also simplifies the sprite image code.
        SLib.SpritesFolders = globals_.gamedef.recursiveFiles('sprites', is_folder=True)[0]

        if globals_.Area.areanum != -1:
            SLib.ImageCache.clear()
            SLib.SpriteImagesLoaded.clear()
            LoadBasics()

            spriteClasses = globals_.gamedef.getImageClasses()

            for s in globals_.Area.sprites:
                if s.sprite_num in SLib.SpriteImagesLoaded:
                    continue
                if s.sprite_num not in spriteClasses:
                    continue

                spriteClasses[s.sprite_num].loadImages()

                SLib.SpriteImagesLoaded.add(s.sprite_num)

            for s in globals_.Area.sprites:
                if s.sprite_num in spriteClasses:
                    s.setImageObj(spriteClasses[s.sprite_num])
                else:
                    s.setImageObj(SLib.SpriteImage)

            # https://github.com/Zement/Reggie/blob/master/gamedef.py#L1036-L1053
            # Recalculate unknown sprite IDs based on current patch's sprite definitions
            unknown_sprite_ids = set()
            for sprite in globals_.Area.sprites:
                if sprite.sprite_num >= globals_.NumSprites or globals_.Sprites[sprite.sprite_num] is None:
                    unknown_sprite_ids.add(sprite.sprite_num)

            # Update the Area's unknown_sprite_ids
            globals_.Area.unknown_sprite_ids = unknown_sprite_ids

            # Check for unknown sprite IDs and show warning icon in status bar
            if unknown_sprite_ids:
                sprite_ids = sorted(unknown_sprite_ids)

                title = globals_.trans.string('Err_UnknownSprite', 0)
                if len(sprite_ids) == 1:
                    msg = globals_.trans.string('Err_UnknownSprite', 1, '[id]', str(sprite_ids[0]))
                else:
                    msg = globals_.trans.string('Err_UnknownSprite', 2, '[ids]', ', '.join(map(str, sprite_ids)))
                QtWidgets.QMessageBox.warning(None, title, msg)

        if dlg:
            dlg.setValue(5)

        # Reload the sprite-picker text
        if dlg:
            dlg.setLabelText(globals_.trans.string('Gamedefs', 12))  # Applying sprite image data...

        if globals_.Area.areanum != -1:
            for spr in globals_.Area.sprites:
                spr.UpdateListItem()  # Reloads the sprite-picker text

        if dlg:
            dlg.setValue(6)

        # Load entrance names
        if dlg:
            dlg.setLabelText(globals_.trans.string('Gamedefs', 16))  # Loading entrance names...

        LoadEntranceNames(True)

        if dlg:
            dlg.setValue(7)

    except Exception:
        raise

    # Success!
    if dlg:
        setSetting('LastGameDef', name)
    return True

@functools.cache
def FindGameDef(name: str, skip: str | None = None):
    """
    Helper function to find a game def with a specific name.
    Skip will be skipped
    """
    patches_path = os.path.join('reggiedata', 'patches')

    for folder in os.listdir(patches_path):
        if folder == skip:
            continue

        def_ = ReggieGameDefinition(folder)

        if def_.name != name:  # Not the one we're looking for, so stop loading.
            continue

        def_.__init2__()
        return def_


def FixSpritesModule(filename: str):
    """
    Fixes any PyQt5 -> PyQt6 incompatibilities with sprites.py modules
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            orig_data = f.read()

        # Fix the import
        new_data = orig_data.replace("PyQt5", "PyQt6")

        # Commonly used things that need to be fixed
        strings = [
            ("QPainter.Antialiasing",   "QPainter.RenderHint.Antialiasing"),
            ("Qt.SmoothTransformation", "Qt.TransformationMode.SmoothTransformation"),
            ("Qt.IgnoreAspectRatio",    "Qt.AspectRatioMode.IgnoreAspectRatio"),
            ("QPoint(",                 "QPointF("), # Skip existing instances of QPointF
            ("Qt.transparent",          "Qt.GlobalColor.transparent"),
            ("Qt.Align",                "Qt.AlignmentFlag.Align"),
        ]

        for old, new in strings:
            new_data = new_data.replace(old, new)

        with open(filename, 'w') as fileOut:
            fileOut.write(new_data)

    except Exception:
        raise
