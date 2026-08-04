from collections import OrderedDict
from typing import Literal

from PyQt6 import QtCore, QtGui, QtWidgets

from classlib import MenuAction, SpriteCategory
from gamedef import ReggieGameDefinition
from level import AbstractLevel
from level import Area as AreaType
from misc import SpriteDefinition
from reggie import ReggieWindow
from tiles import ObjectDef, TilesetTile
from translation import ReggieTranslation
from ui import ReggieTheme

Area: AreaType = AreaType.DummyArea()
AutoSaveData = b''
AutoSaveDirty = False
AutoSavePath = ''
BgANames: list[str] = []
BgBNames: list[str] = []
BoundsDrawn = False
CollisionsShown = False
CommentsFrozen = False
CommentsShown = True
CurrentLayer = 1
CurrentObject = -1
CurrentPaintType = 0
CurrentSprite = -1
Dirty = False
DirtyOverride = 0
DrawEntIndicators = False
EditActions: tuple[MenuAction, ...] = ()
EnablePadding = False
EntranceTypeNames: OrderedDict[int, str] | None = None
EntrancesFrozen = False
ErrMsg = ''
FileActions: tuple[MenuAction, ...] = ()
FileExtentions = ('.arc', '.arc.LH', '.arc.LZ')
GridType: Literal['grid', 'checker'] | None = None
HideResetSpritedata = False
HelpActions: tuple[MenuAction, ...] = ()
Initializing = False
InsertPathNode = False
Layer0Shown = True
Layer1Shown = True
Layer2Shown = True
Level: AbstractLevel # Uninitialized on purpose. It's never accessed before being written to. Reduces redudant "is None" checks.
LevelNames: tuple[str, ...] = ()
LocationsFrozen = False
LocationsShown = True
MusicInfo: dict[str, str] = {}
NumberFont: QtGui.QFont | None = None
NumSprites = 0
ObjDesc: dict[int, str] = {}
ObjectDefinitions: tuple[ObjectDef, ObjectDef, ObjectDef, ObjectDef] = (ObjectDef(), ObjectDef(), ObjectDef(), ObjectDef()) # 4 tilesets
ObjectsFrozen = False
OverriddenTilesets: dict[str, set[str]] = {
    "Pa0": set(),
    "no-Pa0": set(),
    "Flowers": set(),
    "Forest Flowers": set(),
    "Lines": set(),
    "Minigame Lines": set(),
    "Full Lines": set(),
    "Conveyors": set()
}
OverrideSnapping = False
Overrides: list[TilesetTile] = [] # 320 tiles, this is put into Tiles usually
Overrides_safe: list[TilesetTile] = []
OVERRIDE_UNKNOWN = 0
PaddingLength = 0
PathsFrozen = False
PathsShown = True
PlaceObjectsAtFullSize = True
RealViewEnabled = False
ReggieID = 'Reggie! Next Level Editor by Treeki, Tempus and RoadrunnerWMC'
ReggieVersionFloat = 4.11
ReggieVersionShort = 'v4.11.0'
ResetDataWhenHiding = False
RestoredFromAutoSave = False
SettingsActions: tuple[MenuAction, ...] = ()
SpriteCategories: list[SpriteCategory] = []
SpriteImagesShown = True
SpriteListData: list[list[int]] = []
SpritesFrozen = False
SpritesShown = True
Sprites: list[SpriteDefinition] = []
Tiles: dict[int, TilesetTile] = {} # 0x200 tiles per tileset, plus 64 for each type of override
TilesetAnimTimer: QtCore.QTimer | None = None
TilesetFilesLoaded: tuple[str | None, str | None, str | None, str | None] = (None, None, None, None)
TilesetInfo: dict[str, dict[int, tuple[int, int, int]]] = {}
TilesetNames: list = [] # TODO: add proper typing later. I don't even know what is happening here
TilesetsAnimating = False
ViewActions: tuple[MenuAction, ...] = ()
ZoneThemeValues: list[str] = []
UseRoundedRectangles = True
DarkMode = False
UseFullFilepath = False
FirstStageFilename: str | None = None
CursorMode = 0

FileKeybinds: dict[str, tuple[QtCore.QKeyCombination | str | None]]
EditKeybinds: dict[str, tuple[QtCore.QKeyCombination | str | None]]
ViewKeybinds: dict[str, tuple[QtCore.QKeyCombination | str | None]]
SettingsKeybinds: dict[str, tuple[QtCore.QKeyCombination | str | None]]
HelpKeybinds: dict[str, tuple[QtCore.QKeyCombination | str | None]]

# Config settings
DispConnectedPipeDir = False
SpecialEventSpriteID = 0
AllowSizeHacks = False

app: QtWidgets.QApplication | None = None
firstLoad = True
trans: ReggieTranslation = ReggieTranslation('UNDEFINED')
gamedef: ReggieGameDefinition = ReggieGameDefinition()
mainWindow: ReggieWindow | None = None
# uninitialized
settings: QtCore.QSettings
theme: ReggieTheme
