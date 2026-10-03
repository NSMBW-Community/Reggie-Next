# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added the ability to reload the patch list.
- Added a dedicated layer selector to sprites which support being on different layers.
- Added several new definitions for how a spritedata value can be manipulated.
- Added support for importing areas from LZ-compressed levels.
- The toolbar can now be toggled through a dedicated option in the "View" menu.
- Added the ability to set custom keybinds.
- Added an option to toggle the visibility of entrances.
- Added an auto-diagnostic tool that regularly checks the current level for issues.
- Added an exit indicator for forward-linking pipes.
- Added a sprite order list to help with issues caused by an incorrect level-internal sprite order.
- Added an option to forcefully ignore Windows' app scaling setting.

### Changed

- The entire codebase has been improved and restructured to help with future development.
- Bumped minimum Python version to 3.12.
- Improved level diagnostics tool.
- Updated spritedata of sprites:
  - 30, 38, 53, 55, 78, 81 - 87, 92, 93, 96, 138, 139, 152, 185, 188, 191, 195, 205, 216, 226, 243, 310, 361, 362, 368, 369, 373, 399, 414, 437, 451, 459, 461, 475
- Updated spritedata for (Newer) sprites:
  - 63, 80, 94, 113, 272, 273, 414, 441, 446, 451
- Added/updated image previews for sprites:
  - 30, 40, 41, 42, 50, 60, 62, 81-87, 105, 128, 178, 195, 202, 214, 233, 255, 256, 310, 354, 356, 425, 428
- The current zoom level is saved between sessions and used on the next startup.
- Improved the tile collision preview.
- Improved the documentation of area settings, background alignment types and the usage of specific backgrounds.
- The preferences dialog now only shows a restart warning when Reggie actually needs to be restarted.
- Minor adjustments to a few dialog windows.
- When running the source code, the application icon will now be shown properly in the taskbar on Windows.
- The level padding value is now capped at 500 KB.
- Locations can now be duplicated using Ctrl + Left Click.
- Improved randomization of specific tilesets.
- Sprite images now become translucent if their "Spawn after Midway" setting is enabled.
- Improved sprite categories and added a category dedicated to NewerSMBW's sprites.
- Reorganised a few sections in the preferences dialog.
- The toolbar will now update when edited in the preferences dialog, rather than requiring a restart.
- Replaced the "Insert new path node..." setting with a button in the Path Editor to toggle the two modes.
- When inserting nodes into an existing path, the new node will now be selected automatically.
- Improved rendering of liquids if the sprite is near the top edge or outside of a zone.
- Sprite Images that use tileset graphics now support animated tile playback.

### Removed

- Removed the Cython version from the Help menu.
- Removed unused icons.
- Removed the "advanced" attribute from spritedata.
- Removed useless / counterintuitive settings from the toolbar tab of the preferences dialog.
- `spritelib.GetImg` has been removed and replaced by `spritelib.GetImage` and `spritelib.GetPixmap` used for their respective image types.

### Fixed

- Fixed icons not loading for custom themes.
- Fixed some small issues with the sprite resizing functionality.
- Fixed inaccuracies with some of NewerSMBW's level names.
- Fixed the comment icon being smaller than intended.
- Fixed an issue where the middle mouse button would resize objects / locations.
- Fixed the "Can't find level" warning box not appearing in the taskbar.
- The entrance editor now reloads when changing game patches to accomodate for NewerSMBW-specific features.
- Fixed some small issues regarding creating new Areas without properly saving the level.
- Fixed location-based liquids rendering incorrectly if their crest texture is outside of the zone.
- Fixed some sprite images leaving artifacts when rotated.

## [4.10.0] - 2026-07-25

### Added

- Added support for copy/pasting Entrances, Locations, and Path Nodes.
- Added Conveyor Belt tile overrides (made by B1 Gaming).
- Added a toggle for Dark Mode, and rounded rectangles.
- Hovering over level items will now display drag/resize cursors.
- The spritedata now tells the user about all archive files that sprite uses.

### Changed

- Improved spritedata.
- Added/updated image previews for sprites:
  - 23, 31, 43-45, 50, 51, 56, 59, 65-76, 92, 97, 103, 104, 106, 108, 113, 122, 123, 136, 138, 143, 148, 156, 160, 166, 174-176, 178, 188, 193, 194, 203, 204, 219, 230, 233, 247, 262-264, 266, 267, 274, 285, 289, 291, 292, 303, 314-316, 318, 327, 331, 335, 338, 341, 361, 365, 368, 382, 391, 395, 396, 401, 404, 405, 411, 412, 418, 420, 424, 425, 431-433, 438, 455, 457, 478
- Added/updated image previews for (Newer) sprites:
  - 13, 18, 43, 44, 45, 167, 188, 203, 210, 230, 291, 292, 320, 341, 351, 391, 405, 410, 433
- Toggling Layer 0 will display the inside of the Giant Koopa Shell Cave sprite.
- Overhauled the Sprite Resizer Dialog to make it more user-friendly.
- Stage folders no longer require 01-01.arc to be considered valid.
- Duplicating a zone will now copy over its background data.
- Various improvements to the UI of several dialog windows.

### Removed

- Removed the "Add Reggie Patch Folder" feature.

### Fixed

- Other miscellaneous bug fixes and improvements.

## [4.9.0] - 2026-04-19

### Added

- Added better support for translations.
- Added button in the Zone Options to duplicate the current zone.
- Added a few new icons to the UI.
	
### Changed

- Updated to PyQt6.
- Improved spritedata and sprite image previews.
- Improved background preview names (they now describe their in-game usage).
- Levels with unknown sprite IDs can now be loaded in the editor.

### Fixed

- Fixed level corruption issues introduced in 4.8.0.
- Other miscellaneous bug fixes.

## [4.8.0] - 2022-06-06

### Added

- Added support for loading Stage and Texture folders in Game Patches separately. First it checks if <Stage>/Texture is a folder, and if not, it lets the user select the Tilesets folder manually.
- Added an option to visualize Camera Bounds for Zones.
- Implemented saving levels as .arc.LZ files.

### Changed

- Improved spritedata.
- Pa0 overrides now automatically apply to all Tilesets starting with "Pa0_". Adding `override="no-Pa0"` to a Pa0 tileset will disable this behavior.
- The camera now automatically scrolls when dragging items near the screen edge.
- Made CTRL + Scroll zoom in/out to the cursor's position.
- Added/updated images for sprites 53, 111, 112, 138, 139, 216, 311.

### Removed

- Removed the AnotherSMBW, NewerHS and NewerSumSun Game Patches.

### Fixed

- Other miscellaneous bug fixes.

## [4.7.0] - 2021-11-29

### Added

- Added a "Change Layer" button for tiles.
- Added the "Send to Worldmap" and "Spawn half a tile left" settings for Entrances.

### Changed

- Improved spritedata.
- Updated Reggie Next icons for both Windows and Mac (credit to Meorge and grishhung).
- Implemented LZ-compressed level support from Reggie Updated.
- Updated the Sound Modulation names to correspond to the respective level they're used with from the original game.
- Changed the format spritedata.xml's use to refer to bits, as proposed by RoadrunnerWMC.
- Reworked Paths to allow changing the Path and Path Node IDs.
- Changed the default Area timer to 500.
- Added/updated images for sprites 101, 212, 231, 262, 277, 278, 299, 325, 452.

### Fixed

- Other miscellaneous bug fixes.

## [4.6.0] - 2021-09-20

### Added

- Added a "Next Free" button for easily selecting new values at a given ID input.
- Added dialogue in the Area settings configure loaded sprite resources.
- Added a Newer-friendly version of the Training Level, and made the custom tilesets use their own file name.
- Added an option to place Objects at their full size (immediately).
- Added a more alarming Invalid Tile image.

### Changed

- Improved spritedata.
- Further optimized the editor, and improved LH decompression.
- Made the editor load a blank canvas if 01-01 couldn't be found after switching Game Patches.
- Updated the Zone settings.
- Made newly created Zones have the standard BG scroll rates set by default.
- Removed the HUD from all Background previews, and added all missing ones (huge thanks to Stage13-10).
- Improved accuracy of the Level Overview window.
- Updated the selection line of items.
- Improved grid.
- Items will now only be placed into the level when they are set to be visible.
- Reworked the screenshot button. It can now hide the editor canvas.
- The Current Spritelist now updates regularly, can be sorted by sprite ID, and lists all values for IDs if a sprite has multiple.
- Removed most instances of trailing whitespaces on images.
- Made Liquids visually draw to Locations.
- Updated the blue pipe sprite image (Thanks to to B1 Gaming), and images for sprites 40-43, 50, 53, 64, 113, 138, 139, 176, 188, 205, 216, 226, 274, 286, 345, 358, 376, 428, 438, 466, 467, 475, 482.
- Added/updated Newer sprite images/recolors for sprites 19, 26, 57, 58, 60, 105, 230, 296, 302, 414.

### Fixed

- Fixed Newer Bush sprite image error.
- Fixed crashes that occur when the Pa0 tileset isn't selected/found.
- Fixed the positioning of sprites when saved. Before they were slightly offset by their images, which caused issues most notably with rail-controlled sprites.
- Fixed issue of images from game patches not loading in time.
- Fixed previewing themes in Reggie Preferences.
- Other miscellaneous bug fixes.

## [4.5.1] - 2021-04-23

### Added

- Added support for high DPI displays.

### Changed

- Improved spritedata.

### Fixed

- Fixed Move-When-On platform sprite image crashing error.
- Fixed invisible animated tiles issue.
- Other miscellaneous bug fixes.

## [4.5.0] - 2021-04-15

### Changed

- Improved spritedata, and modified window for Sprite Settings.
- Significantly improved loading times (including adding support for nsmblib).
- Implemented support for editing Camera Profiles.
- Made Zones and Locations snap to the 8x8 grid when resized by default (unless Alt is held).
- Updated screenshot feature.
- Removed NewerGEM game patch.
- Added/updated images for sprites 52, 110, 138, 139, 156, 216, 435.

### Fixed

- Repaired AnotherSMBW's and NewerSumSun's game patch.
- Other miscellaneous bug fixes.

## [4.4.0] - 2021-02-12

### Changed

- Improved spritedata.
- Revamped the Zone settings (from Reggie! Updated).
- Fixed bugs related to saving.
- Added/updated images for the overrides, block items, and sprites 21, 46, 95, 113, 192, 193, 194, 262, 263, 308, 338, 349, 364, 365, 372, 375, 381, 383, 407.
- Added/updated Newer sprite images/recolors for sprite 40, 42, 46, 95, 308, 320, 322.

### Removed

- Removed the set max number of sprites that can be listed in the spritedata.

### Fixed

- Many small miscellaneous bug fixes (some from Reggie! Updated).

## [4.3.0] - 2020-11-23

### Added

- Added a new LH Decompressor, which should now properly decompress all files.
- Added support for sprites with multiple IDs in the Current Spritelist.
- Added a sprite image for sprite 406.
- Added Newer sprite images/recolors for sprite 88, 89.

### Changed

- Improved spritedata.
- The editor now properly changes folders when ran from a new location.
- Updated the scripts for building Reggie.

### Fixed

- Fixed/updated sprite images for sprites 40-42, 478, 103, 106, 122, 194, 405.

## [4.2.0] - 2020-09-25

### Added

- Added sprite images for sprites 373, 398, 400, 401, 404, 480.
- Added Newer sprite images/recolors for sprite 105.
- Implemented middle-click-drag scrolling from Reggie Updated.

### Changed

- Improved spritedata.
- Restored the Newer Holiday Special game patch's spritedata.
- Made the initial state of events 33-64 editable.
- Allowed saving for levels with entrances and no Zones.

### Removed

- Removed the Quick Paint Tool.

### Fixed

- Fixed the background setting's saving issue.
- Fixed rendering unknown tiles.
- Fixed bug related to selecting unassigned Zone lighting settings.
- Fixed bugs with resizing multiple tiles at once.
- Bug fixes related to Path nodes.
- Separate windows no longer spawn at the top-left corner.
- Fixed/updated sprite images for sprites 137, 140-142, 305.
- Other miscellaneous bug fixes.

## [4.1.0] - 2020-03-09

### Added

- Added sprite image for sprite 53.
- Added Newer recolors for sprites 43, 45, 123, 219, 286, 311, 357, 387, 414.

### Changed

- Revamped Current Sprites tab.
- Improved spritedata.

### Fixed

- Many bugfixes.

## [4.0.0] - 2020-02-04

### Added

- Added tileset randomization rendering.
- Added override support for custom tilesets.
- Added Newer recolors for sprites 21, 24-26, 30, 47, 58, 60, 63, 78, 81-86, 101, 145, 153, 195, 198, 199, 223, 230, 231, 261, 269, 296, 341, 391, 478, 479.
- Added sprite images for sprites 52, 192, 211, 328, 349, 364, 365, 372, 375, 381, 405, 418, 431, 458, 460, 462, 463, 472, 473, 480-482 and Newer-exclusive sprites 17, 18, 167, 168, 244, 250, 251.
- Added a path visiblity toggle.
- Added option to pad level files.
- Added support for window style and color customization.
- Added reload spritedata option.
- Added some missing icons.
- Added exception handler.

### Changed

- Revamped sprite editor widget and spritedata format.
- Revamped object resizer.
- Changed default location size to 16x16.

### Removed

- Removed the island generator and the old tileset picker.
- Removed the broken updater.
- Removed the splash screen.

### Fixed

- Fixed several bugs that would cause the level to be marked as unsaved.
- Fixed many sprite images.
- Fixed sprite positioning bugs.
- Fixed sprite searching and set Search as default category.
- Fixed adding new areas.
- Fixed location merging.
- Fixed the Quick Paint and Level Diagnostic Tools.
- Fixed default events.
- Fixed preference resetting bug.
- Fixed libpng warnings.

## [3.2.0] - 2017-11-10

### Added

- Added the Quick Paint Tool.
- Added animation rendering for blocks, dash coins and conveyors.
- Added a Recent Files menu.
- Added warning for LH decompression failure.

### Fixed

- Fixed last level loading.
- Fixed sprite 99 image and Newer/NewerSumSun sprite images.
- Other minor bug fixes.

## [3.1.0] - 2017-10-07

### Added

- Added a new TPL decoder, LH and LZ77 decompressors.
- Added snapping Zone to grid.

### Changed

- Updated spritedata.

### Removed

- Removed NSMB2 support and ribbon.

### Fixed

- Fixed creating new levels.
- Fixed saving.
- Fixed importing areas from another level.
- Fixed deselecting paths.
- Fixed sprite categories.
- Fixed painting stamps and comments.
- Fixed real view.
- Fixed themes.
- Fixed tileset animations.
- Other minor bug fixes.

## [2.4.0] - unreleased

### Added

- Added NSMB2 support.
- Added newly-found Area settings.
- Added support for Newer's any-tileset-slot hack.
- Added rendering for nonexistent tiles.
- Added previews for list elements.
- Added stamp rendering, saving, opening and renaming.
- Added undo feature.
- Added Save Copy As button.
- Added sprite image for sprite 149.

### Changed

- Revamped splash screen and logo.
- Changed default Zone position.
- Changed element rendering order.
- Made Zone entrance line optional.

### Removed

- Removed minimum Zone size limit.

## [2.3.0] - 2014-08-05

### Added

- Added sprite image for sprite 62.

### Changed

- Replaced NSMBLib with TPLLib.
- Improved entrance visualizations and changed default setting to non-enterable.

### Fixed

- Fixed new level saving bug.
- Fixed sprite image toggle.

## [2.2.0] - 2014-08-01

### Added

- Added sprite images for the Newer-exclusive sprite 12, and recolors for sprites 20, 57.

## [2.1.0] - 2014-07-31

### Added

- Added tileset animation and collision rendering.
- Added real view.
- Added autosave feature.
- Added comments and stamps.
- Added support for multiple object resizing.
- Added Zone entrance marker.
- Added entrance indicator for door sprites and bitfield editor for sprite 136.
- Added sprite images for sprites 9, 147, 257, 260, 261, 411, 412.
- Added Newer recolors for sprites 157, 188.
- Added Python and PyQt version checks.

### Changed

- Revamped sprite API.
- Replaced icon set.
- Moved default events from Area settings to the Palette.
- Moved sprite list to the sprite tab.

### Fixed

- Fixed sprite 110 crash.

## [1.0.0] - 2013-11-01

### Added

- Added custom theme, translation and game patch support.
- Added the Level Diagnostic Tool.
- Added Zone darkness and looped path rendering.
- Added Zone preset option.
- Added show sprite images toggle.
- Added details about current selection and zoom slider.
- Added preferences menu.
- Added ribbon.
- Added sprite images for sprites
  - 49, 52, 55, 87, 123, 132, 137-142, 145, 157, 160, 170, 179, 190, 191, 206, 216, 219, 222, 287, 305, 323, 368, 451

### Changed

- Revamped tileset picker and background settings.
- Updated several sprite images.
