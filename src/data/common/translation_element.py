import os
from typing import Any, Literal
from xml.etree import ElementTree

from data.common.utils import get_reggiedata_folder, get_root_path


class TranslationElement:
    def __init__(self, items: dict[str, "str | TranslationElement"] | None = None) -> None:
        self._items: dict[str, str | TranslationElement] = items or {}

    def section(self, key: str) -> "TranslationElement":
        result: str | TranslationElement | None = self
        stack_trace: list[str] = []
        for sub_key in key.split("."):
            if result == None:
                stack_trace.append(
                    f' - Could not find translation section for key "{sub_key}"'
                )
                continue
            result = result._items.get(sub_key)
            if not isinstance(result, TranslationElement):
                result = None
                stack_trace.append(
                    f' - Could not find translation section for key "{sub_key}"'
                )
        if not isinstance(result, TranslationElement):
            self._log_error("section", key, stack_trace)
            return TranslationElement()

        return result

    def string(self, key: str, *templates: tuple[str, Any]) -> str:
        keys: list[str] = key.split(".")
        result: str | TranslationElement | None = self
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
            if not isinstance(result, TranslationElement):
                result = None
                stack_trace.append(
                    f' - Could not find translation section for key "{sub_key}"'
                )

        if not isinstance(result, str):
            self._log_error("string", key, stack_trace)
            return key

        if templates:
            for template in templates:
                result = result.replace(template[0], str(template[1]))

        return convert_formatting(result)

    def string_list(self, *keys: str) -> list[str]:
        if len(keys) == 0:
            return [item for item in self._items.values() if isinstance(item, str)]
        return [self.string(key) for key in keys]

    @classmethod
    def init_as_english(cls) -> "TranslationElement":
        tree = ElementTree.parse(
            os.path.join(
                get_reggiedata_folder(), "translations", "strings.xml"
            )
        )
        return cls.parse_tree(tree.getroot())

    @classmethod
    def from_xml(cls, language: str) -> "TranslationElement":
        tree = ElementTree.parse(
            os.path.join(
                get_reggiedata_folder(), "translations", language, "strings.xml"
            )
        )
        return cls.parse_tree(tree.getroot())

    @classmethod
    def parse_tree(cls, element: ElementTree.Element) -> "TranslationElement":
        result: dict[str, str | TranslationElement] = {}
        for node in element:
            if node.tag == "section":
                result[node.attrib["id"]] = cls.parse_tree(node)
            elif node.tag == "string":
                result[node.attrib["id"]] = node.text or node.attrib["id"]

        return cls(result)

    def __repr__(self) -> str:
        result = "TranslationTree{"
        for index, item in enumerate(self._items.items()):
            result += repr(item)
            if index == len(self._items) - 1:
                break
            result += ", "

        return result + "}"

    def _log_error(
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
