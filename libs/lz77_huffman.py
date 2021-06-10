#!/usr/bin/env python3
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


# lz77_huffman.py
# LH (LZ77+Huffman) decompressor in Python.
# Decompiled from NSMBW and simplified by hand

# Previously influenced by the sead::SZSDecompressor decompilation:
# https://github.com/open-ead/sead/blob/master/modules/src/resource/seadSZSDecompressor.cpp


################################################################
################################################################


from struct import unpack_from


def U8toS8(x):
    x &= 0xFF
    return x - ((x & 0x80) << 1)


def U32toS32(x):
    x &= 0xFFFFFFFF
    return x - ((x & 0x80000000) << 1)


def U64toS64(x):
    x &= 0xFFFFFFFFFFFFFFFF
    return x - ((x & 0x8000000000000000) << 1)


def Swap32(x):
    x &= 0xFFFFFFFF
    return (x << 24 |
           (x & 0xFF00) << 8 |
            x >> 24 |
            x >> 8 & 0xFF00) & 0xFFFFFFFF


def Swap16(x):
    x &= 0xFFFF
    return (x << 8 | x >> 8) & 0xFFFF


class BitReader:
    def __init__(self, srcp, srcCount, bitStream, bitStreamLen, srcpOffs=0):
        self.srcp = srcp
        self.srcpOffs = srcpOffs
        self.srcCount = srcCount
        self.bitStream = bitStream
        self.bitStreamLen = bitStreamLen

    def readS32(self, nBits):
        while self.bitStreamLen < nBits:
            if self.srcCount == 0:
                return -1

            self.bitStream <<= 8
            self.bitStream += self.srcp[self.srcpOffs]
            self.srcpOffs += 1
            self.srcCount -= 1
            self.bitStreamLen += 8

        ret = U32toS32(self.bitStream >> self.bitStreamLen - nBits & (1 << nBits) - 1)
        self.bitStreamLen -= nBits

        return ret

    def readS64(self, nBits):
        overflow = 0

        while self.bitStreamLen < nBits:
            if self.srcCount == 0:
                return -1

            if self.bitStreamLen > 24:
                overflow = self.bitStream >> 24 & 0xFF

            self.bitStream <<= 8
            self.bitStream += self.srcp[self.srcpOffs]
            self.srcpOffs += 1
            self.srcCount -= 1
            self.bitStreamLen += 8

        ret = self.bitStream
        ret |= overflow << 32
        ret = U64toS64(ret >> self.bitStreamLen - nBits & (1 << nBits) - 1)
        self.bitStreamLen -= nBits

        return ret


def LHDecompressor_getDecompSize(srcp):
    size = unpack_from('<I', srcp, 0)[0] >> 8
    if size == 0:
        size = unpack_from('<I', srcp, 4)[0]

    return size

def LHDecompressor_decomp(dst, src, srcSize):
    reader = BitReader(src, srcSize, 0, 0)

    bits64 = reader.readS64(32)
    if bits64 < 0:
        return -1

    sizeAndMagic = Swap32(bits64)
    if (sizeAndMagic & 0xF0) != 0x40:
        return -1

    destCount = U32toS32(sizeAndMagic >> 8)
    if destCount == 0:
        bits64 = reader.readS64(32)
        if bits64 < 0:
            return -1

        destCount = U32toS32(Swap32(bits64))

    bits32 = reader.readS32(16)
    if bits32 < 0:
        if destCount == 0 and 0x20 < reader.bitStreamLen:
            return -3

        return destCount

    lengthHuffTbl = [0 for _ in range(1024 + 64)]
    currentIdx = 1
    huffLen = (Swap16(bits32) + 1 << 5) - 16

    while huffLen >= 9:
        bits32 = reader.readS32(9)
        if bits32 < 0:
            if destCount == 0 and 0x20 < reader.bitStreamLen:
                return -3

            return destCount

        lengthHuffTbl[currentIdx] = bits32 & 0xFFFF
        currentIdx += 1
        huffLen -= 9

    if huffLen > 0:
        bits32 = reader.readS32(huffLen & 0xFF)
        if bits32 < 0:
            if destCount == 0 and 0x20 < reader.bitStreamLen:
                return -3

            return destCount

        huffLen = 0

    bits32 = reader.readS32(8)
    if bits32 < 0:
        if destCount == 0 and 0x20 < reader.bitStreamLen:
            return -3

        return destCount

    offsetHuffTbl = [0 for _ in range(64)]
    currentIdx = 1
    huffLen = ((bits32 & 0xFFFF) + 1 << 5) - 8

    while huffLen >= 5:
        bits32 = reader.readS32(5)
        if bits32 < 0:
            if destCount == 0 and 0x20 < reader.bitStreamLen:
                return -3

            return destCount

        offsetHuffTbl[currentIdx] = bits32 & 0xFFFF
        currentIdx += 1
        huffLen -= 5

    if huffLen > 0:
        bits32 = reader.readS32(huffLen & 0xFF)
        if bits32 < 0:
            if destCount == 0 and 0x20 < reader.bitStreamLen:
                return -3

            return destCount

        huffLen = 0

    dstOffs = 0

    while destCount > 0:
        currentNode = lengthHuffTbl; currentNodeOffs = 1

        while True:
            bits32 = reader.readS32(1)
            if bits32 < 0:
                if destCount == 0 and 0x20 < reader.bitStreamLen:
                    return -3

                return destCount

            shift = bits32 & 1
            offset = ((currentNode[currentNodeOffs] & 0x7F) + 1 << 1) + shift

            if currentNode[currentNodeOffs] & (0x100 >> shift):
                copyLen = currentNode[(currentNodeOffs * 2 & ~3) // 2 + offset]
                currentNode = offsetHuffTbl; currentNodeOffs = 1
                break

            else:
                currentNodeOffs = (currentNodeOffs * 2 & ~3) // 2 + offset

        if copyLen < 0x100:
            dst[dstOffs] = copyLen & 0xFF
            dstOffs += 1
            destCount -= 1

        else:
            n = (copyLen & 0xFF) + 3 & 0xFFFF

            while True:
                bits32 = reader.readS32(1)
                if bits32 < 0:
                    if destCount == 0 and 0x20 < reader.bitStreamLen:
                        return -3

                    return destCount

                shift = bits32 & 1
                offset = ((currentNode[currentNodeOffs] & 7) + 1 << 1) + shift

                if currentNode[currentNodeOffs] & (0x10 >> shift):
                    currentNodeOffs = (currentNodeOffs * 2 & ~3) // 2
                    nOffsetBits = U8toS8(currentNode[currentNodeOffs + offset])
                    break

                else:
                    currentNodeOffs = (currentNodeOffs * 2 & ~3) // 2 + offset

            if nOffsetBits <= 1:
                bits32 = nOffsetBits

            else:
                bits32 = reader.readS32(nOffsetBits - 1 & 0xFF)
                if bits32 < 0:
                    if destCount == 0 and 0x20 < reader.bitStreamLen:
                        return -3

                    return destCount

            if nOffsetBits >= 2:
                bits32 |= 1 << (nOffsetBits - 1)

            nOffsetBits = -1
            lzOffset = bits32 + 1 & 0xFFFF

            if destCount < n:
                n = destCount & 0xFFFF

            destCount -= n
            for _ in range(n, 0, -1):
                dst[dstOffs] = dst[dstOffs - lzOffset]
                dstOffs += 1

    if 0x20 < reader.bitStreamLen:
        return -3

    return 0


def UncompressLH(src):
    dstSize = LHDecompressor_getDecompSize(src)
    dst = bytearray(dstSize)

    res = LHDecompressor_decomp(dst, src, len(src))
    if res != 0:
        raise RuntimeError("Failed to uncompress entire LH source data! Error code: %d" % res)

    return bytes(dst)
