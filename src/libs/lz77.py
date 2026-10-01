#!/usr/bin/python
# -*- coding: latin-1 -*-

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

    inLength = len(inData)
    outLength, offset = GetUncompressedSize(inData)
    outData = bytearray(outLength)

    outIndex = 0

    while outIndex < outLength and offset < inLength:
        flags = inData[offset]
        offset += 1

        for x in reversed(range(8)):
            if outIndex >= outLength or offset >= inLength:
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

def CompressLZ77(inData):
    dcsize = len(inData)
    cbuffer = bytearray()

    src = 0
    dest = 4

    if dcsize > 0xFFFFFF:
        return None

    cbuffer.append(0x11)
    cbuffer.append(dcsize & 0xFF)
    cbuffer.append((dcsize >> 8) & 0xFF)
    cbuffer.append((dcsize >> 16) & 0xFF)

    flagrange = [7, 6, 5, 4, 3, 2, 1, 0]

    while src < dcsize:
        flag = 0
        flagpos = dest
        cbuffer.append(flag)
        dest += 1

        for i in flagrange:
            matchOffs, matchLen = CompressionSearch(inData, src, dcsize, 0x1000, 0xFFFF + 273)
            if matchLen > 0:
                flag |= (1 << i)

                matchOffsM1 = matchOffs - 1
                if matchLen <= 0x10:
                    cbuffer.append((((matchLen - 1) & 0xF) << 4) | ((matchOffsM1 >> 8) & 0xF))
                    cbuffer.append(matchOffsM1 & 0xFF)
                    dest += 2
                elif matchLen <= 0x110:
                    matchLenM17 = matchLen - 17
                    cbuffer.append((matchLenM17 & 0xFF) >> 4)
                    cbuffer.append(((matchLenM17 & 0xF) << 4) | ((matchOffsM1 & 0xFFF) >> 8))
                    cbuffer.append(matchOffsM1 & 0xFF)
                    dest += 3
                else:
                    matchLenM273 = matchLen - 273
                    cbuffer.append(0x10 | ((matchLenM273 >> 12) & 0xF))
                    cbuffer.append((matchLenM273 >> 4) & 0xFF)
                    cbuffer.append(((matchLenM273 & 0xF) << 4) | ((matchOffsM1 >> 8) & 0xF))
                    cbuffer.append(matchOffsM1 & 0xFF)
                    dest += 4

                src += matchLen
            else:
                cbuffer.append(inData[src])

                src += 1
                dest += 1

            if src >= dcsize: break

        cbuffer[flagpos] = flag

    return cbuffer

def CompressionSearch(data, offset, totalLength, windowSize=0x1000, maxMatchAmount=18):
    """
    Find the longest possible match (in the current window) of the
    data in "data" (which has total length "length") at offset
    "offset".
    Return the offset of the match relative to "offset", and its
    length.
    This function is ported from ndspy.
    """

    if windowSize > offset:
        windowSize = offset
    start = offset - windowSize

    if windowSize < maxMatchAmount:
        maxMatchAmount = windowSize
    if (totalLength - offset) < maxMatchAmount:
        maxMatchAmount = totalLength - offset

    # Strategy: do a binary search of potential match sizes, to
    # find the longest match that exists in the data.

    lower = 3
    upper = maxMatchAmount

    recordMatchOffset = recordMatchLen = 0
    while lower <= upper:
        # Attempt to find a match at the middle length
        matchLen = (lower + upper) // 2
        match = data[offset : offset + matchLen]
        matchOffset = data.rfind(match, start, offset)

        if matchOffset == -1:
            # No such match -- any matches will be smaller than this
            upper = matchLen - 1
        else:
            # Match found!
            if matchLen > recordMatchLen:
                recordMatchOffset, recordMatchLen = matchOffset, matchLen
            lower = matchLen + 1

    if recordMatchLen == 0:
        return 0, 0
    return offset - recordMatchOffset, recordMatchLen