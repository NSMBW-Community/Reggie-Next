import os
from xml.etree import ElementTree

from PyQt6 import QtCore, QtGui, QtWidgets

import globals_
from dirty import setting


class ReggieTheme:
    """
    Class that represents a Reggie theme
    """

    def __init__(self, folder=None):
        """
        Initializes the theme
        """
        self.initAsClassic()
        if folder and folder != "Classic": self.initFromFolder(folder)

    def initAsClassic(self):
        """
        Initializes the theme as the hardcoded Classic theme
        """
        self.fileName = 'Classic'
        self.styleSheet = ''
        self.formatver = 1.0
        self.version = 1.0
        self.themeName = globals_.trans.string('Themes', 0)
        self.creator = globals_.trans.string('Themes', 1)
        self.description = globals_.trans.string('Themes', 2)
        self.iconCacheSm = {}
        self.iconCacheLg = {}
        self.style = None
        self.forceUiColor = False
        self.forceStyleSheet = False

        # Add the colors                                                       # Descriptions:
        self.colors = {
            'bg': QtGui.QColor(119, 136, 153),  # Main scene background fill
            'comment_fill': QtGui.QColor(220, 212, 135, 120),  # Unselected comment fill
            'comment_fill_s': QtGui.QColor(254, 240, 240, 240),  # Selected comment fill
            'comment_lines': QtGui.QColor(192, 192, 192, 120),  # Unselected comment lines
            'comment_lines_s': QtGui.QColor(220, 212, 135, 240),  # Selected comment lines
            'entrance_fill': QtGui.QColor(190, 0, 0, 120),  # Unselected entrance fill
            'entrance_fill_s': QtGui.QColor(190, 0, 0, 240),  # Selected entrance fill
            'entrance_lines': QtGui.QColor(0, 0, 0),  # Unselected entrance lines
            'entrance_lines_s': QtGui.QColor(255, 255, 255),  # Selected entrance lines
            'grid': QtGui.QColor(255, 255, 255, 100),  # Grid
            'location_fill': QtGui.QColor(114, 42, 188, 70),  # Unselected location fill
            'location_fill_s': QtGui.QColor(170, 128, 215, 100),  # Selected location fill
            'location_lines': QtGui.QColor(0, 0, 0),  # Unselected location lines
            'location_lines_s': QtGui.QColor(255, 255, 255),  # Selected location lines
            'location_text': QtGui.QColor(255, 255, 255),  # Location text
            'object_fill_s': QtGui.QColor(255, 255, 255, 64),  # Select object fill
            'object_lines_s': QtGui.QColor(255, 255, 255),  # Selected object lines
            'object_lines_r': QtGui.QColor(0, 148, 255),  # Clicked object corner
            'overview_entrance': QtGui.QColor(255, 0, 0),  # Overview entrance fill
            'overview_location_fill': QtGui.QColor(114, 42, 188, 50),  # Overview location fill
            'overview_location_lines': QtGui.QColor(0, 0, 0),  # Overview location lines
            'overview_object': QtGui.QColor(255, 255, 255),  # Overview object fill
            'overview_sprite': QtGui.QColor(0, 92, 196),  # Overview sprite fill
            'overview_viewbox': QtGui.QColor(0, 0, 255),  # Overview background fill
            'overview_zone_fill': QtGui.QColor(47, 79, 79, 120),  # Overview zone fill
            'overview_zone_lines': QtGui.QColor(0, 255, 255),  # Overview zone lines
            'overview_path': QtGui.QColor(6, 249, 20),  # Overview path fill
            'path_connector': QtGui.QColor(6, 249, 20),  # Path node connecting lines
            'path_fill': QtGui.QColor(6, 249, 20, 120),  # Unselected path node fill
            'path_fill_s': QtGui.QColor(6, 249, 20, 240),  # Selected path node fill
            'path_lines': QtGui.QColor(0, 0, 0),  # Unselected path node lines
            'path_lines_s': QtGui.QColor(255, 255, 255),  # Selected path node lines
            'smi': QtGui.QColor(255, 255, 255, 80),  # Sprite movement indicator
            'sprite_fill_s': QtGui.QColor(255, 255, 255, 64),  # Selected sprite w/ image fill
            'sprite_lines_s': QtGui.QColor(255, 255, 255),  # Selected sprite w/ image lines
            'spritebox_fill': QtGui.QColor(0, 92, 196, 120),  # Unselected sprite w/o image fill
            'spritebox_fill_s': QtGui.QColor(0, 92, 196, 240),  # Selected sprite w/o image fill
            'spritebox_lines': QtGui.QColor(0, 0, 0),  # Unselected sprite w/o image fill
            'spritebox_lines_s': QtGui.QColor(255, 255, 255),  # Selected sprite w/o image fill
            'zone_entrance_helper': QtGui.QColor(190, 0, 0, 120),  # Zone entrance-placement left border indicator
            'zone_lines': QtGui.QColor(145, 200, 255, 176),  # Zone lines
            'zone_corner': QtGui.QColor(255, 255, 255),  # Zone grabbers/corners
            'zone_dark_fill': QtGui.QColor(0, 0, 0, 48),  # Zone fill when dark
            'zone_text': QtGui.QColor(44, 64, 84),  # Zone text
        }

    def initFromFolder(self, folder):
        """
        Initializes the theme from the folder
        """
        folder = os.path.join('reggiedata', 'themes', folder)

        try:
            _fileList = os.listdir(folder)
        except FileNotFoundError:
            # Return if the theme cannot be found
            # (default theme is already inited)
            return

        # Create a XML ElementTree
        maintree = ElementTree.parse(os.path.join(folder, 'main.xml'))
        root = maintree.getroot()

        # Parse the attributes of the <theme> tag
        if not self.parseMainXMLHead(root):
            # The attributes are messed up
            return

        # Parse the other nodes
        for node in root:
            if node.tag.lower() == 'colors':
                if 'file' not in node.attrib:
                    continue

                # Load the colors XML
                self.loadColorsXML(os.path.join(folder, node.attrib['file']))

            elif node.tag.lower() == 'qss':
                if 'file' not in node.attrib:
                    continue

                # Load the style sheet
                self.loadStyleSheet(os.path.join(folder, node.attrib['file']))

            elif node.tag.lower() == 'icons':
                if not all(thing in node.attrib for thing in ['size', 'folder']):
                    continue

                folderName = node.attrib['folder']
                big = node.attrib['size'].lower()[:2] == 'lg'
                cache = self.iconCacheLg if big else self.iconCacheSm

                # Load the icons
                for fileName in os.listdir(os.path.join(folder, folderName)):
                    iconName = fileName

                    # Remove the 'icon-' prefix and file extension
                    iconName = iconName.removeprefix('icon-')
                    iconName = iconName.removesuffix('.png')

                    with open(os.path.join(folder, folderName, fileName), "rb") as inf:
                        iconData = inf.read()

                    pix = QtGui.QPixmap()
                    if not pix.loadFromData(iconData):
                        continue

                    ico = QtGui.QIcon(pix)
                    cache[iconName] = ico

    def parseMainXMLHead(self, root):
        """
        Parses the main attributes of main.xml
        """
        max_support_version = 1.0
        self.styleSheet = ''

        # Check for required attributes
        if root.tag.lower() != 'theme':
            return False

        if 'format' in root.attrib:
            formatver = root.attrib['format']
            try:
                self.formatver = float(formatver)
            except ValueError:
                return False
        else:
            return False

        if self.formatver > max_support_version:
            return False

        if 'name' in root.attrib:
            self.themeName = root.attrib['name']
        else:
            return False

        # Check for optional attributes
        self.creator = root.get("creator", globals_.trans.string("Themes", 3))
        self.description = root.get("description", globals_.trans.string("Themes", 4))
        self.style = root.get("style")
        self.forceUiColor = root.get("forceUiColor", "false") == "true"
        self.forceStyleSheet = root.get("forceStyleSheet", "false") == "true"

        try:
            self.version = float(root.get("version", "1.0"))
        except ValueError:
            self.version = 1.0

        return True

    def loadColorsXML(self, file):
        """
        Loads a colors.xml file
        """
        try:
            tree = ElementTree.parse(file)
        except ElementTree.ParseError:
            return

        root = tree.getroot()
        if root.tag.lower() != 'colors':
            return False

        colorDict = {}
        for colorNode in root:
            if colorNode.tag.lower() != 'color':
                continue
            if not all(thing in colorNode.attrib for thing in ['id', 'value']):
                continue

            colorval = colorNode.attrib['value']
            colorval = colorval.removeprefix('#')

            a = 255
            try:
                if len(colorval) == 3:
                    # RGB
                    r = int(colorval[0], 16)
                    g = int(colorval[1], 16)
                    b = int(colorval[2], 16)
                elif len(colorval) == 4:
                    # RGBA
                    r = int(colorval[0], 16)
                    g = int(colorval[1], 16)
                    b = int(colorval[2], 16)
                    a = int(colorval[3], 16)
                elif len(colorval) == 6:
                    # RRGGBB
                    r = int(colorval[0:2], 16)
                    g = int(colorval[2:4], 16)
                    b = int(colorval[4:6], 16)
                elif len(colorval) == 8:
                    # RRGGBBAA
                    r = int(colorval[0:2], 16)
                    g = int(colorval[2:4], 16)
                    b = int(colorval[4:6], 16)
                    a = int(colorval[6:8], 16)
                else:
                    continue
            except ValueError:
                continue
            colorobj = QtGui.QColor(r, g, b, a)
            colorDict[colorNode.attrib['id']] = colorobj

        # Merge dictionaries
        self.colors.update(colorDict)

    def loadStyleSheet(self, file):
        """
        Loads a style.qss file
        """
        with open(file, 'r', encoding='utf-8') as inf:
            style = inf.read()

        self.styleSheet = style

    def color(self, name):
        """
        Returns a color
        """
        try:
            return self.colors[name]
        except KeyError:
            return None

    def GetIcon(self, name, big=False):
        """
        Returns an icon
        """
        cache = self.iconCacheLg if big else self.iconCacheSm

        if name not in cache:
            path = os.path.join('reggiedata', 'ico', 'lg' if big else 'sm', 'icon-')
            path += name
            cache[name] = QtGui.QIcon(path)

        return cache[name]


def SetAppStyle(styleKey=''):
    """
    Set the application window color
    """
    if globals_.app is None:
        return

    # Change the color if applicable
    if globals_.theme.color('ui') is not None and not globals_.theme.forceStyleSheet:
        globals_.app.setPalette(QtGui.QPalette(globals_.theme.color('ui')))

    # Change the style
    if not styleKey:
        styleKey = setting('uiStyle', "Fusion")
    style = QtWidgets.QStyleFactory.create(styleKey)
    globals_.app.setStyle(style)

    # Apply the style sheet, if exists
    if globals_.theme.styleSheet:
        globals_.app.setStyleSheet(globals_.theme.styleSheet)

    # Manually set the background color
    if globals_.theme.forceUiColor and not globals_.theme.forceStyleSheet:
        color = None
        qcolor = globals_.theme.color('ui')
        if qcolor is not None:
            color = qcolor.getRgb()

        if color is not None:
            bgColor = "#{:02x}{:02x}{:02x}".format(*tuple(x // 2 if x is not None else 0 for x in color[:3]))
            globals_.app.setStyleSheet(f"""
                QListView, QTreeWidget, QLineEdit, QDoubleSpinBox, QSpinBox, QTextEdit, QPlainTextEdit{{
                    background-color: {bgColor};
                }}""")

        # Fix disabled menubar items being nearly unreadable in some cases
        # (mainly in dark mode and/or when the UI color is overriden)
        globals_.app.setStyleSheet("""QMenu::item:disabled{color: #646464;}""")


def SetColorScheme():
    """
    Sets the application color scheme
    """
    if globals_.app is None:
        return

    style_hint = globals_.app.styleHints()
    if style_hint is not None:
        if globals_.DarkMode:
            style_hint.setColorScheme(QtCore.Qt.ColorScheme.Dark)
        else:
            style_hint.setColorScheme(QtCore.Qt.ColorScheme.Light)


def GetIcon(name: str, big=False):
    """
    Helper function to grab a specific icon
    """
    return globals_.theme.GetIcon(name, big)


def createHorzLine():
    f = QtWidgets.QFrame()
    f.setFrameStyle(QtWidgets.QFrame.Shape.HLine | QtWidgets.QFrame.Shadow.Sunken)
    return f


def createVertLine():
    f = QtWidgets.QFrame()
    f.setFrameStyle(QtWidgets.QFrame.Shape.VLine | QtWidgets.QFrame.Shadow.Sunken)
    return f


def LoadNumberFont():
    """
    Creates a valid font we can use to display the item numbers
    """
    if globals_.NumberFont is not None:
        return

    # this is a really crappy method, but I can't think of any other way
    # normal Qt defines Q_WS_WIN and Q_WS_MAC but we don't have that here
    s = QtCore.QSysInfo()
    if hasattr(s, 'WindowsVersion'):
        globals_.NumberFont = QtGui.QFont('Tahoma', 7)
    elif hasattr(s, 'MacintoshVersion'):
        globals_.NumberFont = QtGui.QFont('Lucida Grande', 9)
    else:
        globals_.NumberFont = QtGui.QFont('Sans', 8)


def clipStr(text: str, idealWidth: int, font=None):
    """
    Returns a shortened string, or None if it need not be shortened
    """
    if font is None: font = QtGui.QFont()
    width = QtGui.QFontMetrics(font).horizontalAdvance(text)
    if width <= idealWidth:
        return None

    # note that Qt has a builtin function for this:
    # QFontMetricsF::elidedText(text, Qt.TextElideMode.ElideNone, idealWidth)
    while width > idealWidth:
        text = text[:-1]
        width = QtGui.QFontMetrics(font).horizontalAdvance(text)

    return text


def setOverrideCursor(cursor: QtGui.QCursor | QtCore.Qt.CursorShape | None):
    """
    Safely override/restore the application cursor.
    Pass cursor as None to restore the previous cursor
    """
    if globals_.app is None:
        return

    if cursor is None:
        globals_.app.restoreOverrideCursor()
        return

    if globals_.app.overrideCursor() is None:
        globals_.app.setOverrideCursor(cursor)
    else:
        globals_.app.changeOverrideCursor(cursor)
