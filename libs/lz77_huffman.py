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
# Pure-Python decompressing functions for LH-compressed files


################################################################
################################################################

import ctypes
import sys

u8 = ctypes.c_ubyte
u32 = ctypes.c_uint

class LHContext():
    """
    A storage place for LH data while decompressing
    """
    def __init__(self):
        self.buf1 = bytearray(0x800)
        self.buf2 = bytearray(0x80)


def loadLHPiece(output_buffer: bytes, inData: bytes, entry_size: u8) -> int:
    """
    Loads an LH header from 'inData' into 'output_buffer'. Each entry in the header has
    'entry_size' bits. Returns the number of bytes read.
    """
    r6 = 1 << entry_size.value

    out_index = u32(2)  # The index at which the next entry should be written
    saved_entries = u32(1)  # The number of entries that are saved in the out buffer
    bytes_queue = u32(0)  # The 4-byte queue of half-parsed entries
    queue_size = u32(0)  # Number of bits in the queue
    entry_mask = u32(r6 - 1)  # The bitmask for an entry in the header
    r30 = u32(r6 << 1)

    bytes_read = u32()  # The number of header bytes that are read

    if entry_size.value <= 8:
        r6 = inData[0]
        bytes_read.value = 1
    else:
        r6 = inData[0] | (inData[1] << 8)
        bytes_read.value = 2

    data_size = u32((r6 + 1) << 2)  # The header length in bytes

    while bytes_read.value < data_size.value:
        # If the queue is not full enough to extract an entry, fill it until it
        # is full enough
        if queue_size.value < entry_size.value:
            # Calculate the number of bytes that need to be added
            r6 = (entry_size.value - queue_size.value + 7) >> 3

            # Load the input in Big Endian into the bytes queue
            for byte in inData[bytes_read.value : bytes_read.value + r6]:
                bytes_queue.value <<= 8
                bytes_queue.value |= byte

            # Update the copied amount and queue size
            bytes_read.value += r6
            queue_size.value += r6 << 3

        if saved_entries.value < r30.value:
            # Save the value as a short into the output buffer.
            entry = (bytes_queue.value >> (queue_size.value - entry_size.value)) & entry_mask.value

            output_buffer[out_index.value] = entry >> 8
            output_buffer[out_index.value + 1] = entry & 0xFF

            out_index.value += 2
            saved_entries.value += 1

        # An entry was extracted, so reduce the queue size
        queue_size.value -= entry_size.value

    return bytes_read.value


def UncompressLH(inData: bytes) -> bytes:
    """
    Decompresses LH data. Argument should be a bytes or bytearray object.
    """
    # Make context to store some buffers that are needed during decompression.
    context = LHContext()

    # Make a memory view for efficient slicing of the input data
    inBuf = memoryview(inData)

    # Read the header to figure out how large the decompressed file is
    outSize = u32(inBuf[1] | (inBuf[2] << 8) | (inBuf[3] << 16))
    inBuf = inBuf[4:]

    if outSize.value == 0:
        outSize = inBuf[0] | (inBuf[1] << 8) | (inBuf[2] << 16) | (inBuf[3] << 24)
        inBuf = inBuf[4:]

    # Make a buffer to store the decompressed file
    outBuf = bytearray(outSize.value)

    inBuf = inBuf[loadLHPiece(context.buf1, inBuf, u8(9)):]
    inBuf = inBuf[loadLHPiece(context.buf2, inBuf, u8(5)):]

    r0 = u32(0x10)
    r3 = u32(0x100)
    r4 = u32(0)
    r5 = u32(0)
    r6 = u32(0)
    r7, r8, r9, r10, r11, r12, r25 = [u32() for i in range(7)]
    outIndex = u32(0)
    flag = False

    while outIndex.value < outSize.value:

        r12.value = 2 # Used as an offset into context.buf1
        r7.value = r4.value # Used as an offset into inBuf

        enter = True
        while flag or enter:
            enter = False

            if r6.value == 0:
                r5.value = inBuf[r7.value]
                r6.value = 8
                r4.value += 1
                r7.value += 1

            r11.value = (context.buf1[r12.value] << 8) | context.buf1[r12.value + 1]
            r6.value -= 1
            r9.value = (r5.value >> r6.value) & 1

            flag = (r11.value & (r3.value >> r9.value) == 0)
            r9.value |= ((r11.value & 0x7F) + 1) << 1

            if flag:
                r12.value &= ~3
                r8.value = r9.value << 1
                r12.value += r8.value
            else:
                r8.value = (r12.value & ~3) + (r9.value << 1)
                r7.value = (context.buf1[r8.value] << 8) | context.buf1[r8.value + 1]

        if r7.value < 0x100:
            outBuf[outIndex.value] = u8(r7.value).value
            outIndex.value += 1
            continue

        # block copy?
        r7.value &= 0xFF
        r25.value = 2
        r7.value += 3
        r7.value &= 0xFFFF # r7 is really an ushort, probably
        r8.value = r4.value # used as an offset into inBuf

        enter = True
        while enter or flag:
            enter = False

            if r6.value == 0:
                r5.value = inBuf[r8.value]
                r6.value = 8
                r4.value += 1
                r8.value += 1

            r12.value = (context.buf2[r25.value] << 8) | context.buf2[r25.value + 1]
            r6.value -= 1
            r10.value = (r5.value >> r6.value) & 1
            r11.value = r12.value & 7

            flag = (r12.value & (r0.value >> r10.value) == 0)
            r10.value |= (r11.value + 1) << 1

            if flag:
                r25.value &= ~3
                r25.value += r10.value << 1
            else:
                r9.value = r25.value & ~3
                r8.value = r10.value << 1
                r11.value = (context.buf2[r9.value + r8.value] << 8) | context.buf2[r9.value + r8.value + 1]

        r10.value = 0
        if r11.value != 0:
            r10.value = 1

            for _ in range((r11.value - 1) & 0xFFFF):
                if r6.value == 0:
                    r6.value = 8
                    r5.value = inBuf[r4.value]
                    r4.value += 1

                r6.value -= 1
                r10.value = ((r10.value << 1) & 0xFFFF) | ((r5.value >> r6.value) & 1)

        if (outIndex.value + r7.value) > outSize.value:
            r7.value = outSize.value - outIndex.value
            r7.value &= 0xFFFF

        r10.value = (r10.value + 1) & 0xFFFF

        # Block copy loop
        for x in range(outIndex.value, outIndex.value + (r7.value & 0xFFFF)):
            outBuf[x] = outBuf[x - r10.value]

        outIndex.value += r7.value & 0xFFFF

    return bytes(outBuf)
