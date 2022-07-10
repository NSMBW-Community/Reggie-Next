# Reggie! Level Editor Next
## The New Super Mario Bros. Wii Editor
(Milestone 4)

----------------------------------------------------------------

Advanced level editor for New Super Mario Bros. Wii originally created by Treeki, Tempus and RoadrunnerWMC using Python, PyQt and Wii.py.

"Next" version created by RoadrunnerWMC, based on official release 3. Milestone 4 version is a collaboration of Horizon users and it aims to add more features requested by users.

This release contains many improvements, in addition to code imports from the following Reggie! forks:
 * "ReggieMod 3.7.2" by JasonP27
 * "Reggie! Level Editor Mod (Newer Sprites) 3.8.1" by Kamek64 and MalStar1000
 * "NeweReggie! (Extension to Reggie! Level Editor)" by Treeki and angelsl
 * "Miyamoto!" by AboodXD
 * "Reggie Updated" by RoadrunnerWMC

Source code can be found at:
https://github.com/CLF78/Reggie-Next/

----------------------------------------------------------------

### Getting Started

If you're on Windows or Mac and don't care about having the bleeding-edge latest features, you can use the official release. This is by far the easiest setup method.

If you are not on those systems or you want the very latest features, you'll need to run Reggie! from source.


### How to Run Reggie! from Source

Download and install the following:
 * Python 3.5 (or newer) - http://www.python.org
 * PyQt 5.4.1 (or newer) - http://www.riverbankcomputing.co.uk/software/pyqt/intro

Optional dependencies:
 * MinGW (for Windows only) - http://tdm-gcc.tdragon.net
 * Cython 0.25.2 - http://cython.org
 * NSMBLib 0.4 (or newer) - https://github.com/RoadrunnerWMC/NSMBLib-Updated

Then, you can run Reggie by simply executing the following command in a command prompt.

    python3 reggie.py

You can replace `python3` with the path to your Python executable, including the executable name and `reggie.py` with the path to `reggie.py` (including the filename).

### macOS Troubleshooting

If you get the error "Reggie! Next Level Editor is damaged and can't be opened.",
it's because the release builds are unsigned. To fix it, launch a Terminal
window and run

    sudo xattr -rd com.apple.quarantine /Applications/Reggie\!\ Next\ Level\ Editor.app
    
which will override the application signature requirement. Then you should be
able to launch the app.

### Reggie! Team

Developers:
 * Treeki - Creator, Programmer, Data, RE
 * Tempus - Programmer, Graphics, Data
 * AerialX - CheerIOS, Riivolution
 * megazig - Code, Optimization, Data, RE
 * Omega - int(), Python, Testing
 * Pop006 - Sprite Images (NSMBW)
 * Tobias - Sprite Data (NSMBW), Event Example Stage
 * AboodXD - Programmer, Optimization
 * Grop - Programmer, Sprite Data (NSMBW)
 * John10v10 - Quick Paint Tool Creator
 * RoadrunnerWMC - Reggie! Next Developer: Programmer, UI, Data, Sprite Images (NSMBW), Other
 * JasonP27 - ReggieMod Developer, Programmer, UI, Sprite Images (NSMBW)
 * Kinnay (Kamek64) - Reggie! Newer Sprites Developer, Programmer, Sprite Images (NSMBW, NewerSMBW)
 * ZementBlock - Sprite Data (NSMBW)
 * MalStar1000 - Sprite Images (NSMBW, NewerSMBW), Other
 * joietyfull64 - Sprite Data (NSMBW)
 * MidiGuyDP - Background Images & Names (NewerSMBW)
 * SnakeBlock - Sprite Data (NSMBW)
 * Danster64 - Sprite Data (NSMBW, NewerSMBW), Sprite Images (NSMBW, NewerSMBW), Windows Builds

Other Testers and Contributors:
 * BulletBillTime, Dirbaio, EdgarAllen, FirePhoenix, GrandMasterJimmy, Mooseknuckle2000, MotherBrainsBrain, RainbowIE, Skawo, Sonicandtails, Tanks, Vibestar, angelsl, ant888, gamesquest1, iZackefx
 * Tobias and Valeth - Text Tileset Addon
 * Meorge and grishhung - The Reggie Next Icons (Windows and Mac)
 * Toms - Mac Builds
 * MandyIGuess, Shudfly, N-I-N-0, B1Gaming, Stage13-10, techmuse8 - Miscellaneous Contributions


### Dependencies/Libraries/Resources

 * Python 3 - Python Software Foundation (https://www.python.org)
 * Qt 5 - Nokia (http://qt.nokia.com)
 * PyQt5 - Riverbank Computing (http://www.riverbankcomputing.co.uk/software/pyqt/intro)
 * NSMBLib - NSMBLib Updated (https://github.com/RoadrunnerWMC/NSMBLib-Updated)
 * MinGW - http://www.mingw.org/
 * Cython - http://cython.org/
 * Wii.py - megazig, Xuzz, The Lemon Man, Matt_P, SquidMan, Omega (https://github.com/grp/Wii.py) (included)
 * Interface Icons - FlatIcons (http://flaticons.net)

### License

Reggie! is released under the GNU General Public License v3.
See the license file in the distribution for information.

----------------------------------------------------------------

## Changelog
Release Next (Milestone 4 and beyond): (February 2, 2020)
https://horizon.miraheze.org/wiki/Reggie_Level_Editor#Changelog

Release Next (Milestone 3 Alpha 2): (November 10, 2017)
 * Added animations rendering for ? blocks, brick blocks, dash coins and conveyors
 * Fixed last level loading
 * Fixed Newer/NewerSumSun sprite images
 * Reggie now warns the user if the LH-compressed file couldn't be decompressed
 * Added the Quick Paint Tool
 * Added a Recent Files menu
 * Fixed Pipe Enemy Generator sprite image
 * Minor bug fixes

Release Next (Milestone 3 Alpha 1): (October 7, 2017)
 * Removed New Super Mario Bros. 2 support
 * Removed PyQtRibbon
 * Removed TPLLib
 * Fixed creating new levels
 * Fixed saving
 * Fixed importing areas from another level
 * Added snapping zone to grid
 * Fixed deselecting paths
 * Added a new TPL decoder
 * Added a new LH decompressor
 * Added a new LZ77 decompressor
 * Updated the spritedata for NSMBW and NewerSMBW
 * Fixed sprite categories bug
 * Fixed painting stamps and comments
 * Re-enabled selecting patches
 * Fixed liquids, snow effect, lava particals, and fog rendering
 * Fixed/added themes
 * Fixed tileset animations
 * Minor bug fixes

Release Next (Milestone 2 Alpha 4): (unreleased)
 * Stamp preview icons are now functional
 * Added image previews to sprite, entrance, location, paths and comments lists
 * Added experimental New Super Mario Bros. 2 support
 * Bug fixes

Release Next (Milestone 2 Alpha 3): (August 5, 2014)
 * Now requires TPLLib, which is not included
 * Removed all references to NSMBLib
 * A couple of small icon changes
 * Entrance visualizations have been improved
 * The default setting for new entrances is now Non-Enterable
 * New sprite image:
   62: Spinning Firebar
 * A few bugfixes

Release Next (Milestone 2 Alpha 2): (July 31, 2014)
 * Fixed a bug that prevented the Zones dialog from working properly
 * Added some debug code to help track an elusive bug
 * Added new sprite images:
   12: Star Collectible (Newer)
   20: Goomba (Newer)
   57: Koopa (Newer)

Release Next (Milestone 2 Alpha 1): (July 30, 2014)
 * Prerequisites have changed; make sure to download the new ones!
 * New Sprite Image API fully implemented
 * Several new sprite images, and more that have been improved
 * New Bitfield editor for Rotating Bullet Bill Launcher
 * Many other new features
 * New icon set from flaticons.net

Release Next (Public Beta 1): (November 1st, 2013)
 * First beta version of Reggie! Next is finally released after a full year of work!
 * First release, may have bugs. Report any errors at the forums (link above).
 * The following sprites now render using new or updated images:
   24:  Buzzy Beetle (UPDATE)
   25:  Spiny (UPDATE)
   49:  Unused Seesaw Platform
   52:  Unused 4x Self Rotating Platforms
   55:  Unused Rising Seesaw Platform
   87:  Unused Trampoline Wall
   123: Unused Swinging Castle Platform
   125: Chain-link Koopa Horizontal (UPDATE)
   126: Chain-link Koopa Vertical (UPDATE)
   132: Beta Path-controlled Platform
   137: 3D Spiked Stake Down
   138: Water (Non-location-based only)
   139: Lava (Non-location-based only)
   140: 3D Spiked Stake Up
   141: 3D Spiked Stake Right
   142: 3D Spiked Stake Left
   145: Floating Barrel
   147: Coin (UPDATE)
   156: Red Coin Ring (UPDATE)
   157: Unused Big Breakable Brick Block
   160: Beta Path-controlled Platform
   170: Powerup in a Bubble
   174: DS One-way Gates
   175: Flying Question Block (UPDATE)
   179: Special Exit Controller
   190: Unused Tilt-controlled Girder
   191: Tile Event
   195: Huckit Crab (UPDATE)
   196: Fishbones (UPDATE)
   197: Clam (UPDATE)
   205: Giant Bubbles (UPDATE)
   206: Zoom Controller
   212: Rolling Hill (UPDATE)
   216: Poison Water (Non-location-based only)
   219: Line Block
   222: Conveyor-belt Spike
   233: Bulber (UPDATE)
   262: Poltergeist Items (UPDATE)
   268: Lava Geyser (UPDATE)
   271: Little Mouser (UPDATE)
   287: Beta Path-controlled Ice Block
   305: Lighting - Circle
   323: Boo Circle
   326: King Bill (UPDATE)
   359: Lamp (UPDATE)
   368: Path-controlled Flashlight Raft
   376: Moving Chain-link Fence (UPDATE)
   416: Invisible Mini-Mario 1-UP (UPDATE)
   417: Invisible Spin-jump coin (UPDATE)
   420: Giant Glow Block (UPDATE)
   433: Floating Question Block (UPDATE)
   447: Underwater Lamp (UPDATE)
   451: Little Mouser Despawner
 * Various bug fixes.


Release 3: (April 2nd, 2011)
 * Unicode is now supported in sprite names within spritedata.xml (thanks to 'NSMBWHack' on rvlution.net for the bug report)
 * Unicode is now supported in sprite categories.
 * Sprites 274, 354 and 356 now render using images.
 * Other various bug fixes.


Release 2: (April 2nd, 2010)
 * Bug with Python 2.5 compatibility fixed.
 * Unicode filenames and Stage folder paths should now work.
 * Changed key shortcut for "Shift Objects" to fix a conflict.
 * Fixed pasting so that whitespace/newlines won't mess up Reggie clips.
 * Fixed a crash with the Delete Zone button in levels with no zones.
 * Added an error message if an error occurs while loading a tileset.
 * Fixed W9 toad houses showing up as unused in the level list.
 * Removed integrated help viewer (should kill the QtWebKit dependency)
 * Fixed a small error when saving levels with empty blocks
 * Fixed tileset changing
 * Palette is no longer unclosable
 * Ctrl+0 now sets the zoom level to 100%
 * Path editing support added (thanks, Angel-SL)


Release 1: (March 19th, 2010)
 * Reggie! is finally released after 4 months of work and 18 test builds!
 * First release, may have bugs or incomplete sprites. Report any errors to us at the forums (link above).
