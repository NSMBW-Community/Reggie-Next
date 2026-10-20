import os
import re
from xml.etree import ElementTree as etree

def update_main(path: str) -> None:
    """
    Updates a gamedef's main.xml
    """
    with open(path, 'r', encoding='utf-8') as f:
        data = f.read()

    # Fix old references
    regex_strings = [
        (r'<file name="bg(\w)" path="(.*?).txt"', r'<file name="bg\1" path="\2.xml"'),
        (r'name="music" path="(.*?).txt"', r'name="music" path="\1.xml"'),
        (r'name="zonethemes" path="(.*?).txt"', r'name="zonethemes" path="\1.xml"'),
        (r'name="ts1_descriptions" path="(.*?).txt"', r'name="ts1_descriptions" path="\1.xml"')
    ]

    for pattern, replace in regex_strings:
        data = re.sub(pattern, replace, data)

    with open(path, 'w', encoding='utf-8') as file_out:
        file_out.write(data)


def update_sprites_module(filename: str) -> None:
    """
    Fixes compatibility issues with sprites.py modules made for older versions of Reggie Next
    """
    with open(filename, "r", encoding="utf-8") as f:
        orig_data = f.read()

    # Fix the import
    new_data = orig_data.replace("PyQt5", "PyQt6")

    # Common PyQt5 -> 6 changes that need to be fixed
    pyqt_strings = [
        ("QPainter.Antialiasing",   "QPainter.RenderHint.Antialiasing"),
        ("Qt.SmoothTransformation", "Qt.TransformationMode.SmoothTransformation"),
        ("Qt.IgnoreAspectRatio",    "Qt.AspectRatioMode.IgnoreAspectRatio"),
        ("QPoint(",                 "QPointF("),
        ("Qt.transparent",          "Qt.GlobalColor.transparent"),
        ("Qt.Align",                "Qt.AlignmentFlag.Align")
    ]

    for old, new in pyqt_strings:
        new_data = new_data.replace(old, new)

    # Regex fixes
    regex_strings = [
        # Fix BlockContents accesses
        (r"\['BlockContents'\]\[(\d+)\]", r"['BlockContents\1']"),
        (r"\['BlockContents'\]\[(.*?)\]", r"[f'BlockContents{\1}']"),
        # Update GetImg() calls to the proper function
        (r"SLib\.GetImg\((\w?[\"']?[\w{}%\.]+[\"']?(?: ?% ?(?:(?:\([\w, +-\.()]+\))|(?:[\w +\-\.()]+)))?)(?:, ?False)?\)", r"SLib.GetPixmap(\1)"),
        (r"SLib\.GetImg\((\w?[\"']?[\w{}%\.]+[\"']?(?: ?% ?(?:(?:\([\w, +-\.()]+\))|(?:[\w +\-\.()]+)))?)(?:, ?True)\)", r"SLib.GetImage(\1)")
    ]

    for pattern, replace in regex_strings:
        new_data = re.sub(pattern, replace, new_data)

    # Fix old sprites_common imports
    new_data = new_data.replace("import sprites_common", "import data.common.sprites")

    # Fix (very rarely used) references to the sprite ID
    new_data = new_data.replace("parent.type", "parent.sprite_num")

    # All done, save the file
    with open(filename, 'w') as file_out:
        file_out.write(new_data)


def convert_txt_to_xml(path: str, split: str, root_name: str, element_name: str, has_key: bool = True) -> None:
    """
    Simple base for converting key-value txt files into an XML format
    """
    # XML exists, return
    if os.path.isfile(path):
        return

    txt_path = path.replace('.xml', '.txt')

    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            raw = [x.strip() for x in f]
    except FileNotFoundError:
        return

    root = etree.Element(root_name)

    for idx, line in enumerate(raw):
        # Make each element
        if has_key:
            data = line.split(split)
            element = etree.SubElement(root, element_name, id=data[0], name=data[1])
        else:
            element = etree.SubElement(root, element_name, id=str(idx), name=line)

    etree.indent(root, space='    ')
    tree = etree.ElementTree(root)
    tree.write(path, encoding='utf-8', xml_declaration=True)

    # Delete the text file
    os.remove(txt_path)
