class TranslationInfo:
    def __init__(self, name: str, version: str, translator: str) -> None:
        self.name: str = name
        self.version: str = version
        self.translator: str = translator
        self.files: dict[str | None, dict[str, str]] = {}
        self.strings: str = "strings.xml"

    def __repr__(self) -> str:
        return f'"{self.name}" v{self.version} by {self.translator}'
