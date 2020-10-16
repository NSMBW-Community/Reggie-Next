@echo off
echo Building should only require Python, PyInstaller, Cython, and PyQt5.
echo Having upx added to PATH can help reduce the size.
echo Finally, follow this guide to essentially pre-compile Cython:
echo https://www.youtube.com/watch?v=CeVlC-js_t4
echo
echo HUGE credit to RoadrunnerWMC for his building script as base.
echo Older PyInstaller command line:
echo pyinstaller --upx-dir=/path/to/upx --windowed -y --onefile reggie.py
python -OO build_reggie.py
pause