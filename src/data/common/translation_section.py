import os
from typing import Any
from xml.etree import ElementTree

from data.common.utils import get_reggiedata_folder, get_root_path


class TranslationSection:
    """
    A basic translation section that contains sub-sections or translation
    strings as well as methods to extract said sub-sections and strings.
    """

    def __init__(
        self, items: dict[str, "str | TranslationSection"] | None = None
    ) -> None:
        self._items: dict[str, str | TranslationSection] = items or {}

    def string(self, id: str, *templates: tuple[str, Any]) -> str:
        """
        :param id: The ID of the translation string to look for. Iterations
        into deeper sections can be achieved by separating the ID with periods.

        **Example**: Providing the ID `common.hello_world` will return the
        translation string with the ID `hello_world` found within the `common`
        section.
        :return: A translation string whose ID matches the structure of the
        given id. If no string with the given ID was found, a warning will be
        logged and said ID will be returned instead.
        """
        result, stack_trace = self._fetch(id)

        if not isinstance(result, str):
            self._log_id_error(id, stack_trace)
            return id

        if templates:
            for template in templates:
                result = result.replace(template[0], str(template[1]))

        return TranslationSection.convert_formatting(result)

    def string_list(self, id: str, *ids: str) -> list[str]:
        """
        :param id: The ID of the first translation string to look for.
        Iterations into deeper sections can be achieved by separating the ID
        with periods.

        **Example**: Providing the ID `common.hello_world` will return the
        translation string with the ID `hello_world` found within the `common`
        section.
        :param ids: Additional IDs of strings or translation sections that
        should be fetched.
        :return: A list of translation strings whose IDs matche the structures
        of the given IDs. If an ID matches a translation section, all strings
        within that section but no sub-section will be added to the list.
        Therefore, the length of the returned list is always greater than or
        equal to the amount of IDs provided.
        """
        result: list[str] = []
        for sub_id in (id, *ids):
            sub_result, stack_trace = self._fetch(sub_id)
            if sub_result is None or len(stack_trace):
                self._log_id_error(id, stack_trace)
                continue

            if isinstance(sub_result, str):
                result.append(sub_result)
                continue

            result += [
                item for item in sub_result._items.values() if isinstance(item, str)
            ]

        return result

    def _fetch(self, id: str) -> tuple["str | TranslationSection | None", list[str]]:
        ids: list[str] = id.split(".")
        result: str | TranslationSection | None = self
        stack_trace: list[str] = []
        for index, sub_id in enumerate(ids):
            if result is None:
                stack_trace.append(
                    f' - Could not find translation section for ID "{sub_id}"'
                )
                continue
            result = result._items.get(sub_id)
            if index == len(ids) - 1 and isinstance(result, str):
                break
            if not isinstance(result, TranslationSection):
                result = None
                stack_trace.append(
                    f' - Could not find translation section for ID "{sub_id}"'
                )

        return (result, stack_trace)

    def _log_id_error(self, id: str, stack_trace: list[str]) -> None:
        message = (
            "[Warning] - Could not find translation(s) for ID"
            + f' "{id}"{("\n" + "\n".join(stack_trace)) if stack_trace else ""}'
        )
        print(message)

        if not os.path.isfile(os.path.join(get_root_path(), "log.txt")):
            mode = "w"
        else:
            mode = "a"

        with open("log.txt", mode, encoding="utf-8") as f:
            f.write(message)

    def __or__(self, other: "TranslationSection") -> "TranslationSection":
        for key in self._items | other._items:
            this_item = self._items.get(key)
            other_item = other._items.get(key)

            if this_item == other_item:
                continue

            if isinstance(this_item, TranslationSection) and isinstance(
                other_item, TranslationSection
            ):
                # both are sections; merge via OR
                self._items[key] = this_item | other_item
                continue

            if (isinstance(this_item, str) and isinstance(other_item, str)) or (
                this_item is None and other_item is not None
            ):
                # both are strings or string does not exist; override original / add
                self._items[key] = other_item
                continue

        return self

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
