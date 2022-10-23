import sys

# TODO: remove globals that are only used by 1 file

Area = None
AutoOpenScriptEnabled = False
AutoSaveData = b''
AutoSaveDirty = False
AutoSavePath = ''
BgANames = None
BgBNames = None
BgScrollRates = [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0, 0.0, 1.2, 1.5, 2.0, 4.0]
BgScrollRateStrings = None
BoundsDrawn = False
CachedGameDefs = {}
CommentsFrozen = False
CommentsShown = True
CurrentLayer = 1
CurrentLevelNameForAutoOpenScript = None
CurrentObject = -1
CurrentPaintType = 0
CurrentSprite = -1
Dirty = False
DirtyOverride = 0
DrawEntIndicators = False
EnablePadding = False
EntranceTypeNames = None
EntrancesFrozen = False
ErrMsg = ''
FileExtentions = ('.arc', '.arc.LH', '.arc.LZ')
GridType = None
HideResetSpritedata = False
InsertPathNode = False
Layer0Shown = True
Layer1Shown = True
Layer2Shown = True
Level = None
LevelNames = None
LocationsFrozen = False
LocationsShown = True
NumberFont = None
NumSprites = 0
ObjDesc = None
ObjectDefinitions = None # 4 tilesets
ObjectsFrozen = False
OverriddenTilesets = {
    "Pa0": set(),
    "no-Pa0": set(),
    "Flowers": set(),
    "Forest Flowers": set(),
    "Lines": set(),
    "Minigame Lines": set(),
    "Full Lines": set()
}
OverrideSnapping = False
Overrides = None # 320 tiles, this is put into Tiles usually
PaddingLength = 0
PathsFrozen = False
PathsShown = True
PlaceObjectsAtFullSize = True
RealViewEnabled = False
ReggieID = 'Reggie! Next Level Editor by Treeki, Tempus and RoadrunnerWMC'
ReggieVersion = 'Version 4.9.0'
ReggieVersionFloat = 4.9
ReggieVersionShort = 'v4.9.0'
ResetDataWhenHiding = False
RestoredFromAutoSave = False
SpriteCategories = None
SpriteImagesShown = True
SpriteListData = None
SpritesFrozen = False
SpritesShown = True
Sprites = None
Tiles = None # 0x200 tiles per tileset, plus 64 for each type of override
TilesetAnimTimer = None
TilesetFilesLoaded = [None, None, None, None]
TilesetInfo = None
TilesetNames = None
TilesetsAnimating = False
UpdateURL = ''

app = None
compressed = False
defaultPalette = None
defaultStyle = None
firstLoad = True
generateStringsXML = '-generatestringsxml' in sys.argv
mainWindow = None
settings = None
theme = None
ZoneThemeValues = None