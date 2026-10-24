#!/usr/bin/python
# -*- coding: latin-1 -*-

# Reggie! - New Super Mario Bros. Wii Level Editor
# Copyright (C) 2009-2010 Treeki, Tempus


# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import json
import os, os.path
import shutil
import sys

import PyInstaller.__main__


########################################################################
############################### Constants ##############################
########################################################################

# Everything highly specific to Reggie is in this section, to make it
# simpler to copypaste this script across all of the NSMBW-related
# projects that use the same technologies (Reggie, Puzzle, BRFNTify,
# etc)

PROJECT_NAME = 'Reggie! Next'
FULL_PROJECT_NAME = 'Reggie! Next Level Editor'
PROJECT_VERSION = '5.0.0'

WIN_ICON = os.path.join('reggiedata', 'win_icon.ico')
MAC_ICON = os.path.join('reggiedata', 'reggie.icns')
MAC_BUNDLE_IDENTIFIER = 'ca.chronometry.reggie'

SCRIPT_PATH = 'src/reggie.py'
SCRIPT_FILE = SCRIPT_PATH[4:-3] # Drops 'src/' and the .py extension
DATA_FOLDERS = ['reggiedata', 'reggieextras']
DATA_FILES = ['README.md', 'CHANGELOG.md', 'license.txt']

# macOS only
AUTO_APP_BUNDLE_NAME = f'{SCRIPT_FILE}.app'
FINAL_APP_BUNDLE_NAME = f'{FULL_PROJECT_NAME}.app'


########################################################################
################################# Intro ################################
########################################################################

if sys.platform == 'win32':
    platform = 'windows'
elif sys.platform == 'darwin':
    platform = 'macos'
else:
    platform = sys.platform

DIR = os.path.join('distrib', f'reggie_next_v{PROJECT_VERSION}_{platform}')
WORKPATH = 'build_temp'
SPECFILE = f'{SCRIPT_FILE}.spec'

def print_emphasis(s):
    print('>>')
    print(f'>> {'=' * (len(s) - 3)}')
    print(s)
    print(f'>> {'=' * (len(s) - 3)}')
    print('>>')

print(f'[[ Building {PROJECT_NAME} ]]')
print('>> Please note: extra command-line arguments passed to this script will be passed through to PyInstaller.')
print(f'>> Destination directory: {DIR}')

# Remove any leftovers from previous build(s)
if os.path.isdir(DIR):
    shutil.rmtree(DIR)

if os.path.isdir(WORKPATH):
    shutil.rmtree(WORKPATH)

if os.path.isdir(SPECFILE):
    os.remove(SPECFILE)

def run_pyinstaller(args):
    print('>>')
    print_msg = ['>> Running PyInstaller with the following arguments:']
    for a in args:
        if ' ' in a:
            print_msg.append(f'"{a}"')
        else:
            print_msg.append(a)

    print(' '.join(print_msg))
    print('>>')

    PyInstaller.__main__.run(args)


########################################################################
######################### Environment detection ########################
########################################################################
print('>>')
print('>> Detecting environment...')
print('>>')

# Python optimization level
if sys.flags.optimize == 2:
    print('>>   [X] Python optimization level is -OO')
else:
    print('>>   [ ] Python optimization level is -OO')

# NSMBLib being installed
try:
    import nsmblib
    print('>>   [X] NSMBLib is installed')
except ImportError:
    nsmblib = None
    print('>>   [ ] NSMBLib is installed')

# UPX being installed
# There seems to be no reliable way to determine in this script if
# PyInstaller will detect UPX or not. PyInstaller itself provides no
# public API for this, and doing horrible things with its private API
# didn't ultimately work well enough to be useful.


# Now show big warning messages if any of those failed
if sys.flags.optimize < 2:
    msg = 'without' if sys.flags.optimize == 0 else 'with only one level of'
    print_emphasis(f'>> WARNING: Python is being run {msg} optimizations enabled! Please consider building with -OO.')

if nsmblib is None:
    print_emphasis('>> WARNING: NSMBLib does not seem to be installed! Please consider installing it prior to building.')

print_emphasis('>> NOTE: If the PyInstaller output below says "INFO: UPX is not available.", you should install UPX!')


########################################################################
######################### Excludes and Includes ########################
########################################################################
print('>>')
print('>> Populating excludes and includes...')
print('>>')

# Excludes
excludes = ['doctest', 'pdb', 'unittest', 'difflib',
            'os2emxpath', 'optpath', 'multiprocessing', 'ssl',
            'PyQt6.QtWebKit', 'PyQt6.QtNetwork']

if sys.platform == 'nt':
    excludes.append('posixpath')

# Add excludes for other Qt modules
qt_exclude = ['Designer', 'Network', 'OpenGL', 'Qml', 'Script', 'Sql', 'Test', 'WebKit', 'Xml']
qt_require = ['Core', 'Gui', 'Widgets']

# Exclude all the stuff we don't use
for name in qt_exclude:
    excludes.append(f'PyQt6.Qt{name}')

# Includes
includes = ['pkgutil']

# Binary excludes
excludes_binaries = []
if sys.platform == 'win32':
    excludes_binaries = [
        # Qt stuff
        'Qt6Network.dll', 'Qt6Qml.dll', 'Qt6QmlModels.dll',
        'Qt6Quick.dll', 'Qt6WebSockets.dll',
        # Other stuff
        'opengl32sw.dll',
        'd3dcompiler_',  # currently (2020-09-25) "d3dcompiler_47.dll",
                         # but that'll probably change eventually, so we
                         # just exclude anything that starts with this
                         # substring
    ]

elif sys.platform == 'darwin':
    # Sadly, we can't exclude anything on macOS -- it just crashes. :(
    # If a workaround could be found, here's the list we'd use:
    # excludes_binaries = [
    #     # Qt stuff (none of these have any file extensions at all)
    #     'QtNetwork', 'QtPrintSupport', 'QtQml', 'QtQmlModels',
    #     'QtQuick', 'QtWebSockets',
    # ]
    pass

elif sys.platform == 'linux':
    excludes_binaries = [
        # Qt stuff
        # Currently (2020-09-25) these all end with ".so.5", but that
        # may change, so we exclude anything that starts with these
        # substrings
        'libQt6Network.so', 'libQt6Qml.so', 'libQt6QmlModels.so',
        'libQt6Quick.so', 'libQt6WebSockets.so',
        # Other stuff
        'libgtk-3.so',
    ]


print(f'>> Will use the following excludes list: {', '.join(excludes)}')
print(f'>> Will use the following includes list: {', '.join(includes)}')
print(f'>> Will use the following binaries excludes list: {', '.join(excludes_binaries)}')


########################################################################
################### Running PyInstaller (first time) ###################
########################################################################

# Our only goal here is to create a specfile we can edit. Unfortunately,
# there's no good way to do that without doing a full PyInstaller
# build...

args = [
    '--windowed',
    '--onefile',
    '--upx-exclude=vcruntime140.dll',
    f'--distpath={DIR}',
    f'--workpath={WORKPATH}',
]

if sys.platform == 'win32':
    args.append(f'--icon={os.path.abspath(WIN_ICON)}')
elif sys.platform == 'darwin':
    args.append(f'--icon={os.path.abspath(MAC_ICON)}')
    args.append(f'--osx-bundle-identifier={MAC_BUNDLE_IDENTIFIER}')

for e in excludes:
    args.append(f'--exclude-module={e}')

for i in includes:
    args.append(f'--hidden-import={i}')

args.extend(sys.argv[1:])
args.append(SCRIPT_PATH)

run_pyinstaller(args)

shutil.rmtree(DIR)
shutil.rmtree(WORKPATH)


########################################################################
########################## Adjusting specfile ##########################
########################################################################
print('>> Adjusting specfile...')

# New plist file data (if on Mac)
info_plist = {
    'CFBundleName': PROJECT_NAME,
    'CFBundleDisplayName': FULL_PROJECT_NAME,
    'CFBundleShortVersionString': PROJECT_VERSION,
    'CFBundleGetInfoString': f'{FULL_PROJECT_NAME} {PROJECT_VERSION}',
    'CFBundleExecutable': SCRIPT_FILE,
}

# Open original specfile
with open(SPECFILE, 'r', encoding='utf-8') as f:
    lines = f.read().splitlines()

# Iterate over its lines, and potentially add new ones
new_lines = []
insert_info_plist = False
for line in lines:
    if 'PYZ(' in line and excludes_binaries:
        new_lines.append(f'EXCLUDES = {repr(excludes_binaries)}')
        new_lines.append('new_binaries = []')
        new_lines.append('for x, y, z in a.binaries:')
        new_lines.append('    for e in EXCLUDES:')
        new_lines.append('        if x.startswith(e):')
        new_lines.append('            print(f"specfile: excluding {x}")')
        new_lines.append('            break')
        new_lines.append('    else:')
        new_lines.append('        new_binaries.append((x, y, z))')
        new_lines.append('a.binaries = new_binaries')

    new_lines.append(line)

    if insert_info_plist:
        new_lines.append(f'    info_plist={json.dumps(info_plist)},')
        insert_info_plist = False

    if sys.platform == 'darwin' and 'BUNDLE(' in line:
        # We cannot insert the info_plist keyword argument now, as the next
        # argument is not a keyword argument. As such, we set a flag to add it
        # after the next line.
        insert_info_plist = True

# Save new specfile
with open(SPECFILE, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))



########################################################################
################### Running PyInstaller (second time) ##################
########################################################################

# Most of the arguments are now contained in the specfile. Thus, we can
# run with minimal arguments this time.

args = [
    f'--distpath={DIR}',
    f'--workpath={WORKPATH}',
    SPECFILE,
]

run_pyinstaller(args)

shutil.rmtree(WORKPATH)
os.remove(SPECFILE)


########################################################################
######################## Copying required files ########################
########################################################################
print('>> Copying required files...')

if sys.platform == 'darwin':
    dest_folder = os.path.join(DIR, AUTO_APP_BUNDLE_NAME, 'Contents', 'Resources')
else:
    dest_folder = DIR

for f in DATA_FOLDERS:
    if os.path.isdir(os.path.join(dest_folder, f)):
        shutil.rmtree(os.path.join(dest_folder, f))
    shutil.copytree(f, os.path.join(dest_folder, f))

for f in DATA_FILES:
    shutil.copy(f, dest_folder)


########################################################################
################################ Cleanup ###############################
########################################################################
print('>> Cleaning up...')

# On macOS, there's a second "reggie" executable for some reason,
# separate from the app bundle. I don't know why it's there, but we
# delete it.

if sys.platform == 'darwin':
    leftover_executable = os.path.join(DIR, SCRIPT_FILE.split('.')[0])
    if os.path.isfile(leftover_executable):
        os.unlink(leftover_executable)

# Also on macOS, we have to rename the .app folder to the display name
# because CFBundleDisplayName is dumb and doesn't actually affect
# the app name shown in Finder
if sys.platform == 'darwin':
    os.rename(os.path.join(DIR, AUTO_APP_BUNDLE_NAME), os.path.join(DIR, FINAL_APP_BUNDLE_NAME))


########################################################################
################################## End #################################
########################################################################
print(f'>> {PROJECT_NAME} has been built to the {DIR} folder!')
