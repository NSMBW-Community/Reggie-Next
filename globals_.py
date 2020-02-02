import sys

# TODO: remove globals that are only used by 1 file

AltSettingIcons = False
Area = None
AutoOpenScriptEnabled = False
AutoSaveData = b''
AutoSaveDirty = False
AutoSavePath = ''
BgANames = None
BgBNames = None
BgScrollRates = None
BgScrollRateStrings = None
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
FileExtentions = ('.arc', '.arc.LH')
GridType = None
HideResetSpritedata = False
Layer0Shown = True
Layer1Shown = True
Layer2Shown = True
LevelNames = None
LocationsFrozen = False
LocationsShown = True
NumberFont = None
ObjDesc = None
ObjectDefinitions = None # 4 tilesets
ObjectsFrozen = False
OverriddenTilesets = {
    "Pa0": set(),
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
RealViewEnabled = False
ReggieID = 'Reggie Next Level Editor by Treeki, Tempus and RoadrunnerWMC'
ReggieVersion = 'Milestone 4'
ReggieVersionFloat = 4.0
ReggieVersionShort = 'M4'
ResetDataWhenHiding = False
RestoredFromAutoSave = False
SpriteCategories = None
SpriteImagesShown = True
SpriteListData = None
SpritesFrozen = False
SpritesShown = True
Sprites = []
TileBehaviours = None
Tiles = None # 0x200 tiles per tileset, plus 64 for each type of override
TilesetAnimTimer = None
TilesetFilesLoaded = [None, None, None, None]
TilesetInfo = None
TilesetNames = None
TilesetsAnimating = False
UpdateURL = ''

app = None
arcname = ''
compressed = False
cython_available = False
defaultPalette = None
defaultStyle = None
firstLoad = True
generateStringsXML = '-generatestringsxml' in sys.argv
mainWindow = None
settings = None
theme = None