import os
from typing import Any, Literal
from xml.etree import ElementTree

from data.common.utils import get_reggiedata_folder, get_root_path


class TranslationSection:
    """
    A basic translation section that contains translation strings or further
    translation sections.
    """
    def __init__(self, items: dict[str, "str | TranslationSection"] | None = None) -> None:
        self._items: dict[str, str | TranslationSection] = items or {}

    def section(self, key: str) -> "TranslationSection":
        """
        Returns a section within this section or any sub-section that matches
        the given key.

        :param key: The ID of the translation section to look for. Iterations
        deeper into this section can be achieved by separating the keys
        with a period.

        **Example**: Providing the key `common.greetings` will return the
        section with the ID `greetings` found within the `common` section.
        :return: A translation section that matches the hierarchy of the given
        key. If no section with the given ID was found, a warning will be
        logged and an empty section will be returned instead.
        """
        result: str | TranslationSection | None = self
        stack_trace: list[str] = []
        for sub_key in key.split("."):
            if result == None:
                stack_trace.append(
                    f' - Could not find translation section for key "{sub_key}"'
                )
                continue
            result = result._items.get(sub_key)
            if not isinstance(result, TranslationSection):
                result = None
                stack_trace.append(
                    f' - Could not find translation section for key "{sub_key}"'
                )
        if not isinstance(result, TranslationSection):
            self._log_key_error("section", key, stack_trace)
            return TranslationSection()

        return result

    def string(self, key: str, *templates: tuple[str, Any]) -> str:
        """
        Returns a string within this section or any sub-section that matches
        the given key.

        :param key: The ID of the translation string to look for. Iterations
        deeper into this section can be achieved by separating the keys
        with a period.

        **Example**: Providing the key `common.hello_world` will return the
        translation string with the ID `hello_world` found within the `common`
        section.
        :return: A translation string that matches the hierarchy of the given
        key. If no string with the given ID was found, a warning will be logged
        and the given key will be returned instead.
        """
        keys: list[str] = key.split(".")
        result: str | TranslationSection | None = self
        stack_trace: list[str] = []
        for index, sub_key in enumerate(keys):
            if result == None:
                stack_trace.append(
                    f' - Could not find translation section for key "{sub_key}"'
                )
                continue
            result = result._items.get(sub_key)
            if index == len(keys) - 1 and isinstance(result, str):
                break
            if not isinstance(result, TranslationSection):
                result = None
                stack_trace.append(
                    f' - Could not find translation section for key "{sub_key}"'
                )

        if not isinstance(result, str):
            self._log_key_error("string", key, stack_trace)
            return key

        if templates:
            for template in templates:
                result = result.replace(template[0], str(template[1]))

        return TranslationSection.convert_formatting(result)

    def string_list(self, *keys: str) -> list[str]:
        """
        Returns a list of strings within this section that matches the given
        key.

        :param keys: The IDs of the translation strings to look for. Iterations
        deeper into this section can be achieved by separating the keys
        with a period.

        **Example**: Providing the key `common.hello_world` will return the
        translation string with the ID `hello_world` found within the `common`
        section.

        If no keys are provided, all strings within this section will be
        returned instead. Strings from child sections are not included.
        :return: A list of translation strings that matches the hierarchies of
        the given keys. The length of the list is always equal to the amount of
        keys provided. If a string with a specific key could not be found, a
        warning will be logged and the given key will be added to the returned
        list instead.
        """
        if len(keys) == 0:
            return [item for item in self._items.values() if isinstance(item, str)]
        return [self.string(key) for key in keys]

    @classmethod
    def init_as_english(cls) -> "TranslationSection":
        tree = ElementTree.parse(
            os.path.join(
                get_reggiedata_folder(), "translations", "strings.xml"
            )
        )
        return cls._parse_tree(tree.getroot())

    @classmethod
    def from_xml(cls, language: str) -> "TranslationSection":
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

    def _log_key_error(
        self, type: Literal["section", "string"], key: str, stack_trace: list[str]
    ) -> None:
        message = f'[Warning] - Could not find translation {type} for key "{key}"{("\n" + "\n".join(stack_trace)) if stack_trace else ""}'
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
