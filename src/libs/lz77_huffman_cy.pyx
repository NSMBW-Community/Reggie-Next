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
# Decompiled from NSMBW and simplified by hand

# Previously influenced by the sead::SZSDecompressor decompilation:
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


# Buffer where the length and offset huffman tables will be stored
cdef u16 WorkBuffer[1024 + 64]


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


cdef u32 LHDecompressor_getDecompSize(const void* src):
    cdef u32 size = (<u32*>src)[0] >> 8
    if size == 0:
        size = (<u32*>src)[1]

    return size


cdef s32 LHDecompressor_decomp(u8* dst, const void* src, u32 srcSize):
    cdef:
        s32 bits32, destCount, huffLen
        s64 bits64
        u32 sizeAndMagic, currentIdx, offset
        u16 *lengthHuffTbl
        u16 *offsetHuffTbl
        u16 *currentNode
        u16 copyLen, n, lzOffset
        u8 shift
        s8 nOffsetBits

        BitReader reader

    reader.srcp = <const u8*>src
    reader.srcCount = srcSize
    reader.bitStream = 0
    reader.bitStreamLen = 0

    bits64 = BitReader_readS64(&reader, 32)
    if bits64 < 0:
        return -1

    sizeAndMagic = Swap32(<u32>bits64)
    if (sizeAndMagic & 0xF0) != 0x40:
        return -1

    destCount = <s32>(sizeAndMagic >> 8)
    if destCount == 0:
        bits64 = BitReader_readS64(&reader, 32)
        if bits64 < 0:
            return -1

        destCount = <s32>Swap32(<u32>bits64)

    bits32 = BitReader_readS32(&reader, 16)
    if bits32 < 0:
        if destCount == 0 and 0x20 < reader.bitStreamLen:
            return -3

        return destCount

    lengthHuffTbl = WorkBuffer
    currentIdx = 1
    huffLen = (Swap16(<u16>bits32) + 1 << 5) - 16

    while huffLen >= 9:
        bits32 = BitReader_readS32(&reader, 9)
        if bits32 < 0:
            if destCount == 0 and 0x20 < reader.bitStreamLen:
                return -3

            return destCount

        lengthHuffTbl[currentIdx] = <u16>bits32
        currentIdx += 1
        huffLen -= 9

    if huffLen > 0:
        bits32 = BitReader_readS32(&reader, <u8>huffLen)
        if bits32 < 0:
            if destCount == 0 and 0x20 < reader.bitStreamLen:
                return -3

            return destCount

        huffLen = 0

    bits32 = BitReader_readS32(&reader, 8)
    if bits32 < 0:
        if destCount == 0 and 0x20 < reader.bitStreamLen:
            return -3

        return destCount

    offsetHuffTbl = WorkBuffer + 1024
    currentIdx = 1
    huffLen = (<u16>bits32 + 1 << 5) - 8

    while huffLen >= 5:
        bits32 = BitReader_readS32(&reader, 5)
        if bits32 < 0:
            if destCount == 0 and 0x20 < reader.bitStreamLen:
                return -3

            return destCount

        offsetHuffTbl[currentIdx] = <u16>bits32
        currentIdx += 1
        huffLen -= 5

    if huffLen > 0:
        bits32 = BitReader_readS32(&reader, <u8>huffLen)
        if bits32 < 0:
            if destCount == 0 and 0x20 < reader.bitStreamLen:
                return -3

            return destCount

        huffLen = 0

    while destCount > 0:
        currentNode = lengthHuffTbl + 1

        while True:
            bits32 = BitReader_readS32(&reader, 1)
            if bits32 < 0:
                if destCount == 0 and 0x20 < reader.bitStreamLen:
                    return -3

                return destCount

            shift = <u8>(bits32 & 1)
            offset = ((<u32>currentNode[0] & 0x7F) + 1 << 1) + shift

            if currentNode[0] & 0x100 >> shift:
                copyLen = (<u16*>(<uintptr_t>currentNode & ~<uintptr_t>3))[offset]
                currentNode = offsetHuffTbl + 1
                break

            else:
                currentNode = <u16*>(<uintptr_t>currentNode & ~<uintptr_t>3) + offset

        if copyLen < 0x100:
            dst[0] = <u8>copyLen
            dst += 1
            destCount -= 1

        else:
            n = <u16>((copyLen & 0xFF) + 3)

            while True:
                bits32 = BitReader_readS32(&reader, 1)
                if bits32 < 0:
                    if destCount == 0 and 0x20 < reader.bitStreamLen:
                        return -3

                    return destCount

                shift = <u8>(bits32 & 1)
                offset = ((<u32>currentNode[0] & 7) + 1 << 1) + shift

                if currentNode[0] & 0x10 >> shift:
                    currentNode = <u16*>(<uintptr_t>currentNode & ~<uintptr_t>3)
                    nOffsetBits = <s8>currentNode[offset]
                    break

                else:
                    currentNode = <u16*>(<uintptr_t>currentNode & ~<uintptr_t>3) + offset

            if nOffsetBits <= 1:
                bits32 = nOffsetBits

            else:
                bits32 = BitReader_readS32(&reader, <u8>(nOffsetBits - 1))
                if bits32 < 0:
                    if destCount == 0 and 0x20 < reader.bitStreamLen:
                        return -3

                    return destCount

            if nOffsetBits >= 2:
                bits32 |= 1 << nOffsetBits - 1

            nOffsetBits = -1
            lzOffset = <u16>(bits32 + 1)

            if destCount < n:
                n = <u16>destCount

            destCount -= n
            while postdecrement(n):
                dst[0] = dst[-lzOffset]
                dst += 1

    if 0x20 < reader.bitStreamLen:
        return -3

    return 0


cpdef bytes UncompressLH(src):
    cdef:
        array.array srcArr = array.array('B', src)
        u8* srcp = srcArr.data.as_uchars
        u32 srcSize = <u32>len(src)

        u32 dstSize = LHDecompressor_getDecompSize(srcp)
        array.array dstArr = array.array('B', bytes(dstSize))
        res = LHDecompressor_decomp(dstArr.data.as_uchars, srcp, srcSize)

    if res != 0:
        raise RuntimeError("Failed to uncompress entire LH source data! Error code: %d" % res)

    return dstArr.tobytes()
