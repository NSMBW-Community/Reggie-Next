import os
import sys
import importlib
from xml.etree import ElementTree as etree

from PyQt5 import QtWidgets, QtCore, QtGui

from ui import GetIcon, createVertLine
from misc import LoadSpriteData, LoadSpriteListData, LoadSpriteCategories, LoadBgANames, LoadBgBNames, LoadObjDescriptions, LoadTilesetNames, LoadTilesetInfo, LoadEntranceNames, LoadZoneThemes
from dirty import setting, setSetting

import globals_
import spritelib as SLib
import sprites

class GameDefViewer(QtWidgets.QWidget):
    """
    Widget which displays basic info about the current game definition
    """

    def __init__(self):
        """
        Initializes the widget
        """
        QtWidgets.QWidget.__init__(self)
        self.imgLabel = QtWidgets.QLabel()
        self.imgLabel.setToolTip(globals_.trans.string('Gamedefs', 0))
        self.imgLabel.setPixmap(GetIcon('sprites', False).pixmap(16, 16))
        self.versionLabel = QtWidgets.QLabel()
        self.titleLabel = QtWidgets.QLabel()
        self.descLabel = QtWidgets.QLabel()
        self.descLabel.setWordWrap(True)
        self.descLabel.setMinimumHeight(40)

        # Make layouts
        left = QtWidgets.QVBoxLayout()
        left.addWidget(self.imgLabel)
        left.addWidget(self.versionLabel)
        left.addStretch(1)
        right = QtWidgets.QVBoxLayout()
        right.addWidget(self.titleLabel)
        right.addWidget(self.descLabel)
        right.addStretch(1)
        main = QtWidgets.QHBoxLayout()
        main.addLayout(left)
        main.addWidget(createVertLine())
        main.addLayout(right)
        main.setStretch(2, 1)
        self.setLayout(main)
        self.setMaximumWidth(256 + 64)

        self.updateLabels()

    def updateLabels(self):
        """
        Updates all labels
        """
        empty = QtGui.QPixmap(16, 16)
        empty.fill(QtGui.QColor(0, 0, 0, 0))
        img = GetIcon('sprites', False).pixmap(16, 16) if (
        (globals_.gamedef.recursiveFiles('sprites', False, True) != []) or (not globals_.gamedef.custom)) else empty
        ver = '' if globals_.gamedef.version is None else '<i><p style="font-size:10px;">v' + str(globals_.gamedef.version) + '</p></i>'
        title = '<b>' + str(globals_.gamedef.name) + '</b>'
        desc = str(globals_.gamedef.description)

        self.imgLabel.setPixmap(img)
        self.versionLabel.setText(ver)
        self.titleLabel.setText(title)
        self.descLabel.setText(desc)


class GameDefMenu(QtWidgets.QMenu):
    """
    A menu which lets the user pick gamedefs
    """
    gameChanged = QtCore.pyqtSignal()
    update_flag = False

    def __init__(self):
        """
        Creates and initializes the menu
        """
        QtWidgets.QMenu.__init__(self)

        # Add the gamedef viewer widget
        self.currentView = GameDefViewer()
        self.currentView.setMinimumHeight(100)
        self.gameChanged.connect(self.currentView.updateLabels)

        v = QtWidgets.QWidgetAction(self)
        v.setDefaultWidget(self.currentView)
        self.addAction(v)
        self.addSeparator()

        # Add entries for each gamedef
        self.GameDefs = getAvailableGameDefs()

        self.actGroup = QtWidgets.QActionGroup(self)
        loadedDef = setting('LastGameDef')
        for folder in self.GameDefs:
            def_ = ReggieGameDefinition(folder)

            act = QtWidgets.QAction(self)
            act.setText(def_.name)
            act.setToolTip(def_.description)
            act.setData(folder)
            act.setActionGroup(self.actGroup)
            act.setCheckable(True)
            act.setChecked(folder == loadedDef)
            act.toggled.connect(self.handleGameDefClicked)

            self.addAction(act)

    def handleGameDefClicked(self, checked):
        """
        Handles the user clicking a gamedef
        """
        if not checked or self.update_flag: return

        name = self.actGroup.checkedAction().data()
        success = loadNewGameDef(name)
        if success:
            self.gameChanged.emit()
            return

        # Setting the new gamedef failed for some reason, so load back the old
        # game def.
        real_gamedef = setting('LastGameDef')
        success = loadNewGameDef(real_gamedef)
        if not success:
            raise Exception("Restoring the previous game def (%r) failed after failing to load new game def (%r)" % (real_gamedef, name))

        self.update_flag = True
        for act in self.actGroup.actions():
            act.setChecked(act.data() == real_gamedef)
        self.update_flag = False


class ReggieGameDefinition:
    """
    A class that defines a NSMBW hack: songs, tilesets, sprites, etc.
    """

    # Gamedef File - has 2 values: name (str) and patch (bool)
    class GameDefinitionFile:
        """
        A class that defines a filepath, and some options
        """

        def __init__(self, path, patch):
            """
            Initializes the GameDefinitionFile
            """
            self.path = path
            self.patch = patch

    def __init__(self, name=None):
        """
        Initializes the ReggieGameDefinition
        """
        self.InitAsEmpty()

        # Try to init it from name if possible
        NoneTypes = (None, 'None', 0, '', True, False)
        if name in NoneTypes:
            return

        try:
            self.InitFromName(name)
        except Exception:
            self.InitAsEmpty()
            raise

    def InitAsEmpty(self):
        """
        Sets all properties to their default values
        """
        gdf = self.GameDefinitionFile

        self.custom = False
        self.base = None  # gamedef to use as a base
        self.gamepath = None
        self.name = globals_.trans.string('Gamedefs', 13)  # 'New Super Mario Bros. Wii'
        self.description = globals_.trans.string('Gamedefs', 14)  # 'A new Mario adventure!<br>' and the date
        self.version = '2'

        self.sprites = sprites

        self.files = {
            'bga': gdf(None, False),
            'bgb': gdf(None, False),
            'entrancetypes': gdf(None, False),
            'levelnames': gdf(None, False),
            'music': gdf(None, False),
            'spritecategories': gdf(None, False),
            'spritedata': gdf(None, False),
            'spritelistdata': gdf(None, False),
            'spritenames': gdf(None, False),
            'tilesets': gdf(None, False),
            'tilesetinfo': gdf(None, False),
            'ts1_descriptions': gdf(None, False),
            'zonethemes': gdf(None, False),
        }
        self.folders = {
            'bga': gdf(None, False),
            'bgb': gdf(None, False),
            'sprites': gdf(None, False),
            'external': gdf(None, False),
        }

    def InitFromName(self, name):
        """
        Attempts to open/load a Game Definition from a name string. Just loads
        the name and description to avoid referring to other game definitions.
        """
        self.custom = True
        name = str(name)
        self.gamepath = name

        # Parse the file (errors are handled by __init__())
        path = os.path.join("reggiedata", "patches", name, "main.xml")
        tree = etree.parse(path)
        root = tree.getroot()

        # Add the attributes of root: name, description and version.
        # base is added in __init2__, only when needed.
        self.name = root.get('name')

        if self.name is None:
            raise ValueError("Game definition XML %r has no 'name' attribute on the root node." % path)

        default = globals_.trans.string('Gamedefs', 15)
        self.description = root.get('description', default).replace('[', '<').replace(']', '>')
        self.version = root.get('version')

    def __init2__(self):
        """
        Finishes up initialisation of custom gamedefs. This avoids infinite
        recursion with gamedefs referring to other gamedefs.
        """
        if not self.custom:
            return

        path = os.path.join("reggiedata", "patches", self.gamepath, "main.xml")
        tree = etree.parse(path)
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

            game = node.get('game')
            if game is None:
                path = os.path.join(addpath, node.get('path'))
            elif game == globals_.trans.string('Gamedefs', 13):  # 'New Super Mario Bros. Wii'
                path = os.path.join('reggiedata', node.get('path'))
            else:
                def_ = FindGameDef(game, self.gamepath)
                path = os.path.join('reggiedata', 'patches', def_.gamepath, node.get('path'))

            dict_type = self.files if n == 'file' else self.folders  # self.files or self.folders
            dict_type[node.get('name')] = self.GameDefinitionFile(path, patch)

        # Get rid of the XML stuff
        del tree, root

        # Load sprites.py if provided
        if 'sprites' in self.files:
            with open(self.files['sprites'].path, 'r') as f:
                filedata = f.read()

            # https://stackoverflow.com/a/53080237 with modifications
            spec = importlib.util.spec_from_loader(self.name + "->sprites", loader=None)
            new_module = importlib.util.module_from_spec(spec)

            exec(filedata, new_module.__dict__)
            sys.modules[new_module.__name__] = new_module
            self.sprites = new_module

    def bgFile(self, name, layer):
        """
        Returns the folder to a bg image. Layer must be 'a' or 'b'
        """
        # Name will be of the format '0000.png'
        fallback = os.path.join('reggiedata', 'bg' + layer, name)
        filename = 'bg%s/%s' % (layer, name)

        # See if it was defined specifically
        if filename in self.files:
            path = self.files[filename].path
            if os.path.isfile(path): return path

        # See if it's in one of self.folders
        if self.folders['bg%s' % layer].path is not None:
            trypath = self.folders['bg%s' % layer].path + '/' + name
            if os.path.isfile(trypath): return trypath

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

        name = 'TextureGamePath_' + self.name
        setname = setting(name)

        # Use the default if there are no settings for this yet
        if setname is None:
            return setting('TextureGamePath')
        else:
            return str(setname)

    def SetTextureGamePath(self, path):
        """
        Sets the texture game path
        """
        if not self.custom:
            setSetting('TextureGamePath', path)
        else:
            name = 'TextureGamePath_' + self.name
            setSetting(name, path)

    def GetStageGamePath(self):
        """
        Returns the stage game path
        """
        if not self.custom:
            return setting('StageGamePath')

        name = 'StageGamePath_' + self.name
        setname = setting(name)

        # Use the default if there are no settings for this yet
        if setname is None:
            return setting('StageGamePath')
        else:
            return str(setname)

    def SetStageGamePath(self, path):
        """
        Sets the stage game path
        """
        if not self.custom:
            setSetting('StageGamePath', path)
        else:
            name = 'StageGamePath_' + self.name
            setSetting(name, path)

    def GetTexturePaths(self):
        """
        Returns the texture game paths of this globals_.gamedef and its bases
        """
        paths = [setting('TextureGamePath')]

        if not self.custom:
            return paths

        stg = setting('TextureGamePath_' + self.name)

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

        name = 'LastLevel_' + self.name
        stg = setting(name)

        # Use the default if there are no settings for this yet
        if stg is None:
            return setting('LastLevel')

        return stg

    def SetLastLevel(self, path):
        """
        Sets the last loaded level
        """
        if path in {None, 'None', 'none', True, 'True', 'true', False, 'False', 'false', 0, 1, ''}:
            return

        if not self.custom:
            setSetting('LastLevel', path)
        else:
            name = 'LastLevel_' + self.name
            setSetting(name, path)

    def recursiveFiles(self, name, isPatch=False, folder=False):
        """
        Checks each base of this globals_.gamedef and returns a list of successive file paths
        """
        ListToCheckIn = self.files if not folder else self.folders

        # This can be handled 4 ways: if we do or don't have a base, and if we do or don't have a copy of the file.
        if self.base is None:
            if ListToCheckIn[name].path is None:  # No base, no file

                if isPatch:
                    return [], True
                else:
                    return []

            else:  # No base, file

                alist = []
                alist.append(ListToCheckIn[name].path)
                if isPatch:
                    return alist, ListToCheckIn[name].patch
                else:
                    return alist

        else:

            if isPatch:
                listUpToNow, wasPatch = self.base.recursiveFiles(name, True, folder)
            else:
                listUpToNow = self.base.recursiveFiles(name, False, folder)

            if ListToCheckIn[name].path is None:  # Base, no file

                if isPatch:
                    return listUpToNow, wasPatch
                else:
                    return listUpToNow

            else:  # Base, file

                # If it's a patch, just add it to the end of the list
                if ListToCheckIn[name].patch:
                    listUpToNow.append(ListToCheckIn[name].path)

                # If it's not (it's free-standing), make a new list and start over
                else:
                    newlist = []
                    newlist.append(ListToCheckIn[name].path)
                    if isPatch:
                        return newlist, False
                    else:
                        return newlist

                # Return
                if isPatch:
                    return listUpToNow, wasPatch
                else:
                    return listUpToNow

    def multipleRecursiveFiles(self, *args):
        """
        Returns multiple recursive files in order of least recent to most recent as a list of tuples, one list per globals_.gamedef base
        """

        # This should be very simple
        # Each arg should be a file name
        if self.base is None:
            main = []  # start a new level
        else:
            main = self.base.multipleRecursiveFiles(*args)

        # Add the values from this level, and then return it
        result = []
        for name in args:
            try:
                file = self.files[name]
                if file.path is None: raise KeyError
                result.append(self.files[name])
            except KeyError:
                result.append(None)
        main.append(tuple(result))
        return main

    def file(self, name):
        """
        Returns a file by recursively checking successive globals_.gamedef bases
        """
        if name not in self.files: return

        if self.files[name].path is not None:
            return self.files[name].path
        else:
            if self.base is None: return
            return self.base.file(name)  # it can recursively check its base, too

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
    game_defs = []

    # Add them
    folders = os.listdir(os.path.join('reggiedata', 'patches'))
    for folder in folders:
        if not os.path.isfile(os.path.join('reggiedata', 'patches', folder, 'main.xml')): continue

        def_ = ReggieGameDefinition(folder)
        if def_.custom:
            game_defs.append((def_.name, folder))

    # Alphabetize them, and then add the default
    game_defs.sort()

    return [None] + [folder for _, folder in game_defs]


def loadNewGameDef(def_):
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
def LoadGameDef(name=None, dlg=None):
    """
    Loads a game definition
    """
    if dlg: dlg.setMaximum(7)

    # Put the whole thing into a try-except clause
    # to catch whatever errors may happen
    try:

        # Load the globals_.gamedef
        if dlg: dlg.setLabelText(globals_.trans.string('Gamedefs', 1))  # Loading game patch...

        globals_.gamedef = ReggieGameDefinition(name)
        globals_.gamedef.__init2__()

        if globals_.gamedef.custom and (not globals_.settings.contains('StageGamePath_' + globals_.gamedef.name)):
            # First-time usage of this globals_.gamedef. Have the
            # user pick a stage folder so we can load stages
            # and tilesets from there
            pressed_button = QtWidgets.QMessageBox.information(None,
                globals_.trans.string('Gamedefs', 2),
                globals_.trans.string('Gamedefs', 3, '[game]', globals_.gamedef.name),
                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
            )

            if pressed_button == QtWidgets.QMessageBox.Cancel:
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
                QtWidgets.QMessageBox.Ok
            )

            if not result:
                # If the user refused to select a game path, abort the patch
                # switching process.
                return False

        if dlg: dlg.setValue(1)

        # Load spritedata.xml and spritecategories.xml
        if dlg: dlg.setLabelText(globals_.trans.string('Gamedefs', 8))  # Loading sprite data...

        LoadSpriteData()
        LoadSpriteListData(True)
        LoadSpriteCategories(True)

        if globals_.mainWindow is not None:
            globals_.mainWindow.spriteViewPicker.clear()

            for cat in globals_.SpriteCategories:
                globals_.mainWindow.spriteViewPicker.addItem(cat[0])

            globals_.mainWindow.sprPicker.LoadItems()  # Reloads the sprite picker list items
            globals_.mainWindow.spriteViewPicker.setCurrentIndex(0)  # Sets the sprite picker to category 0 (enemies)
            globals_.mainWindow.spriteDataEditor.setSprite(globals_.mainWindow.spriteDataEditor.spritetype,
                                                  True)  # Reloads the sprite data editor fields

        if dlg: dlg.setValue(2)

        # Load BgA/BgB names
        if dlg: dlg.setLabelText(globals_.trans.string('Gamedefs', 9))  # Loading background names...

        LoadBgANames(True)
        LoadBgBNames(True)
        if globals_.gamedef.recursiveFiles('zonethemes', True)[0]:
            LoadZoneThemes(True)
        else:
            globals_.ZoneThemeValues = globals_.trans.stringList('ZonesDlg', 1)

        if dlg: dlg.setValue(3)

        # Reload tilesets
        if dlg: dlg.setLabelText(globals_.trans.string('Gamedefs', 10))  # Reloading tilesets...

        LoadObjDescriptions(True)  # reloads ts1_descriptions
        if globals_.mainWindow is not None:
            globals_.mainWindow.ReloadTilesets(True)
        LoadTilesetNames(True)  # reloads tileset names
        LoadTilesetInfo(True)  # reloads tileset info

        if dlg: dlg.setValue(4)

        # Load sprites.py
        if dlg: dlg.setLabelText(globals_.trans.string('Gamedefs', 11))  # Loading sprite image data...

        # Always load the sprites folders so the correct sprite images can be
        # loaded when Reggie is started. This avoids loading all sprite images
        # again and also simplifies the sprite image code.
        SLib.SpritesFolders = globals_.gamedef.recursiveFiles('sprites', False, True)

        if globals_.Area is not None:
            SLib.ImageCache.clear()
            SLib.SpriteImagesLoaded.clear()
            sprites.LoadBasics()

            spriteClasses = globals_.gamedef.getImageClasses()

            for s in globals_.Area.sprites:
                if s.type in SLib.SpriteImagesLoaded: continue
                if s.type not in spriteClasses: continue

                spriteClasses[s.type].loadImages()

                SLib.SpriteImagesLoaded.add(s.type)

            for s in globals_.Area.sprites:
                if s.type in spriteClasses:
                    s.setImageObj(spriteClasses[s.type])
                else:
                    s.setImageObj(SLib.SpriteImage)

        if dlg: dlg.setValue(5)

        # Reload the sprite-picker text
        if dlg: dlg.setLabelText(globals_.trans.string('Gamedefs', 12))  # Applying sprite image data...
        if globals_.Area is not None:
            for spr in globals_.Area.sprites:
                spr.UpdateListItem()  # Reloads the sprite-picker text
        if dlg: dlg.setValue(6)

        # Load entrance names
        if dlg: dlg.setLabelText(globals_.trans.string('Gamedefs', 16))  # Loading entrance names...
        LoadEntranceNames(True)
        if dlg: dlg.setValue(7)

    except Exception:
        raise
    #    # Something went wrong.
    #    if dlg: dlg.setValue(7) # autocloses it
    #    QtWidgets.QMessageBox.information(None, globals_.trans.string('Gamedefs', 17), globals_.trans.string('Gamedefs', 18, '[error]', str(e)))
    #    if name is not None: LoadGameDef(None)
    #    return False


    # Success!
    if dlg: setSetting('LastGameDef', name)
    return True

def FindGameDef(name, skip=None):
    """
    Helper function to find a game def with a specific name.
    Skip will be skipped
    """
    if name in globals_.CachedGameDefs:
        return globals_.CachedGameDefs[name]

    patches_path = os.path.join('reggiedata', 'patches')

    for folder in os.listdir(patches_path):
        if folder == skip:
            continue

        def_ = ReggieGameDefinition(folder)

        if def_.name != name:  # Not the one we're looking for, so stop loading.
            continue

        def_.__init2__()
        globals_.CachedGameDefs[def_.name] = def_
        return def_
