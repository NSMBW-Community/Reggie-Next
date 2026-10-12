import os, re, shutil

# Compatibility fixes for gamedefs

def update_main(path: str):
    """
    Updates a gamedef's main.xml
    """
    with open(path, 'r', encoding='utf-8') as f:
        data = f.read()

    # This really only works if the patch creator doesn't use
    # their own filenames, but it's probably fine...
    fix_strings = [
        ('name="spritedata"',  'name="actordata"'),
        ('path="spritedata.xml"', 'path="actordata.xml"'),
        ('name="sprites"',  'name="actors"'),
        ('path="sprites.py"', 'path="actors.py"'),
        ('path="sprites"',  'path="actors"'),
    ]

    # Check for a sprites folder and rename it
    sprites_path = os.path.join(os.path.dirname(path), 'sprites')
    if os.path.isdir(sprites_path):
        dest = os.path.join(os.path.dirname(path), 'actors')
        os.rename(sprites_path, dest)

    for old, new in fix_strings:
        data = data.replace(old, new)

    with open(path, 'w', encoding='utf-8') as file_out:
        file_out.write(data)


def update_actors_module(path: str):
    """
    Fixes compatibility issues with actors.py modules made for older versions of Reggie Next
    """
    # Move sprites.py to actors.py
    sprites_path = os.path.join(os.path.dirname(path), 'sprites.py')
    if os.path.isfile(sprites_path):
        shutil.copy2(sprites_path, path)
        os.remove(sprites_path)

    with open(path, "r", encoding="utf-8") as f:
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
    new_data = new_data.replace("import src.data.common.sprites", "import data.common.sprites") # Only happens if updating during the refactoring

    # Fix (very rarely used) references to the sprite ID
    new_data = new_data.replace("parent.type", "parent.sprite_num")

    # Sprite -> Actor
    new_data = new_data.replace("SpriteItem", "ActorItem")
    new_data = new_data.replace("AuxiliarySpriteItem", "AuxiliaryActorItem")

    # All done, save the file
    with open(path, 'w') as file_out:
        file_out.write(new_data)


def update_actordata(path: str):
    """
    Updates actordata.xml
    """
    # Check if there's a spritedata.xml, and move it to actordata.xml
    spritedata_path = os.path.join(os.path.dirname(path), 'spritedata.xml')
    if os.path.isfile(spritedata_path):
        shutil.copy2(spritedata_path, path)
        print(path)
        os.remove(spritedata_path)

    with open(path, 'r', encoding='utf-8') as f:
        data = f.read()

    # Fix elements
    fix_strings = [
        # Sprite -> Actor fixes (only relevant if updating a spritedata XML)
        ('<sprites>',  '<actors>'),
        ('</sprites>', '</actors>'),
        ('<sprite ',    '<actor '), # Space to avoid catching <spritetex> elements
        ('</sprite>',  '</actor>'),
        ('sprite=',    'actor=')
    ]

    for old, new in fix_strings:
        data = data.replace(old, new)

    with open(path, 'w', encoding='utf-8') as file_out:
        file_out.write(data)
