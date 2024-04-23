from enum import Enum



class RawData:
    '''Represents raw sprite data'''

    class Format(Enum):
        Old = 16
        New = 8


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
