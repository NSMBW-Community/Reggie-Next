import json
from typing import Any

class Metadata:
    """
    Manages Reggie Next metadata (level information, comments, etc)
    """

    def __init__(self) -> None:
        """
        Init the class
        """
        self.data: dict[str, str] = {}

    def load(self, data: bytes) -> None:
        """
        Loads the metadata
        """
        self.data = json.loads(data.decode())

    def save(self) -> bytes:
        """
        Returns the metadata as bytes
        """
        return json.dumps(self.data).encode()

    def get_meta_data(self, key: str) -> Any:
        """
        Returns a metadata value
        """
        try:
            return self.data[key]
        except KeyError:
            return None

    def set_meta_data(self, key: str, val: Any) -> None:
        """
        Sets a metadata value
        """
        # This key differs between the original level metadata and
        # the pre-JSON system, causing this data to no longer appear
        # in the metadata dialog
        if key == 'Webpage':
            key = 'website'

        self.data[key.lower()] = val
