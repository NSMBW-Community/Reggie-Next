try:
    import pyximport
    pyximport.install()

    from . import lz77_huffman_cy as lh
    from . import lz77_cy as lz77
    from . import tpl_cy as tpl

except:
    from . import lz77_huffman as lh
    from . import lz77
    from . import tpl
