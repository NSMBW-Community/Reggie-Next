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
# Decompiled from NSMBW

# Heavily influenced by the sead::SZSDecompressor decompilation:
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


class LHDecompressor:
    class DecompContext:
        def __init__(self, dst):
            self.initialize(dst)

        def initialize(self, dst):
            self.destp = dst
            self.destpOffs = 0
            self.destCount = -1
            self.lengthHuffTbl = [0 for _ in range(1024)]
            self.offsetHuffTbl = [0 for _ in range(64)]
            self.currentNode = self.lengthHuffTbl
            self.currentNodeOffs = 1
            self.lengthHuffLen = -1
            self.offsetHuffLen = -1
            self.headerSize = 8
            self.copyLen = 0
            self.bitStream = 0
            self.bitStreamLen = 0
            self.nOffsetBits = -1
            self.forceDestCount = 0

    def __init__(self, dstSize):
        self.dst = bytearray(dstSize)
        self.context = LHDecompressor.DecompContext(self.dst)

    def decomp(self, srcp, len):
        return LHDecompressor.streamDecomp(self.context, srcp, len)

    def get(self):
        if self.context.destCount > 0 or self.context.headerSize > 0:
            raise RuntimeError("Tried to readS32 LH decompressed data, but compression is not done!")

        return bytes(self.dst)

    @staticmethod
    def getDecompSize(srcp):
        size = unpack_from('<I', srcp, 0)[0] >> 8
        if size == 0:
            size = unpack_from('<I', srcp, 4)[0]

        return size

    @staticmethod
    def streamDecomp(context, src, srcSize):
        reader = BitReader(src, srcSize, context.bitStream, context.bitStreamLen)

        while context.headerSize > 0:
            bits64 = reader.readS64(32)
            if bits64 < 0:
                context.bitStream = reader.bitStream
                context.bitStreamLen = reader.bitStreamLen

                if context.destCount == 0 and context.forceDestCount == 0 and 0x20 < reader.bitStreamLen:
                    return -3

                return context.destCount

            context.headerSize -= 4
            if context.headerSize == 4:
                sizeAndMagic = Swap32(bits64)
                if (sizeAndMagic & 0xF0) != 0x40:
                    return -1

                context.destCount = U32toS32(sizeAndMagic >> 8)

                if context.destCount == 0:
                    context.headerSize = 4
                    context.destCount = -1

                else:
                    context.headerSize = 0

            else:
                context.destCount = U32toS32(Swap32(bits64))

            if context.headerSize == 0:
                if context.forceDestCount > 0 and context.forceDestCount < context.destCount:
                    context.destCount = context.forceDestCount

        if context.lengthHuffLen < 0:
            bits32 = reader.readS32(16)
            if bits32 < 0:
                context.bitStream = reader.bitStream
                context.bitStreamLen = reader.bitStreamLen

                if context.destCount == 0 and context.forceDestCount == 0 and 0x20 < reader.bitStreamLen:
                    return -3

                return context.destCount

            context.currentIdx = 1
            context.lengthHuffLen = (Swap16(bits32) + 1 << 5) - 16

        while context.lengthHuffLen >= 9:
            bits32 = reader.readS32(9)
            if bits32 < 0:
                context.bitStream = reader.bitStream
                context.bitStreamLen = reader.bitStreamLen

                if context.destCount == 0 and context.forceDestCount == 0 and 0x20 < reader.bitStreamLen:
                    return -3

                return context.destCount

            context.lengthHuffTbl[context.currentIdx] = bits32 & 0xFFFF
            context.currentIdx += 1
            context.lengthHuffLen -= 9

        if context.lengthHuffLen > 0:
            bits32 = reader.readS32(context.lengthHuffLen & 0xFF)
            if bits32 < 0:
                context.bitStream = reader.bitStream
                context.bitStreamLen = reader.bitStreamLen

                if context.destCount == 0 and context.forceDestCount == 0 and 0x20 < reader.bitStreamLen:
                    return -3

                return context.destCount

            context.lengthHuffLen = 0

            ### insert table verification(?) here that I'm too lazy to decomp ###

        if context.offsetHuffLen < 0:
            bits32 = reader.readS32(8)
            if bits32 < 0:
                context.bitStream = reader.bitStream
                context.bitStreamLen = reader.bitStreamLen

                if context.destCount == 0 and context.forceDestCount == 0 and 0x20 < reader.bitStreamLen:
                    return -3

                return context.destCount

            context.currentIdx = 1
            context.offsetHuffLen = ((bits32 & 0xFFFF) + 1 << 5) - 8

        while context.offsetHuffLen >= 5:
            bits32 = reader.readS32(5)
            if bits32 < 0:
                context.bitStream = reader.bitStream
                context.bitStreamLen = reader.bitStreamLen

                if context.destCount == 0 and context.forceDestCount == 0 and 0x20 < reader.bitStreamLen:
                    return -3

                return context.destCount

            context.offsetHuffTbl[context.currentIdx] = bits32 & 0xFFFF
            context.currentIdx += 1
            context.offsetHuffLen -= 5

        if context.offsetHuffLen > 0:
            bits32 = reader.readS32(context.offsetHuffLen & 0xFF)
            if bits32 < 0:
                context.bitStream = reader.bitStream
                context.bitStreamLen = reader.bitStreamLen

                if context.destCount == 0 and context.forceDestCount == 0 and 0x20 < reader.bitStreamLen:
                    return -3

                return context.destCount

            context.offsetHuffLen = 0

            ### insert table verification(?) here that I'm too lazy to decomp ###

        currentNode = context.currentNode; currentNodeOffs = context.currentNodeOffs
        copyLen = context.copyLen

        while context.destCount > 0:
            if copyLen == 0:
                while True:
                    bits32 = reader.readS32(1)
                    if bits32 < 0:
                        context.currentNode = currentNode; context.currentNodeOffs = currentNodeOffs
                        context.copyLen = copyLen
                        context.bitStream = reader.bitStream
                        context.bitStreamLen = reader.bitStreamLen

                        if context.destCount == 0 and context.forceDestCount == 0 and 0x20 < reader.bitStreamLen:
                            return -3

                        return context.destCount

                    shift = bits32 & 1
                    offset = ((currentNode[currentNodeOffs] & 0x7F) + 1 << 1) + shift

                    if currentNode[currentNodeOffs] & (0x100 >> shift):
                        copyLen = currentNode[(currentNodeOffs * 2 & ~3) // 2 + offset]
                        currentNode = context.offsetHuffTbl
                        currentNodeOffs = 1
                        break

                    else:
                        currentNodeOffs = (currentNodeOffs * 2 & ~3) // 2 + offset

            if copyLen < 0x100:
                context.destp[context.destpOffs] = copyLen & 0xFF
                context.destpOffs += 1
                context.destCount -= 1

                currentNode = context.lengthHuffTbl
                currentNodeOffs = 1
                copyLen = 0

            else:
                n = (copyLen & 0xFF) + 3 & 0xFFFF

                if context.nOffsetBits < 0:
                    while True:
                        bits32 = reader.readS32(1)
                        if bits32 < 0:
                            context.currentNode = currentNode; context.currentNodeOffs = currentNodeOffs
                            context.copyLen = copyLen
                            context.bitStream = reader.bitStream
                            context.bitStreamLen = reader.bitStreamLen

                            if context.destCount == 0 and context.forceDestCount == 0 and 0x20 < reader.bitStreamLen:
                                return -3

                            return context.destCount

                        shift = bits32 & 1
                        offset = ((currentNode[currentNodeOffs] & 7) + 1 << 1) + shift

                        if currentNode[currentNodeOffs] & (0x10 >> shift):
                            currentNodeOffs = (currentNodeOffs * 2 & ~3) // 2
                            context.nOffsetBits = U8toS8(currentNode[currentNodeOffs + offset])
                            break

                        else:
                            currentNodeOffs = (currentNodeOffs * 2 & ~3) // 2 + offset

                if context.nOffsetBits <= 1:
                    bits32 = context.nOffsetBits

                else:
                    bits32 = reader.readS32(context.nOffsetBits - 1 & 0xFF)
                    if bits32 < 0:
                        context.currentNode = currentNode; context.currentNodeOffs = currentNodeOffs
                        context.copyLen = copyLen
                        context.bitStream = reader.bitStream
                        context.bitStreamLen = reader.bitStreamLen

                        if context.destCount == 0 and context.forceDestCount == 0 and 0x20 < reader.bitStreamLen:
                            return -3

                        return context.destCount

                if context.nOffsetBits >= 2:
                    bits32 |= 1 << (context.nOffsetBits - 1)

                context.nOffsetBits = -1
                lzOffset = bits32 + 1 & 0xFFFF

                if context.destCount < n:
                    if context.forceDestCount == 0:
                        return -4

                    n = context.destCount & 0xFFFF

                context.destCount -= n
                for _ in range(n, 0, -1):
                    context.destp[context.destpOffs] = context.destp[context.destpOffs - lzOffset]
                    context.destpOffs += 1

                copyLen = 0
                currentNode = context.lengthHuffTbl
                currentNodeOffs = 1

        context.bitStream = reader.bitStream
        context.bitStreamLen = reader.bitStreamLen

        if context.destCount == 0 and context.forceDestCount == 0 and 0x20 < reader.bitStreamLen:
            return -3

        return context.destCount


def UncompressLH(srcp):
    dstSize = LHDecompressor.getDecompSize(srcp)
    decompressor = LHDecompressor(dstSize)

    res = decompressor.decomp(srcp, len(srcp))
    if res != 0:
        raise RuntimeError("Failed to uncompress entire LH source data! Error code: %d" % res)

    return decompressor.get()
