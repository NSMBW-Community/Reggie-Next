from level import Area as AreaType
from tiles import TilesetTile, ObjectDef

Area: AreaType | None = None
AutoSaveData = b''
AutoSaveDirty = False
AutoSavePath = ''
BgANames = None
BgBNames = None
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
EditActions = None
EnablePadding = False
EntranceTypeNames = None
EntrancesFrozen = False
ErrMsg = ''
FileActions = None
FileExtentions = ('.arc', '.arc.LH', '.arc.LZ')
GridType = None
HideResetSpritedata = False
HelpActions = None
Initializing = None
InsertPathNode = False
Layer0Shown = True
Layer1Shown = True
Layer2Shown = True
Level = None
LevelNames = None
LocationsFrozen = False
LocationsShown = True
MusicInfo = None
NumberFont = None
NumSprites = 0
ObjDesc = None
ObjectDefinitions: list[ObjectDef] # 4 tilesets
ObjectsFrozen = False
OverriddenTilesets = {
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
SettingsActions = None
SpriteCategories = None
SpriteImagesShown = True
SpriteListData = None
SpritesFrozen = False
SpritesShown = True
Sprites = None
Tiles: dict[int, TilesetTile] = {} # 0x200 tiles per tileset, plus 64 for each type of override
TilesetAnimTimer = None
TilesetFilesLoaded: [str, str, str, str]
TilesetInfo = None
TilesetNames = None
TilesetsAnimating = False
ViewActions = None
ZoneThemeValues = None
UseRoundedRectangles = True
DarkMode = False
UseFullFilepath = False
FirstStageFilename = None
CursorMode = 0

FileKeybinds: dict
EditKeybinds: dict 
ViewKeybinds: dict
SettingsKeybinds: dict
HelpKeybinds: dict

# Config settings
DispConnectedPipeDir = False
SpecialEventSpriteID = 0
AllowSizeHacks = False

app = None
firstLoad = True
gamedef = None
mainWindow = None
settings = None
theme = None
trans = None
