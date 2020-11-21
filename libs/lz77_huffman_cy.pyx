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


# lz77_huffman_cy.pyx
# LH (LZ77+Huffman) decompressor in Cython.
# Decompiled from NSMBW

# Heavily influenced by the sead::SZSDecompressor decompilation:
# https://github.com/open-ead/sead/blob/master/modules/src/resource/seadSZSDecompressor.cpp


################################################################
################################################################


from cpython cimport array
from cython cimport view
from cython.operator cimport postdecrement
from libc.stdint cimport  int8_t,  int16_t,  int32_t,  int64_t
from libc.stdint cimport uint8_t, uint16_t, uint32_t, uint64_t, uintptr_t
from libc.stdlib cimport malloc, free
from libc.string cimport memcpy

ctypedef   int8_t s8
ctypedef  uint8_t u8
ctypedef  int16_t s16
ctypedef uint16_t u16
ctypedef  int32_t s32
ctypedef uint32_t u32
ctypedef  int64_t s64
ctypedef uint64_t u64


cdef inline u32 Swap32(u32 x):
    return (x << 24 |
           (x & 0xFF00) << 8 |
            x >> 24 |
            x >> 8 & 0xFF00)


cdef inline u16 Swap16(u16 x):
    return (x << 8 | x >> 8) & 0xFFFF


cdef struct BitReader:
    const u8* srcp
    u32 srcCount
    u32 bitStream
    u32 bitStreamLen


cdef inline s32 BitReader_readS32(BitReader* this, u8 nBits):
    cdef s32 ret

    while this.bitStreamLen < nBits:
        if this.srcCount == 0:
            return -1

        this.bitStream <<= 8
        this.bitStream += this.srcp[0]
        this.srcp += 1
        this.srcCount -= 1
        this.bitStreamLen += 8

    ret = <s32>(this.bitStream >> this.bitStreamLen - nBits & (1 << nBits) - 1)
    this.bitStreamLen -= nBits

    return ret


cdef inline s64 BitReader_readS64(BitReader* this, u8 nBits):
    cdef:
        s64 ret
        u8 overflow = 0

    while this.bitStreamLen < nBits:
        if this.srcCount == 0:
            return -1

        if this.bitStreamLen > 24:
            overflow = <u8>(this.bitStream >> 24)

        this.bitStream <<= 8
        this.bitStream += this.srcp[0]
        this.srcp += 1
        this.srcCount -= 1
        this.bitStreamLen += 8

    ret = this.bitStream
    ret |= <s64>overflow << 32
    ret = <s64>(ret >> this.bitStreamLen - nBits & (1 << nBits) - 1)
    this.bitStreamLen -= nBits

    return ret


cdef struct LHDecompressor_DecompContext:
    u8* destp
    s32 destCount
    s32 forceDestCount
    u16 lengthHuffTbl[1024]
    u16 offsetHuffTbl[64]
    u16* currentNode
    s32 lengthHuffLen
    s32 offsetHuffLen
    u32 currentIdx
    u32 bitStream
    u32 bitStreamLen
    u16 copyLen
    s8 nOffsetBits
    u8 headerSize

cdef void LHDecompressor_DecompContext_initialize(LHDecompressor_DecompContext* this, void* dst):  # 0x801d7060, NSMBW PALv1
    this.destp = <u8*>dst
    this.destCount = -1
    this.currentNode = this.lengthHuffTbl + 1
    this.lengthHuffLen = -1
    this.offsetHuffLen = -1
    this.headerSize = 8
    this.copyLen = 0
    this.bitStream = 0
    this.bitStreamLen = 0
    this.nOffsetBits = -1
    this.forceDestCount = 0


cdef class LHDecompressor:
    cdef array.array dstArr
    cdef LHDecompressor_DecompContext context

    def __cinit__(self, bytes dst):
        self.dstArr = array.array('B', dst)
        LHDecompressor_DecompContext_initialize(&self.context, self.dstArr.data.as_uchars)

    cdef s32 decomp(self, const void* srcp, u32 len):
        return LHDecompressor.streamDecomp(&self.context, srcp, len)

    cdef bytes get(self):
        if self.context.destCount > 0 or self.context.headerSize > 0:
            raise RuntimeError("Tried to read LH decompressed data, but compression is not done!")

        return self.dstArr.tobytes()

    @staticmethod
    cdef u32 getDecompSize(const void* srcp):  # 0x801d8290, NSMBW PALv1
        cdef u32 size = (<u32*>srcp)[0] >> 8
        if size == 0:
            size = (<u32*>srcp)[1]

        return size

    @staticmethod
    cdef s32 streamDecomp(LHDecompressor_DecompContext* context, const void* src, u32 srcSize):  # 0x801d70a0, NSMBW PALv1
        cdef:
            s32 bits32
            s64 bits64
            u32 sizeAndMagic, offset
            u16* currentNode
            u16 copyLen, n, lzOffset
            u8 shift

            BitReader reader

        reader.srcp = <const u8*>src
        reader.srcCount = srcSize
        reader.bitStream = context.bitStream
        reader.bitStreamLen = context.bitStreamLen

        while context.headerSize > 0:
            bits64 = BitReader_readS64(&reader, 32)
            if bits64 < 0:
                context.bitStream = reader.bitStream
                context.bitStreamLen = reader.bitStreamLen

                if context.destCount == 0 and context.forceDestCount == 0 and 0x20 < reader.bitStreamLen:
                    return -3

                return context.destCount

            context.headerSize -= 4
            if context.headerSize == 4:
                sizeAndMagic = Swap32(<u32>bits64)
                if (sizeAndMagic & 0xF0) != 0x40:
                    return -1

                context.destCount = <s32>(sizeAndMagic >> 8)

                if context.destCount == 0:
                    context.headerSize = 4
                    context.destCount = -1

                else:
                    context.headerSize = 0

            else:
                context.destCount = <s32>Swap32(<u32>bits64)

            if context.headerSize == 0:
                if context.forceDestCount > 0 and context.forceDestCount < context.destCount:
                    context.destCount = context.forceDestCount

        if context.lengthHuffLen < 0:
            bits32 = BitReader_readS32(&reader, 16)
            if bits32 < 0:
                context.bitStream = reader.bitStream
                context.bitStreamLen = reader.bitStreamLen

                if context.destCount == 0 and context.forceDestCount == 0 and 0x20 < reader.bitStreamLen:
                    return -3

                return context.destCount

            context.currentIdx = 1
            context.lengthHuffLen = (Swap16(<u16>bits32) + 1 << 5) - 16

        while context.lengthHuffLen >= 9:
            bits32 = BitReader_readS32(&reader, 9)
            if bits32 < 0:
                context.bitStream = reader.bitStream
                context.bitStreamLen = reader.bitStreamLen

                if context.destCount == 0 and context.forceDestCount == 0 and 0x20 < reader.bitStreamLen:
                    return -3

                return context.destCount

            context.lengthHuffTbl[context.currentIdx] = <u16>bits32
            context.currentIdx += 1
            context.lengthHuffLen -= 9

        if context.lengthHuffLen > 0:
            bits32 = BitReader_readS32(&reader, <u8>context.lengthHuffLen)
            if bits32 < 0:
                context.bitStream = reader.bitStream
                context.bitStreamLen = reader.bitStreamLen

                if context.destCount == 0 and context.forceDestCount == 0 and 0x20 < reader.bitStreamLen:
                    return -3

                return context.destCount

            context.lengthHuffLen = 0

            ### insert table verification(?) here that I'm too lazy to decomp ###

        if context.offsetHuffLen < 0:
            bits32 = BitReader_readS32(&reader, 8)
            if bits32 < 0:
                context.bitStream = reader.bitStream
                context.bitStreamLen = reader.bitStreamLen

                if context.destCount == 0 and context.forceDestCount == 0 and 0x20 < reader.bitStreamLen:
                    return -3

                return context.destCount

            context.currentIdx = 1
            context.offsetHuffLen = (<u16>bits32 + 1 << 5) - 8

        while context.offsetHuffLen >= 5:
            bits32 = BitReader_readS32(&reader, 5)
            if bits32 < 0:
                context.bitStream = reader.bitStream
                context.bitStreamLen = reader.bitStreamLen

                if context.destCount == 0 and context.forceDestCount == 0 and 0x20 < reader.bitStreamLen:
                    return -3

                return context.destCount

            context.offsetHuffTbl[context.currentIdx] = <u16>bits32
            context.currentIdx += 1
            context.offsetHuffLen -= 5

        if context.offsetHuffLen > 0:
            bits32 = BitReader_readS32(&reader, <u8>context.offsetHuffLen)
            if bits32 < 0:
                context.bitStream = reader.bitStream
                context.bitStreamLen = reader.bitStreamLen

                if context.destCount == 0 and context.forceDestCount == 0 and 0x20 < reader.bitStreamLen:
                    return -3

                return context.destCount

            context.offsetHuffLen = 0

            ### insert table verification(?) here that I'm too lazy to decomp ###

        currentNode = context.currentNode
        copyLen = context.copyLen

        while context.destCount > 0:
            if copyLen == 0:
                while True:
                    bits32 = BitReader_readS32(&reader, 1)
                    if bits32 < 0:
                        context.currentNode = currentNode
                        context.copyLen = copyLen
                        context.bitStream = reader.bitStream
                        context.bitStreamLen = reader.bitStreamLen

                        if context.destCount == 0 and context.forceDestCount == 0 and 0x20 < reader.bitStreamLen:
                            return -3

                        return context.destCount

                    shift = <u8>(bits32 & 1)
                    offset = ((<u32>currentNode[0] & 0x7F) + 1 << 1) + shift

                    if currentNode[0] & 0x100 >> shift:
                        copyLen = (<u16*>(<uintptr_t>currentNode & ~<uintptr_t>3))[offset]
                        currentNode = context.offsetHuffTbl + 1
                        break

                    else:
                        currentNode = <u16*>(<uintptr_t>currentNode & ~<uintptr_t>3) + offset

            if copyLen < 0x100:
                context.destp[0] = <u8>copyLen
                context.destp += 1
                context.destCount -= 1

                currentNode = context.lengthHuffTbl + 1
                copyLen = 0

            else:
                n = <u16>((copyLen & 0xFF) + 3)

                if context.nOffsetBits < 0:
                    while True:
                        bits32 = BitReader_readS32(&reader, 1)
                        if bits32 < 0:
                            context.currentNode = currentNode
                            context.copyLen = copyLen
                            context.bitStream = reader.bitStream
                            context.bitStreamLen = reader.bitStreamLen

                            if context.destCount == 0 and context.forceDestCount == 0 and 0x20 < reader.bitStreamLen:
                                return -3

                            return context.destCount

                        shift = <u8>(bits32 & 1)
                        offset = ((<u32>currentNode[0] & 7) + 1 << 1) + shift

                        if currentNode[0] & 0x10 >> shift:
                            currentNode = <u16*>(<uintptr_t>currentNode & ~<uintptr_t>3)
                            context.nOffsetBits = <s8>currentNode[offset]
                            break

                        else:
                            currentNode = <u16*>(<uintptr_t>currentNode & ~<uintptr_t>3) + offset

                if context.nOffsetBits <= 1:
                    bits32 = context.nOffsetBits

                else:
                    bits32 = BitReader_readS32(&reader, <u8>(context.nOffsetBits - 1))
                    if bits32 < 0:
                        context.currentNode = currentNode
                        context.copyLen = copyLen
                        context.bitStream = reader.bitStream
                        context.bitStreamLen = reader.bitStreamLen

                        if context.destCount == 0 and context.forceDestCount == 0 and 0x20 < reader.bitStreamLen:
                            return -3

                        return context.destCount

                if context.nOffsetBits >= 2:
                    bits32 |= 1 << context.nOffsetBits - 1

                context.nOffsetBits = -1
                lzOffset = <u16>(bits32 + 1)

                if context.destCount < n:
                    if context.forceDestCount == 0:
                        return -4

                    n = <u16>context.destCount

                context.destCount -= n
                while postdecrement(n):
                    context.destp[0] = context.destp[-lzOffset]
                    context.destp += 1

                copyLen = 0
                currentNode = context.lengthHuffTbl + 1

        context.bitStream = reader.bitStream
        context.bitStreamLen = reader.bitStreamLen

        if context.destCount == 0 and context.forceDestCount == 0 and 0x20 < reader.bitStreamLen:
            return -3

        return context.destCount

cpdef bytes UncompressLH(src):
    cdef:
        array.array srcArr = array.array('B', src)
        u8* srcp = srcArr.data.as_uchars
        u32 srcSize = len(src)

        u32 dstSize = LHDecompressor.getDecompSize(srcp)
        LHDecompressor decompressor = LHDecompressor(bytes(dstSize))

        s32 res = decompressor.decomp(srcp, srcSize)

    if res != 0:
        raise RuntimeError("Failed to uncompress entire LH source data! Error code: %d" % res)

    return decompressor.get()
