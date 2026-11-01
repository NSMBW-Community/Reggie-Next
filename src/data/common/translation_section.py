import os
from typing import Any, Literal
from xml.etree import ElementTree

from data.common.utils import get_reggiedata_folder, get_root_path

ElementType = Literal["section", "string"]


class TranslationSection:
    """
    A basic translation section that contains sub-sections or translation
    strings as well as methods to extract said sub-sections and strings.
    """

    def __init__(
        self, items: dict[str, "str | TranslationSection"] | None = None
    ) -> None:
        self._items: dict[str, str | TranslationSection] = items or {}

    def section(self, id: str) -> "TranslationSection":
        """
        Returns a section within this section or any sub-section that matches
        the given id.

        :param id: The ID of the translation section to look for. Iterations
        deeper into this section can be achieved by separating the ID with
        periods.

        **Example**: Providing the ID `common.greetings` will return the
        section with the ID `greetings` found within the `common` section.
        :return: A translation section that matches the structure of the given
        ID. If no section with the given ID was found, a warning will be
        logged and an empty section will be returned instead.
        """
        result, stack_trace = self._fetch(id, "section")
        if not isinstance(result, TranslationSection):
            self._log_id_error("section", id, stack_trace)
            return TranslationSection()

        return result

    def string(self, id: str, *templates: tuple[str, Any]) -> str:
        """
        Returns a string within this section or any sub-section that matches
        the given id.

        :param id: The ID of the translation string to look for. Iterations
        deeper into this section can be achieved by separating the ID with
        periods.

        **Example**: Providing the ID `common.hello_world` will return the
        translation string with the ID `hello_world` found within the `common`
        section.
        :return: A translation string that matches the structure of the given
        id. If no string with the given ID was found, a warning will be logged
        and said ID will be returned instead.
        """
        result, stack_trace = self._fetch(id, "string")

        if not isinstance(result, str):
            self._log_id_error("string", id, stack_trace)
            return id

        if templates:
            for template in templates:
                result = result.replace(template[0], str(template[1]))

        return TranslationSection.convert_formatting(result)

    def string_list(self, *ids: str) -> list[str]:
        """
        Returns a list of strings within this section or any sub-section where
        each string's ID matches a given ID.

        :param ids: The IDs of the translation strings to look for. Iterations
        deeper into this section can be achieved by separating an ID with
        periods.

        **Example**: Providing the ID `common.hello_world` will return the
        translation string with the ID `hello_world` found within the `common`
        section.

        :return: A list of translation strings that matches the structures of
        the given IDs. The length of the list is always equal to the amount of
        IDs provided. If no IDs are provided, all strings from this section but
        no sub-section will be returned instead. If a string with a given ID
        could not be found, a warning will be logged and said ID will be added
        to the list instead.
        """
        if len(ids) == 0:
            return [item for item in self._items.values() if isinstance(item, str)]
        return [self.string(id) for id in ids]

    def _fetch(
        self, id: str, type: ElementType
    ) -> tuple["str | TranslationSection | None", list[str]]:
        ids: list[str] = id.split(".")
        result: str | TranslationSection | None = self
        stack_trace: list[str] = []
        for index, sub_id in enumerate(ids):
            if result == None:
                stack_trace.append(
                    f' - Could not find translation section for ID "{sub_id}"'
                )
                continue
            result = result._items.get(sub_id)
            if type == "string" and index == len(ids) - 1 and isinstance(result, str):
                break
            if not isinstance(result, TranslationSection):
                result = None
                stack_trace.append(
                    f' - Could not find translation section for ID "{sub_id}"'
                )

        return (result, stack_trace)

    def _log_id_error(self, type: ElementType, id: str, stack_trace: list[str]) -> None:
        message = f'[Warning] - Could not find translation {type} for ID "{id}"{("\n" + "\n".join(stack_trace)) if stack_trace else ""}'
        print(message)

        if not os.path.isfile(os.path.join(get_root_path(), "log.txt")):
            mode = "w"
        else:
            mode = "a"

        with open("log.txt", mode, encoding="utf-8") as f:
            f.write(message)

    @staticmethod
    def convert_formatting(text: str) -> str:
        """
        Performs automatic replacements on text strings.
        Intended for XMLs where proper formatting can't be applied
        """
        replace = {
            "[br]": "<br>",
            "[b]": "<b>",
            "[/b]": "</b>",
            "[i]": "<i>",
            "[/i]": "</i>",
            "[a": "<a",
            '"]': '">',  # Workaround
            "[/a]": "</a>",
            "\\n": "\n",
            "//n": "\n",
            "[tm]": "™",
            "[small]": "<small>",
            "[/small]": "</small>",
        }

        for old, new in replace.items():
            text = text.replace(old, new)

        return text

    @classmethod
    def init_as_english(cls) -> "TranslationSection":
        """
        Initialises the English translation.
        """
        tree = ElementTree.parse(
            os.path.join(get_reggiedata_folder(), "translations", "strings.xml")
        )
        return cls._parse_tree(tree.getroot())

    @classmethod
    def from_xml(cls, language: str) -> "TranslationSection":
        """
        Loads the translation of the given language.
        :param language: The language folder name to fetch the translation file
        from.
        """
        tree = ElementTree.parse(
            os.path.join(
                get_reggiedata_folder(), "translations", language, "strings.xml"
            )
        )
        return cls._parse_tree(tree.getroot())

    @classmethod
    def _parse_tree(cls, element: ElementTree.Element) -> "TranslationSection":
        result: dict[str, str | TranslationSection] = {}
        for node in element:
            if node.tag == "section":
                result[node.attrib["id"]] = cls._parse_tree(node)
            elif node.tag == "string":
                result[node.attrib["id"]] = node.text or node.attrib["id"]

        return cls(result)
