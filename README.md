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
https://github.com/NSMBW-Community/Reggie-Next/

----------------------------------------------------------------

### Getting Started

If you're on Windows or Mac and don't care about having the bleeding-edge latest features, you can use the official release. This is by far the easiest setup method.

If you are not on those systems or you want the very latest features, you'll need to run Reggie! from source.


### How to Run Reggie! from Source

Download and install the following:
 * Python 3.12 (or newer) - http://www.python.org
 * PyQt 6.9 (or newer) - http://www.riverbankcomputing.co.uk/software/pyqt/intro

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
 * RoadrunnerWMC - Reggie! Next Developer: Programmer, UI, Data, Sprite Images (NSMBW), Other
 * JasonP27 - ReggieMod Developer, Programmer, UI, Sprite Images (NSMBW)
 * Kinnay (Kamek64) - Reggie! Newer Sprites Developer, Programmer, Sprite Images
 * ZementBlock - Sprite Data (NSMBW)
 * MalStar1000 - Sprite Images, Other
 * joietyfull64 - Sprite Data (NSMBW)
 * MidiGuyDP - (Old) Background Images & Names (NewerSMBW)
 * SnakeBlock - Sprite Data (NSMBW)
 * Danster64 - Sprite Data, Sprite Images, Windows Builds
 * MandyIGuess - Programmer, UI, Sprite Data, Sprite Images, Background Names, Data, RE, Other QoL improvements
 * B1 Gaming - Sprite Data, Sprite Images, Data / Docs, Other QoL improvements

Other Testers and Contributors:
 * BulletBillTime, Dirbaio, EdgarAllen, FirePhoenix, GrandMasterJimmy, Mooseknuckle2000, MotherBrainsBrain, RainbowIE, Skawo, Sonicandtails, Tanks, Vibestar, angelsl, ant888, gamesquest1, iZackefx
 * Tobias and Valeth - Text Tileset Addon
 * Meorge and grishhung - The Reggie Next Icons (Windows and Mac)
 * Toms - Mac Builds
 * Stage13-10 - Background Images
 * Shudfly, N-I-N-0, techmuse8 - Miscellaneous Contributions


### Dependencies/Libraries/Resources

 * Python 3 - Python Software Foundation (https://www.python.org)
 * Qt 6 - Nokia (http://qt.nokia.com)
 * PyQt6 - Riverbank Computing (http://www.riverbankcomputing.co.uk/software/pyqt/intro)
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

A full changelog can be found here: https://horizon.miraheze.org/wiki/Reggie_Level_Editor#Changelog
