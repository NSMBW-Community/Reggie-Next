@echo off
echo This will work only if you've installed Python 3.4 in its default folder (C:\Python34\)
echo You need to have cx-freeze installed in order to compile Reggie
echo Press any key to continue or close the window to stop
pause
C:\Python34\python.exe windows_build.py
copy C:\Python34\Lib\calendar.py distrib\reggie_next_m3a2_win32\calendar.py
copy C:\Python34\Lib\locale.py distrib\reggie_next_m3a2_win32\locale.py
copy C:\Python34\Lib\posixpath.py distrib\reggie_next_m3a2_win32\posixpath.py
set bklog=%date:~6,4%-%date:~3,2%-%date:~0,2%_%time:~0,2%%time:~3,2%
move distrib\reggie_next_m3a2_win32 "distrib\reggie_next_m3a2_windows_%bklog%"
pause
