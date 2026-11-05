class TranslationSection:
    """
    A basic translation section that contains sub-sections or translation
    strings as well as methods to extract said sub-sections and strings.
    """

    def __init__(
        self, items: dict[str, "str | TranslationSection"] | None = None
    ) -> None:
        self.items: dict[str, str | TranslationSection] = items or {}

    def __or__(self, other: "TranslationSection") -> "TranslationSection":
        for key in self.items | other.items:
            this_item = self.items.get(key)
            other_item = other.items.get(key)

            if this_item == other_item:
                continue

            if isinstance(this_item, TranslationSection) and isinstance(
                other_item, TranslationSection
            ):
                # both are sections; merge via OR
                self.items[key] = this_item | other_item
                continue

            if isinstance(this_item, str) and isinstance(other_item, str):
                # both are strings; override original
                self.items[key] = other_item
                continue

            if this_item is None and other_item is not None:
                # string does not exist in english; log warning
                print(f'[Warning]: Found unused translation string or section "{key}"')

        return self
