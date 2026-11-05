import os
from typing import Any
from xml.etree import ElementTree

from data.common.utils import get_reggiedata_folder


class ReggieTranslation:
    """
    A translation of all visible Reggie strings
    """

    def __init__(self, name: str | None):
        """
        Creates a Reggie translation
        """
        self.InitAsEnglish()

        # Try to load it from an XML
        ok = self.InitFromXML(name)
        if not ok:
            self.InitAsEnglish()

    def InitAsEnglish(self) -> None:
        """
        Initializes the ReggieTranslation as the English translation
        """
        self.name = 'English'
        self.version = 1.0
        self.translator = 'Treeki, Tempus'

        # TODO: Add support for translating "external" folder XMLs
        self.files: dict[str | None, dict[str, str]] = { None: {
            'bga': os.path.join(get_reggiedata_folder(), 'bga.xml'),
            'bgb': os.path.join(get_reggiedata_folder(), 'bgb.xml'),
            'entrancetypes': os.path.join(get_reggiedata_folder(), 'entrancetypes.txt'),
            'levelnames': os.path.join(get_reggiedata_folder(), 'levelnames.xml'),
            'music': os.path.join(get_reggiedata_folder(), 'music.xml'),
            'spritecategories': os.path.join(get_reggiedata_folder(), 'spritecategories.xml'),
            'spritedata': os.path.join(get_reggiedata_folder(), 'spritedata.xml'),
            'tilesets': os.path.join(get_reggiedata_folder(), 'tilesets.xml'),
            'ts1_descriptions': os.path.join(get_reggiedata_folder(), 'ts1_descriptions.xml'),
            'zonethemes': os.path.join(get_reggiedata_folder(), 'zonethemes.xml'),
            'external-actors': os.path.join(get_reggiedata_folder(), 'external', 'actors.xml')
        }}

        self.strings: dict[str, dict[int, str | None | tuple[str | None, ...]]] = {
            'Gamedefs': {
                13: 'New Super Mario Bros. Wii'
            },
            'LocationDataEditor': {
                0: 'ID:',
                1: '[b]ID:[/b][br]Must be different from all other IDs',
                2: 'X Pos:',
                3: '[b]X Pos:[/b][br]Specifies the X position of the location',
                4: 'Y Pos:',
                5: '[b]Y Pos:[/b][br]Specifies the Y position of the location',
                6: 'Width:',
                7: '[b]Width:[/b][br]Specifies the width of the location',
                8: 'Height:',
                9: '[b]Height:[/b][br]Specifies the height of the location',
                10: 'Snap to Grid',
                11: '[b]Location [id]:[/b]',
                12: 'Modify Selected Location Properties',
                13: '[i]No Location Selected[/i]'
            },
            'MainWindow': {
                0: None,  # REMOVED: '[unsaved]'
                1: 'You\'re trying to paste over 300 items at once.[br]This may take a while (depending on your computer speed), are you sure you want to continue?',
                8: 'Warning',
            },
            'PathDataEditor': {
                0: 'Loops:',
                1: '[b]Loops:[/b][br]Anything following this path will wait for any delay set at the last node and then proceed back in a straight line to the first node, and continue.',
                2: 'Speed:',
                3: '[b]Speed:[/b][br]Unknown unit. Mess around and report your findings!',
                4: 'Accel:',
                5: '[b]Accel:[/b][br]Unknown unit. Mess around and report your findings!',
                6: 'Delay:',
                7: '[b]Delay:[/b][br]Amount of time to stop here (at this node) before continuing to next node. Unit is 1/60 of a second (60 for 1 second)',
                8: '[b]Path [id][/b]',
                9: '[b]Node [id][/b]',
                10: 'Modify Selected Path Node Properties',
                11: 'ID',
                12: 'Append Node to End of Path',
                13: 'Insert After Selected Node',
                14: '[b]Placement Mode:[/b][br]This determines how new nodes will be added onto the path.[br][b]Appending[/b] will add each node to the end of the path.[br][b]Inserting[/b] will add a new node after the [i]selected[/i] node.',
                15: '[i]No Node Selected[/i]'
            },
            'SpriteDataEditor': {
                0: 'Modify Selected Sprite Properties',
                1: '[b][name][/b]: [note]',
                2: '[b]Sprite Notes:[/b] [notes]',
                3: 'Modify Raw Data:',
                4: 'Notes',
                5: '[b]Unidentified/Unknown Sprite ([id])[/b]',
                6: '[b]Sprite [id]:[br][name][/b]',
                7: 'Object Files',
                8: '[b]This sprite loads:[/b][br]* [list]',
                9: '[b]Yoshi Notes:[/b] [notes]',
                10: 'Advanced Notes',
                11: '[b]Advanced Notes:[/b] [notes]',
                12: 'Notes',
                13: 'Read more...',
                14: 'Read less...',
                15: 'This sprite works properly with Yoshi.',
                16: None,  # REMOVED: '[b]Information:[/b]'
                17: 'Reset all settings',
                18: 'Check dependent sprites',
                19: 'Check dependency notes',
                20: 'Sprite [id]: required in area',
                21: 'Sprite [id]: suggested in area',
                22: 'Sprite [id]: required in zone',
                23: 'Sprite [id]: suggested in zone',
                24: None,  # REMOVED: 'Show raw data',
                25: 'This sprite has the following dependencies:',
                26: 'Add Sprite',
                27: 'Resize',
                28: 'NO TITLE GIVEN!',
                29: 'Next Free',
                30: 'Sprite [id]: required resource',
                31: 'Add to Loaded Sprites',
                32: 'Layer',
                33: '[b]Layer[/b]: This determines what layer the sprite will be active on. In almost all cases, you\'ll want to use Layer 1.',
                34: (
                    'Layer 1',
                    'Layer 2',
                    'Layer 0',
                ),
                35: '[id]: Undefined Entry',
                36: 'Unknown/Undefined',
                37: 'Default Properties',
            },
        }

    def InitFromXML(self, name: str | None) -> bool:
        """
        Parses the translation XML - returns True if successful, False if not.
        """
        if name in ('', None, 'None'):
            return False

        name = str(name)

        # Parse the file
        path = os.path.join(get_reggiedata_folder(), 'translations', name, 'main.xml')

        try:
            tree = ElementTree.parse(path)
        except FileNotFoundError:
            return False

        root = tree.getroot()

        # Add attributes
        # Name
        if 'name' not in root.attrib: return False
        self.name = root.attrib['name']
        # Version
        if 'version' not in root.attrib: return False
        self.version = float(root.attrib['version'])
        # Translator
        if 'translator' not in root.attrib: return False
        self.translator = root.attrib['translator']

        # Parse the nodes
        strings = False
        base_path = os.path.join(get_reggiedata_folder(), 'translations', name)
        for node in root:
            if node.tag.lower() == 'file':
                # It's a file node
                name = node.attrib['name']
                path = os.path.join(base_path, node.attrib['path'])
                self.files[None][name] = path
            elif node.tag.lower() == 'strings':
                # It's a strings node
                strings = os.path.join(base_path, node.attrib['path'])
            elif node.tag.lower() == 'for':
                # Translation for other gamedefs
                target = node.attrib['name']
                self.files[target] = {}
                for child in node:
                    if child.tag.lower() == 'file':
                        name = child.attrib['name']
                        self.files[target][name] = os.path.join(base_path, child.attrib['path'])

        # Get rid of the XML stuff
        del tree, root

        # Check for a strings node
        if not strings: return False

        # Parse the strings
        tree = ElementTree.parse(strings)
        root = tree.getroot()

        # Parse the nodes
        strings = {}
        for section in root:
            # Get a section
            if section.tag.lower() != 'section': continue
            id = section.attrib['id']
            sectionStrings = {}

            # Get the strings/stringlists in this section
            for string in section:
                if not hasattr(string, 'attrib'): continue
                strValue = None
                if string.tag.lower() == 'string':
                    # String node
                    strValue = string.text
                elif string.tag.lower() == 'stringlist':
                    # Not as easy, but not hard
                    strValue = []
                    for entry in string:
                        if entry.tag.lower() == 'entry':
                            strValue.append(entry.text)
                    strValue = tuple(strValue)

                # Add this string to sectionStrings
                idB = int(string.attrib['id'])
                if strValue is not None: sectionStrings[idB] = strValue

            # Add it to strings
            strings[id] = sectionStrings

        # Overwrite self.strings with strings
        for index in strings:
            if index not in self.strings: self.strings[index] = {}
            for index2 in strings[index]:
                self.strings[index][index2] = strings[index][index2]

        return True

    def string(self, name: str, numcode: int, *args: Any) -> str | None:
        """
        Usage: string(section, numcode, replacementDummy, replacement, replacementDummy2, replacement2, etc.)
        """

        # If there are errors when the string is found, return an error report instead
        try:
            return self.string_(name, numcode, *args)
        except TypeError as e:
            text = '\n\nReggieTranslation.string() ERROR: ' + str(numcode) + '; ' + str(args[0]) + '; ' + repr(e) + '\n'
            # do 3 things with the text - print it, write it to the error log, return it
            print(text)

            if not os.path.isfile('log.txt'):
                mode = 'w'
            else:
                mode = 'a'

            with open('log.txt', mode, encoding='utf-8') as f:
                f.write(text)

            return text

    def string_(self, name: str, numcode: int, *args: Any) -> str | None:
        """
        Gets a string from the translation and returns it
        """

        # Get the string
        astring = self.strings[name][numcode]
        if astring is None:
            return None
        if isinstance(astring, tuple):
            raise TypeError(f"String {name}/{numcode} is a tuple: {astring}. Use stringList() instead")

        # Perform any replacements
        i = 0
        while i < len(args):
            # Get the old string
            old = str(args[i])

            # Get the new string
            new = str(args[i + 1])

            # Replace
            astring = astring.replace(old, new)
            i += 2

        # Return it
        return convert_formatting(astring)

    def stringOneLine(self, name: str, numcode: int, *args: Any) -> str | None:
        """
        Works like string(), but guarantees that the resulting string will have
        no line breaks or \\<br>'s.
        """
        newstr = self.string(name, numcode, *args)
        if newstr is None:
            return None

        return newstr.replace('\n', ' ').replace('<br>', ' ')

    def stringList(self, section: str, numcode: int) -> tuple[str | None, ...] | None:
        """
        Returns a list of strings
        """
        strList = self.strings[section][numcode]
        if isinstance(strList, str):
            return ('ReggieTranslation.stringList() ERROR:',)

        return strList

    def path(self, key: str, gamedef: str | None = None) -> str | None:
        """
        Returns the path to the file indicated by key
        """
        if gamedef == self.string('Gamedefs', 13):  # 'New Super Mario Bros. Wii'
            gamedef = None

        try:
            return self.files[gamedef][key]
        except KeyError:
            return None

    def paths(self, key: str, gamedef_names: list[str | None] | None = None) -> list[str | None]:
        if gamedef_names is None:
            return [self.path(key)]

        return [self.path(key, name) for name in gamedef_names]

    def generateXML(self) -> None:
        """
        Generates a strings.xml and places it in the folder of reggie.py
        """

        # Sort self.strings
        sortedstrings = sorted(
            (
                (
                    key,
                    sorted(
                        self.strings[key].items(),
                        key=lambda entry: entry[0]),
                )
                for key in self.strings
            ),
            key=lambda entry: entry[0])

        # Create an XML
        root = ElementTree.Element('strings')
        for sectionname, section in sortedstrings:
            sectionElem = ElementTree.Element('section', {'id': sectionname})
            root.append(sectionElem)
            for stringid, string in section:
                if isinstance(string, (tuple, list)):
                    stringlistElem = ElementTree.Element('stringlist', {'id': str(stringid)})
                    sectionElem.append(stringlistElem)
                    for entryname in string:
                        entryElem = ElementTree.Element('entry')
                        entryElem.text = entryname
                        stringlistElem.append(entryElem)
                else:
                    stringElem = ElementTree.Element('string', {'id': str(stringid)})
                    stringElem.text = string
                    sectionElem.append(stringElem)

        # Indent everything
        ElementTree.indent(root, space='    ')

        # Provide sample info at the start, this is so the XML can be quickly updated alongside this
        header = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!-- Reggie! Next sample translations XML -->\n'
            '<!-- &lt;   = < -->\n'
            '<!-- &gt;   = > -->\n'
            '<!-- &quot; = " -->\n'
            '<!-- &lt;font color=&quot;COLOR&quot;&gt;TEXT TEXT TEXT.&lt;/font&gt; = Colored Text -->\n'
            '<!-- Bracketed placeholders ([id], [num], [x], [y], etc.) should not be modified, the editor fills these in with proper data -->\n\n'

            '<!-- The contents of this file are based on (and should be identical to) the default English strings in translation.py -->\n'
            '<!-- Removed strings are self-closing and do not contain any text. These can be ignored while translating -->\n\n'
        )

        raw_string = ElementTree.tostring(root, encoding='utf-8').decode('utf-8')
        path = os.path.join(get_reggiedata_folder(), 'translations', 'strings.xml')

        with open(path, 'w', encoding='utf-8') as f:
            f.write(header + raw_string + '\n')

# TODO: This might belong in another file?
@staticmethod
def convert_formatting(text: str) -> str:
    """
    Performs automatic replacements on text strings.
    Intended for XMLs where proper formatting can't be applied
    """
    replace = {
        '[br]': '<br>',
        '[b]': '<b>',
        '[/b]': '</b>',
        '[i]': '<i>',
        '[/i]': '</i>',
        '[a': '<a',
        '"]': '">',  # Workaround
        '[/a]': '</a>',
        '\\n': '\n',
        '//n': '\n',
        '[tm]': '™',
        '[small]': '<small>',
        '[/small]': '</small>',
    }

    for old, new in replace.items():
        text = text.replace(old, new)

    return text
