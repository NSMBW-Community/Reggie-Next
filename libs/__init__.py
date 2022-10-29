# Check the dependency for loading level files. The fastest option is nsmblib,
# but if the user does not have that installed, we fall back to a Cython
# implementation. If the user also does not have that installed, we have a slow
# pure Python implementation.

try:
    import nsmblib
    has_nsmblib = True
except ModuleNotFoundError:
    has_nsmblib = False

try:
    import pyximport
    pyximport.install()
    has_cython = True
except ModuleNotFoundError:
    has_cython = False

# Now use whether we have nsmblib and/or cython to do the actual imports.

lib_versions = {
    "cython": None,
    "nsmblib": None,
    "nsmblib-updated": None,
}

if has_nsmblib:
    # We need to convert the API of tpl.py and lz77.py to the API of nsmblib, so
    # we need to change some function names.
    import types
    lz77 = types.SimpleNamespace()
    lz77.UncompressLZ77 = nsmblib.decompress11LZS
    lz77.CompressLZ77 = nsmblib.compress11LZS

    # nsmblib does not support decoding tileset images that are not a full
    # tileset. Reggie Next uses the "decodeRGB4A3" function for decoding tile
    # animations as well, which are a lot smaller. Thus, we need a non-nsmblib
    # fallback if the size of the image is not a full image.
    if has_cython:
        from . import tpl_cy as _tpl
    else:
        from . import tpl as _tpl

    def handler(data, width, height, no_alpha):
        if width == 1024 and height == 256:
            if no_alpha:
                rgbdata = nsmblib.decodeTilesetNoAlpha(data)
            else:
                rgbdata = nsmblib.decodeTileset(data)
        return _tpl.decodeRGB4A3(data, width, height, no_alpha)

    tpl = types.SimpleNamespace()
    tpl.decodeRGB4A3 = handler

    lib_versions["nsmblib"] = nsmblib.getVersion()

    # NSMBLib Updated 2021.10.14.1 adds a new function that keeps track of the
    # Updated version
    if hasattr(nsmblib, 'getUpdatedVersion'):
        lib_versions["nsmblib-updated"] = nsmblib.getUpdatedVersion()

    del types

elif has_cython:
    from . import lz77 as lz77_py
    from . import lz77_cy as lz77
    from . import tpl_cy as tpl

    # Fall back to python, since cython does not have this implemented
    lz77.CompressLZ77 = lz77_py.CompressLZ77

else:
    from . import lz77
    from . import tpl

# For LH decompression, only cython or pure python can be used, so pick the best
# available.
if has_cython:
    from . import lz77_huffman_cy as lh

    import Cython
    lib_versions["cython"] = Cython.__version__
    del Cython
else:
    from . import lz77_huffman as lh
