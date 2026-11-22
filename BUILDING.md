# DISCLAIMER
- Program error reports tend to show the directory of the build location!

## Building Reggie Next

1. You need to have at least Python 3.12, so make sure to install it and add it to `PATH` on Windows.
1. Run the following command to install the required dependencies:
    ```
    pip install PyQt6 nsmblib pyinstaller
    ```
1. (Optional) You can change the version number by editing the `ReggieVersion` string in the `/src/data/globals_.py` file.
1. (Optional) You can install [UPX][https://upx.github.io/] and add it to PATH. This may decrease the size of the built executable.
1. If you're on Windows, you can run the `build_reggie.bat` script. On other platforms, you have to run the following command in the folder `build_reggie.py` is in:
    ```
    python -OO build_reggie.py
    ```

After the script finishes, the build can be found in the `distrib` folder.
