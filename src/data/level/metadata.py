import json

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
        Loads the course metadata
        """
        self.data = json.loads(data.decode())

    def save(self) -> bytes:
        """
        Returns the course metadata as bytes
        """
        return json.dumps(self.data).encode()

    def get_meta_string(self, key: str) -> str | None:
        """
        Returns a metadata string
        """
        try:
            return self.data[key]
        except KeyError:
            return None

    def set_meta_string(self, key: str, val: str) -> None:
        """
        Sets a metadata value
        """
        # This key differs between the original Reggie metadata and
        # the pre-JSON system, causing this data to no longer appear
        # in the metadata dialog
        if key == 'Webpage':
            key = 'website'
        self.data[key.lower()] = val

    def set_meta_strings(self, keys: list[str], vals: list[str]) -> None:
        """
        Sets multiple metadata strings
        """
        for key, val in keys, vals:
            self.set_meta_string(key, val)
