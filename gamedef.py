import os
import sys
import importlib
from xml.etree import ElementTree as etree

from PyQt5 import QtWidgets, QtCore, QtGui

from ui import GetIcon, createVertLine
from misc import LoadSpriteData, LoadSpriteListData, LoadSpriteCategories, LoadBgANames, LoadBgBNames, LoadObjDescriptions, LoadTilesetNames, LoadTilesetInfo, LoadEntranceNames
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


class GameDefSelector(QtWidgets.QWidget):
    """
    Widget which lets you pick a new game definition
    """
    gameChanged = QtCore.pyqtSignal()

    def __init__(self):
        """
        Initializes the widget
        """
        QtWidgets.QWidget.__init__(self)

        # Populate a list of globals_.gamedefs
        self.GameDefs = getAvailableGameDefs()

        # Add them to the main layout
        self.group = QtWidgets.QButtonGroup()
        self.group.setExclusive(True)
        L = QtWidgets.QGridLayout()
        row = 0
        col = 0
        current = setting('LastGameDef')

        for i, folder in enumerate(self.GameDefs):
            def_ = ReggieGameDefinition(folder)

            btn = QtWidgets.QRadioButton()
            btn.setChecked(folder == current)
            btn.toggled.connect(self.HandleRadioButtonClick)

            self.group.addButton(btn, i)

            btn.setToolTip(def_.description)

            name = QtWidgets.QLabel(def_.name)
            name.setToolTip(def_.description)

            col = (i >> 1) << 1
            L.addWidget(btn, i & 1, col)
            L.addWidget(name, i & 1, col + 1)

        self.setLayout(L)

    def HandleRadioButtonClick(self, checked):
        """
        Handles radio button clicks
        """
        if not checked: return  # this is called twice; one button is checked, another is unchecked

        loadNewGameDef(self.GameDefs[self.group.checkedId()])
        self.gameChanged.emit()


class GameDefMenu(QtWidgets.QMenu):
    """
    A menu which lets the user pick globals_.gamedefs
    """
    gameChanged = QtCore.pyqtSignal()

    def __init__(self):
        """
        Creates and initializes the menu
        """
        QtWidgets.QMenu.__init__(self)

        # Add the globals_.gamedef viewer widget
        self.currentView = GameDefViewer()
        self.currentView.setMinimumHeight(100)
        self.gameChanged.connect(self.currentView.updateLabels)

        v = QtWidgets.QWidgetAction(self)
        v.setDefaultWidget(self.currentView)
        self.addAction(v)
        self.addSeparator()

        # Add entries for each globals_.gamedef
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
        Handles the user clicking a globals_.gamedef
        """
        if not checked: return

        name = self.actGroup.checkedAction().data()
        loadNewGameDef(name)
        self.gameChanged.emit()


class ReggieGameDefinition:
    """
    A class that defines a NSMBW hack: songs, tilesets, sprites, songs, etc.
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
        self.base = None  # globals_.gamedef to use as a base
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
        if 'name' not in root.attrib: raise Exception
        self.name = root.attrib['name']

        self.description = globals_.trans.string('Gamedefs', 15)
        if 'description' in root.attrib:
            self.description = root.attrib['description'].replace('[', '<').replace(']', '>')

        self.version = root.attrib.get('version')

        del tree, root

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

            path = os.path.join(addpath, node.attrib['path'])
            patch = node.attrib.get('patch', 'true').lower() == 'true'

            if 'game' in node.attrib:
                if node.attrib['game'] != globals_.trans.string('Gamedefs', 13):  # 'New Super Mario Bros. Wii'
                    def_ = FindGameDef(node.attrib['game'], self.gamepath)
                    path = os.path.join('reggiedata', 'patches', def_.gamepath, node.attrib['path'])
                else:
                    path = os.path.join('reggiedata', node.attrib['path'])

            ListToAddTo = self.files if n == 'file' else self.folders  # self.files or self.folders
            ListToAddTo[node.attrib['name']] = self.GameDefinitionFile(path, patch)

        # Get rid of the XML stuff
        del tree, root

        # Load sprites.py if provided
        if 'sprites' in self.files:
            with open(self.files['sprites'].path, 'r') as f:
                filedata = f.read()

            # https://stackoverflow.com/questions/5362771/load-module-from-string-in-python
            # with modifications
            new_module = importlib.types.ModuleType(self.name + '->sprites')
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

    def GetGamePath(self):
        """
        Returns the game path
        """
        if not self.custom: return setting('GamePath')
        name = 'GamePath_' + self.name
        setname = setting(name)

        # Use the default if there are no settings for this yet
        if setname is None:
            return setting('GamePath')
        else:
            return str(setname)

    def SetGamePath(self, path):
        """
        Sets the game path
        """
        if not self.custom:
            setSetting('GamePath', path)
        else:
            name = 'GamePath_' + self.name
            setSetting(name, path)

    def GetGamePaths(self):
        """
        Returns game paths of this globals_.gamedef and its bases
        """
        mainpath = setting('GamePath')
        if not self.custom: return [mainpath, ]

        name = 'GamePath_' + self.name
        stg = setting(name)
        if self.base is None:
            return [mainpath, stg]
        else:
            paths = self.base.GetGamePaths()
            paths.append(stg)
            return paths

    def GetLastLevel(self):
        """
        Returns the last loaded level
        """
        if not self.custom: return setting('LastLevel')
        name = 'LastLevel_' + self.name
        stg = setting(name)

        # Use the default if there are no settings for this yet
        if stg is None:
            return setting('LastLevel')
        else:
            return stg

    def SetLastLevel(self, path):
        """
        Sets the last loaded level
        """
        if path in (None, 'None', 'none', True, 'True', 'true', False, 'False', 'false', 0, 1, ''): return
        print('Last loaded level set to ' + str(path))
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
    GameDefs = []

    # Add them
    folders = os.listdir(os.path.join('reggiedata', 'patches'))
    for folder in folders:
        if not os.path.isdir(os.path.join('reggiedata', 'patches', folder)): continue
        inFolder = os.listdir(os.path.join('reggiedata', 'patches', folder))
        if 'main.xml' not in inFolder: continue
        def_ = ReggieGameDefinition(folder)
        if def_.custom: GameDefs.append((def_, folder))

    # Alphabetize them, and then add the default
    GameDefs = sorted(GameDefs, key=lambda def_: def_[0].name)
    new = [None]
    for item in GameDefs: new.append(item[1])
    return new


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

    LoadGameDef(def_, dlg)

    dlg.setValue(100)
    del dlg

# Game Definitions
def LoadGameDef(name=None, dlg=None):
    """
    Loads a game definition
    """
    # # global globals_.gamedef
    if dlg: dlg.setMaximum(7)

    # Put the whole thing into a try-except clause
    # to catch whatever errors may happen
    try:

        # Load the globals_.gamedef
        if dlg: dlg.setLabelText(globals_.trans.string('Gamedefs', 1))  # Loading game patch...

        globals_.gamedef = ReggieGameDefinition(name)
        globals_.gamedef.__init2__()

        if globals_.gamedef.custom and (not globals_.settings.contains('GamePath_' + globals_.gamedef.name)):
            # First-time usage of this globals_.gamedef. Have the
            # user pick a stage folder so we can load stages
            # and tilesets from there
            QtWidgets.QMessageBox.information(None,
                globals_.trans.string('Gamedefs', 2),
                globals_.trans.string('Gamedefs', 3, '[game]', globals_.gamedef.name),
                QtWidgets.QMessageBox.Ok
            )

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

        if dlg: dlg.setValue(1)

        # Load spritedata.xml and spritecategories.xml
        if dlg: dlg.setLabelText(globals_.trans.string('Gamedefs', 8))  # Loading sprite data...
        LoadSpriteData()
        LoadSpriteListData(True)
        LoadSpriteCategories(True)
        if globals_.mainWindow:
            globals_.mainWindow.spriteViewPicker.clear()
            for cat in globals_.SpriteCategories:
                globals_.mainWindow.spriteViewPicker.addItem(cat[0])
            globals_.mainWindow.sprPicker.LoadItems()  # Reloads the sprite picker list items
            globals_.mainWindow.spriteViewPicker.setCurrentIndex(0)  # Sets the sprite picker to category 0 (enemies)
            globals_.mainWindow.spriteDataEditor.setSprite(globals_.mainWindow.spriteDataEditor.spritetype,
                                                  True)  # Reloads the sprite data editor fields
            globals_.mainWindow.spriteDataEditor.update()
        if dlg: dlg.setValue(2)

        # Load BgA/BgB names
        if dlg: dlg.setLabelText(globals_.trans.string('Gamedefs', 9))  # Loading background names...
        LoadBgANames(True)
        LoadBgBNames(True)
        if dlg: dlg.setValue(3)

        # Reload tilesets
        if dlg: dlg.setLabelText(globals_.trans.string('Gamedefs', 10))  # Reloading tilesets...
        LoadObjDescriptions(True)  # reloads ts1_descriptions
        if globals_.mainWindow is not None: globals_.mainWindow.ReloadTilesets(True)
        LoadTilesetNames(True)  # reloads tileset names
        LoadTilesetInfo(True)  # reloads tileset info
        if dlg: dlg.setValue(4)

        # Load sprites.py
        if dlg: dlg.setLabelText(globals_.trans.string('Gamedefs', 11))  # Loading sprite image data...
        if globals_.Area is not None:
            SLib.SpritesFolders = globals_.gamedef.recursiveFiles('sprites', False, True)

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
