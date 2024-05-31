from enum import Enum
from typing import Callable
import globals_



class RawData:
    '''Represents raw sprite data'''

    class Format(Enum):
        Vanilla = 16
        Extended = 8


    def __init__(self, original: bytes, *blocks: bytes, format: Format) -> None:
        assert all(isinstance(block, bytes) for block in blocks)

        self._original = original
        self._blocks = list(blocks)
        self._format = format


    @property
    def events(self) -> bytes:
        return self._original[:2] + self._original[6:]

    @events.setter
    def events(self, value: bytes) -> None:
        assert isinstance(value, bytes)
        assert len(value) == 4, f'Expected 4 bytes, got {len(value)}'

        self._original = self._original[:2] + value + self._original[6:]


    @property
    def settings(self) -> bytes:
        return self._original[2:6]

    @settings.setter
    def settings(self, value: bytes) -> None:
        assert isinstance(value, bytes)
        assert len(value) == 4, f'Expected 4 bytes, got {len(value)}'

        self._original = self._original[:2] + value + self._original[6:]


    @property
    def original(self) -> bytes:
        return self._original

    @original.setter
    def original(self, value: bytes) -> None:
        assert isinstance(value, bytes)
        assert len(value) == 8, f'Expected 8 bytes, got {len(value)}'

        self._original = value


    @property
    def blocks(self) -> list[bytes]:
        return self._blocks

    @blocks.setter
    def blocks(self, value: list[bytes]) -> None:
        assert all(isinstance(block, bytes) for block in value)
        self._blocks = value


    @property
    def format(self) -> Format:
        return self._format


    def __getitem__(self, index: int) -> bytes:
        return self._original[index]


    def __setitem__(self, index: int, value: bytes) -> None:
        self._original = self._original[:index] + value + self._original[index + len(value):]


    def _binary_operation(self, other: 'RawData', operation: Callable[[int, int], int]) -> 'RawData':
        return RawData(operation(self._original, other._original), *self._blocks, format = self._format)


    def __or__(self, other: bytes) -> 'RawData':
        return self._binary_operation(other, lambda a, b: a | b)


    def __and__(self, other: bytes) -> 'RawData':
        return self._binary_operation(other, lambda a, b: a & b)


    def __xor__(self, other: bytes) -> 'RawData':
        return self._binary_operation(other, lambda a, b: a ^ b)


    def copy(self) -> 'RawData':
        return RawData(
            self._original,
            *self._blocks,
            format = self._format
        )


    @staticmethod
    def from_sprite_id(sprite_id: int) -> 'RawData':
        extended_settings = globals_.Sprites[sprite_id].extendedSettings

        return RawData(
            bytes(8),
            *(bytes(4) for _ in range(extended_settings)),
            format = RawData.Format.Extended if extended_settings else RawData.Format.Vanilla,
        )


    def fix_size_if_needed(self, sprite_id: int) -> None:
        block_count = globals_.Sprites[sprite_id].extendedSettings

        while len(self.blocks) < block_count:
            self.blocks.append(bytes(4))

        while len(self.blocks) > block_count:
            # Only remove empty blocks
            if self.blocks[-1] != bytes(4):
                break

            self.blocks.pop(-1)


    @property
    def optimized(self) -> 'RawData':
        copy = self.copy()
        while copy.blocks and copy.blocks[-1] == bytes(4):
            copy.blocks.pop(-1)

        return copy
