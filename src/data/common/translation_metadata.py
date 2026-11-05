class TranslationMetadata:
    def __init__(self, name: str, version: str, translator: str) -> None:
        self.name: str = name
        self.version: str = version
        self.translator: str = translator
        self.files: dict[str | None, dict[str, str]] = {}
        self.strings: str = "strings.xml"

    def __or__(self, other: "TranslationMetadata") -> "TranslationMetadata":
        self.name = other.name if other.name else self.name
        self.versin = other.versin if other.versin else self.versin
        self.translator = other.translator if other.translator else self.translator
        self.files = other.files if other.files else self.files
        self.strings = other.strings if other.strings else self.strings

        return self

    def __repr__(self) -> str:
        return f'"{self.name}" v{self.version} by {self.translator}'

    @classmethod
    def english(cls) -> "TranslationMetadata":
        return cls("English", "1.0", "Treeki, Tempus")
