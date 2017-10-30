#!/usr/bin/python
# -*- coding: latin-1 -*-

# Reggie Next - New Super Mario Bros. Wii Level Editor
# Milestone 3
# Copyright (C) 2009-2014 Treeki, Tempus, angelsl, JasonP27, Kamek64,
# MalStar1000, RoadrunnerWMC, 2017 Stella/AboodXD, John10v10

# This file is part of Reggie Next.

# Reggie Next is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Reggie Next is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Reggie Next.  If not, see <http://www.gnu.org/licenses/>.


# tpl_cy.pyx
# TPL image data decoder in Cython.


################################################################
################################################################

cpdef bytes decodeRGB4A3(data, int width, int height):
    cdef bytearray result = bytearray(width * height * 4)

    cdef int i, yTile, xTile, y, x
    cdef int pixel, r, g, b, a, pos

    i = 0

    for yTile in range(0, height, 4):
        for xTile in range(0, width, 4):
            for y in range(yTile, yTile + 4):
                for x in range(xTile, xTile + 4):
                    pixel = (data[i] << 8) | data[i+1]

                    if pixel & 0x8000:
                        r = (pixel & 0x1F) * 255 // 0x1F
                        g = ((pixel >> 5) & 0x1F) * 255 // 0x1F
                        b = ((pixel >> 10) & 0x1F) * 255 // 0x1F
                        a = 0xFF

                    else:
                        r = (pixel & 0xF) * 255 // 0xF
                        g = ((pixel & 0xF0) >> 4) * 255 // 0xF
                        b = ((pixel & 0xF00) >> 8) * 255 // 0xF
                        a = ((pixel & 0x7000) >> 12) * 255 // 0x7

                    pos = (y * width + x) * 4

                    # works but slow
                    ## result[pos:pos + 4] = ((r << 24) | (g << 16) | (b << 8) | a).to_bytes(4, "big")

                    result[pos] = r
                    result[pos + 1] = g
                    result[pos + 2] = b
                    result[pos + 3] = a

                    i += 2 

    return bytes(result)
