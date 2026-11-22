#!/usr/bin/python
# -*- coding: latin-1 -*-

# Reggie Next - New Super Mario Bros. Wii Level Editor
# Milestone 5 - See license_short.txt for more details.

# tpl.py
# TPL image data encoder and decoder in Python.
# Based on decoder from Reggie Updated.

################################################################
################################################################

import struct


RGB4A3LUT         = [0 for _ in range(0x10000)]
RGB4A3LUT_NoAlpha = [0 for _ in range(0x10000)]


def PrepareRGB4A3LUTs():
    global RGB4A3LUT, RGB4A3LUT_NoAlpha

    for LUT, hasA in [(RGB4A3LUT, True), (RGB4A3LUT_NoAlpha, False)]:
        # RGB4A3
        for d in range(0x8000):
            if hasA:
                alpha = d >> 12
                alpha = alpha << 5 | alpha << 2 | alpha >> 1
            else:
                alpha = 0xFF
            red = ((d >> 8) & 0xF) * 17
            green = ((d >> 4) & 0xF) * 17
            blue = (d & 0xF) * 17
            LUT[d] = blue | (green << 8) | (red << 16) | (alpha << 24)

        # RGB555
        for d in range(0x8000):
            red = d >> 10
            red = red << 3 | red >> 2
            green = (d >> 5) & 0x1F
            green = green << 3 | green >> 2
            blue = d & 0x1F
            blue = blue << 3 | blue >> 2
            LUT[d + 0x8000] = blue | (green << 8) | (red << 16) | 0xFF000000

PrepareRGB4A3LUTs()


# 'src' must be RGB4A3 raw data
def decodeRGB4A3(src, width, height, noAlpha):
    dst = bytearray(width * height * 4)
    LUT = RGB4A3LUT_NoAlpha if noAlpha else RGB4A3LUT
    pack_into = struct.pack_into

    i = 0
    for yTile in range(0, height, 4):
        for xTile in range(0, width, 4):
            for y in range(yTile, yTile + 4):
                for x in range(xTile, xTile + 4):
                    pack_into("<I", dst, (y * width + x) * 4, LUT[(src[i] << 8) | src[i+1]])

                    i += 2 

    return bytes(dst)
