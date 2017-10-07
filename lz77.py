#!/usr/bin/python
# -*- coding: latin-1 -*-

# Reggie Next - New Super Mario Bros. Wii Level Editor
# Milestone 3
# Copyright (C) 2009-2014 Treeki, Tempus, angelsl, JasonP27, Kamek64,
# MalStar1000, RoadrunnerWMC, 2017 Stella/AboodXD

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


# lz77.py
# LZ77 decompressor in Python.


################################################################
################################################################

def GetUncompressedSize(inData):
    offset = 4
    outSize = inData[1] | (inData[2] << 8) | (inData[3] << 16)

    if not outSize:
        outSize = inData[4] | (inData[5] << 8) | (inData[6] << 16) | (inData[7] << 24)
        offset += 4

    return outSize, offset


def UncompressLZ77(inData):
    if inData[0] != 0x11:
        return inData

    outLength, offset = GetUncompressedSize(inData)
    outData = bytearray(outLength)
    
    outIndex = 0

    while outIndex < outLength and offset < len(inData):
        flags = inData[offset]
        offset += 1

        for x in reversed(range(8)):
            if outIndex >= outLength or offset >= len(inData):
                break

            if flags & (1 << x):
                first = inData[offset]
                offset += 1

                second = inData[offset]
                offset += 1

                if first < 32:
                    third = inData[offset]
                    offset += 1

                    if first >= 16:
                        fourth = inData[offset]
                        offset += 1

                        pos = (((third & 0xF) << 8) | fourth) + 1
                        copylen = ((second << 4) | ((first & 0xF) << 12) | (third >> 4)) + 273

                    else:
                        pos = (((second & 0xF) << 8) | third) + 1
                        copylen = (((first & 0xF) << 4) | (second >> 4)) + 17

                else:
                    pos = (((first & 0xF) << 8) | second) + 1
                    copylen = (first >> 4) + 1

                for y in range(copylen):
                    outData[outIndex + y] = outData[outIndex - pos + y]

                outIndex += copylen

            else:
                outData[outIndex] = inData[offset]
                offset += 1
                outIndex += 1

    return bytes(outData)
