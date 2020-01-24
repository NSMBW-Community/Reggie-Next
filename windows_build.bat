@echo off
echo This will work only if you've installed Python 3.5 or Newer and added it to PATH
echo You need to have cx-freeze installed in order to compile Reggie
echo Most importantly, follow this video along with it's 1st part for context: https://www.youtube.com/watch?v=CeVlC-js_t4
echo Press any key to continue or close the window to stop
pause
python windows_build.py -upx
pause
