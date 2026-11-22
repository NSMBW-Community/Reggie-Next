#!/usr/bin/python
# -*- coding: latin-1 -*-

# Reggie Next - New Super Mario Bros. Wii Level Editor
# Milestone 5 - See license_short.txt for more details.

# lz77.py
# LZ77 decompressor in Cython.

################################################################
################################################################

from cpython cimport array
from cython cimport view
from libc.stdlib cimport malloc, free


ctypedef unsigned char u8
ctypedef unsigned short u16
ctypedef unsigned int u32


cdef (u32, u32) GetUncompressedSize(u8 *inData):
    cdef u32 offset = 4
    cdef u32 outSize = inData[1] | (inData[2] << 8) | (inData[3] << 16)

    if not outSize:
        outSize = inData[4] | (inData[5] << 8) | (inData[6] << 16) | (inData[7] << 24)
        offset += 4

    return outSize, offset


cpdef bytes UncompressLZ77(data):
    cdef:
        array.array dataArr = array.array('B', data)
        u8 *inData = dataArr.data.as_uchars

    if inData[0] != 0x11:
        return bytes(data)

    cdef:
        u32 inLength, outLength, offset, outIndex, copylen
        u8 flags, x, first, second, third, fourth
        u16 pos
        u8 *outData

    inLength = len(data)
    outLength, offset = GetUncompressedSize(inData)
    outData = <u8 *>malloc(outLength)

    try:
        outIndex = 0
        while outIndex < outLength and offset < inLength:
            flags = inData[offset]
            offset += 1

            for x in range(7, -1, -1):
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

                    for _ in range(copylen):
                        outData[outIndex] = outData[outIndex - pos]; outIndex += 1

                else:
                    outData[outIndex] = inData[offset]
                    offset += 1
                    outIndex += 1

        return bytes(<u8[:outLength]>outData)

    finally:
        free(outData)
