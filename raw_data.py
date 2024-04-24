from enum import Enum
from typing import Callable



class RawData:
    '''Represents raw sprite data'''

    class Format(Enum):
        Vanilla = 16
        Extended = 8


    def __init__(self, events: bytes, *blocks: bytes, format: Format) -> None:
        self._events = events
        self._blocks = tuple(blocks)
        self._format = format


    @property
    def events(self) -> bytes:
        return self._events


    @property
    def blocks(self) -> tuple[bytes]:
        return self._blocks


    @property
    def format(self) -> Format:
        return self._format


    def __getitem__(self, index: int) -> bytes:
        if self._format == RawData.Format.Vanilla:
            return self._events[index]

        return self._blocks[index]


    def __setitem__(self, index: int, value: bytes) -> None:
        if self._format == RawData.Format.Vanilla:
            self._events[index] = value

        else:
            self._blocks[index] = value


    def _binary_operation(self, other: 'RawData', operation: Callable[[int, int], int]) -> 'RawData':
        if self._format == RawData.Format.Vanilla:
            return RawData(operation(self._events, other), format = self._format)

        else:
            all_blocks = 0
            for i, block in enumerate(self._blocks):
                # make a big block with all the blocks, shifting them to the right position
                all_blocks |= int.from_bytes(block, 'big') << (i * 8)

        all_blocks = operation(all_blocks, int.from_bytes(other, 'big'))

        new_blocks = []
        for i in range(len(self._blocks)):
            # extract the blocks from the big block
            new_blocks.append((all_blocks >> (i * 8)).to_bytes(1, 'big'))

        return RawData(self._events, *new_blocks, format = self._format)


    def __or__(self, other: bytes) -> 'RawData':
        return self._binary_operation(other, lambda a, b: a | b)


    def __and__(self, other: bytes) -> 'RawData':
        return self._binary_operation(other, lambda a, b: a & b)


    def __xor__(self, other: bytes) -> 'RawData':
        return self._binary_operation(other, lambda a, b: a ^ b)
