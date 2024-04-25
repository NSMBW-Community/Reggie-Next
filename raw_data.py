from enum import Enum
from typing import Callable



class RawData:
    '''Represents raw sprite data'''

    class Format(Enum):
        Vanilla = 16
        Extended = 8


    def __init__(self, *blocks: bytes, format: Format) -> None:
        assert all(isinstance(block, bytes) for block in blocks)

        self._blocks = list(blocks)
        self._format = format


    @property
    def raw(self) -> bytes:
        return b''.join(self._blocks)

    @raw.setter
    def raw(self, value: bytes) -> None:
        assert isinstance(value, bytes)

        if self._format == RawData.Format.Vanilla:
            if len(value) < 8:
                value += b'\x00' * (8 - len(value))

            elif len(value) > 8:
                value = value[:8]

            self._blocks = (value,)

        else:
            self._blocks = list(value[i:i + 4] for i in range(0, len(value), 4))

            if len(self._blocks[-1]) < 4:
                self._blocks = self._blocks[:-1] + (self._blocks[-1] + b'\x00' * (4 - len(self._blocks[-1])),)


    @property
    def events(self) -> bytes:
        if self._format == RawData.Format.Vanilla:
            return b''.join([self._blocks[0][0:4], self._blocks[0][12:16]])
        
        return self._blocks[0]

    @events.setter
    def events(self, value: bytes) -> None:
        assert isinstance(value, bytes)

        if self._format == RawData.Format.Vanilla:
            self._blocks = (value[:4] + self._blocks[0][4:12] + value[4:],)

        else:
            self._blocks = (value,) + self._blocks[1:]


    @property
    def blocks(self) -> list[bytes]:
        return self._blocks


    @property
    def format(self) -> Format:
        return self._format


    def __getitem__(self, index: int) -> bytes:
        if self._format == RawData.Format.Vanilla:
            return self._blocks[0][index]

        return self._blocks[index]


    def __setitem__(self, index: int, value: bytes) -> None:
        assert isinstance(value, bytes)

        if self._format == RawData.Format.Vanilla:
            self._blocks[0] = self._blocks[0][:index] + value + self._blocks[0][index + 1:]

        else:
            self._blocks[index] = value


    def _binary_operation(self, other: 'RawData', operation: Callable[[int, int], int]) -> 'RawData':
        if self._format == RawData.Format.Vanilla:
            return RawData(operation(self.blocks[0], other), format = self._format)

        all_blocks = self.raw

        all_blocks = operation(all_blocks, int.from_bytes(other, 'big'))
        new_blocks = list(all_blocks[i:i + 4] for i in range(0, len(all_blocks), 4))

        return RawData(*new_blocks, format = self._format)


    def __or__(self, other: bytes) -> 'RawData':
        return self._binary_operation(other, lambda a, b: a | b)


    def __and__(self, other: bytes) -> 'RawData':
        return self._binary_operation(other, lambda a, b: a & b)


    def __xor__(self, other: bytes) -> 'RawData':
        return self._binary_operation(other, lambda a, b: a ^ b)


    def copy(self) -> 'RawData':
        return RawData(*self._blocks, format = self._format)
