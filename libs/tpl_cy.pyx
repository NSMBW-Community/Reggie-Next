#!/usr/bin/env python3
#cython: language_level=3
# -*- coding: utf-8 -*-

# Reggie Next - New Super Mario Bros. Wii Level Editor
# Milestone 4
# Copyright (C) 2009-2020 Treeki, Tempus, angelsl, JasonP27, Kamek64,
# MalStar1000, RoadrunnerWMC, AboodXD, John10v10, TheGrop, CLF78,
# Zementblock, Danster64

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
# Based on decoder from Reggie Updated.


################################################################
################################################################

from cpython cimport array
from cython cimport view
from libc.stdint cimport int32_t
from libc.stdint cimport uint8_t, uint16_t, uint32_t
from libc.stdlib cimport malloc, free

ctypedef  uint8_t u8
ctypedef uint16_t u16
ctypedef  int32_t s32
ctypedef uint32_t u32


cdef u32 RGB4A3LUT[0x10000]
cdef u32 RGB4A3LUT_NoAlpha[0x10000]


cdef inline void PrepareRGB4A3LUT(u32 LUT[], s32 hasA):
    cdef u16 d
    cdef u8 red, green, blue, alpha

    # RGB4A3
    for d in range(0x8000):
        if hasA:
            alpha = <u8>(d >> 12)
            alpha = alpha << 5 | alpha << 2 | alpha >> 1
        else:
            alpha = 0xFF
        red = <u8>((d >> 8) & 0xF) * 17
        green = <u8>((d >> 4) & 0xF) * 17
        blue = <u8>(d & 0xF) * 17
        LUT[d] = blue | (<u32>green << 8) | (<u32>red << 16) | (<u32>alpha << 24)

    # RGB555
    for d in range(0x8000):
        red = <u8>(d >> 10)
        red = red << 3 | red >> 2
        green = <u8>((d >> 5) & 0x1F)
        green = green << 3 | green >> 2
        blue = <u8>(d & 0x1F)
        blue = blue << 3 | blue >> 2
        LUT[d + 0x8000] = blue | (<u32>green << 8) | (<u32>red << 16) | 0xFF000000U


cdef void PrepareRGB4A3LUTs():
    PrepareRGB4A3LUT(RGB4A3LUT, True)
    PrepareRGB4A3LUT(RGB4A3LUT_NoAlpha, False)

PrepareRGB4A3LUTs()


# '_src' must be RGB4A3 raw data
cpdef bytes decodeRGB4A3(_src, u32 width, u32 height, s32 noAlpha):
    cdef:
        array.array srcArr = array.array('B', _src)
        const u8* src = srcArr.data.as_uchars

        u32* dst = <u32*>malloc(width * height * 4)

        u32 i, yTile, xTile, y, x
        u32* LUT

    if noAlpha:
        LUT = RGB4A3LUT_NoAlpha
    else:
        LUT = RGB4A3LUT

    i = 0
    for yTile in range(0, height, 4):
        for xTile in range(0, width, 4):
            for y in range(yTile, yTile + 4U):
                for x in range(xTile, xTile + 4U):
                    dst[y * width + x] = LUT[(<u16>src[i] << 8) | src[i+1]]
                    i += 2 

    try:
        return bytes(<u8[:width * height * 4]>(<u8*>dst))

    finally:
        free(dst)
