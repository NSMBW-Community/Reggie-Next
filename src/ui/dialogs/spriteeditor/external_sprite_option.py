import os
from xml.etree import ElementTree

from PyQt6 import QtCore, QtWidgets

import globals_
from src.ui.dialogs.spriteeditor.external_sprite_option_row import (
    ExternalSpriteOptionRow,
)


class ExternalSpriteOptionDialog(QtWidgets.QDialog):
    """
    Dialog for the external sprite option.
    """

    def __init__(self, type, current):
        """
        Initialise the dialog
        """
        QtWidgets.QDialog.__init__(self)

        # create edit thing based on type
        # each of these functions should assign the editing thing to self.widget
        self.type = type

        # Set appropriate window title
        types = ['actors', 'models', 'sfx', 'gfx']
        for idx, extType in enumerate(types):
            if extType == self.type:
                self.setWindowTitle(globals_.trans.string('ExternalOptionDlg', idx))

        items, order = self.loadItemsFromXML()
        self.fillWidgetFromItems(items, order)

        self.value = current

        # make the layout of ExternalSpriteOptionWidgets
        self.widget = QtWidgets.QWidget()
        self.buttons = []
        self.visibleEntries = []

        L = QtWidgets.QVBoxLayout()
        self.buttongroup = QtWidgets.QButtonGroup()

        # create a widget for every entry
        self.widgets = []
        for i, widget in enumerate(self.entries):
            button = QtWidgets.QRadioButton()
            button.setChecked(i == self.value)
            self.buttongroup.addButton(button, i)

            self.widgets.append(
                ExternalSpriteOptionRow(button, widget[0], widget[1])
            )

        self.widget.setLayout(L)

        # search thing
        searchbar = QtWidgets.QLineEdit()
        searchbar.textEdited.connect(self.search)

        L = QtWidgets.QHBoxLayout()
        L.addWidget(QtWidgets.QLabel(globals_.trans.string('ExternalOptionDlg', 4)))
        L.addWidget(searchbar)

        search = QtWidgets.QWidget()
        search.setLayout(L)

        # create layout
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        scrollWidget = QtWidgets.QScrollArea()
        scrollWidget.setWidget(self.widget)
        scrollWidget.setWidgetResizable(True)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(search)
        mainLayout.addWidget(scrollWidget)
        mainLayout.addWidget(buttonBox, 0, QtCore.Qt.AlignmentFlag.AlignBottom)

        self.setLayout(mainLayout)

        self.updateVisibleRows(list(range(len(self.entries))))

        # Keep col widths constant
        #layout = self.widget.layout()
        #colCount = layout.columnCount()
        #rowCount = layout.rowCount()

        #for column in range(colCount):
        #    for row in range(rowCount):
        #        try:
        #            width = layout.itemAtPosition(row, column).widget().width()
        #            layout.itemAtPosition(row, column).widget().setFixedWidth(width)
        #        except:
        #            pass

    def loadItemsFromXML(self):
        """
        Returns the items from the correct XML
        """
        # find correct xml
        filename = globals_.gamedef.externalFile(self.type + '.xml')
        if not os.path.isfile(filename):
            raise FileNotFoundError # file does not exist

        # parse the xml
        options = {}
        primary = []
        secondary = []

        tree = ElementTree.parse(filename)
        root = tree.getroot()

        primary += [None if x.strip().lower() == "[id]" else x.strip() for x in root.attrib['primary'].split(',')]

        secondary += [x.strip() for x in root.attrib['secondary'].split(',')]

        for option in root:
            # skip if this is not an <option>
            if option.tag.lower() != 'option':
                continue

            # read properties and put it in this dict
            properties = {}
            for prop in option:
                if prop.tag.lower() != 'property':
                    continue

                name = prop.attrib['name']
                value = prop.attrib['value']

                properties[name] = value

            # parse the value [can be hexadecimal, binary or octal]
            value = int(option.attrib['value'], 0)

            # save it
            options[value] = properties

        # delete the xml stuff
        del tree, root

        return (options, (primary, secondary))

    def fillWidgetFromItems(self, options, order):
        """
        Adds items to the layout
        """
        # list of widgets sorted by value
        self.entries = []

        for option in options:
            items = options[option]
            subwidgets = ([], [])

            for prop in order[0]:
                if prop == None:
                    value = option
                else:
                    value = items[prop]

                subwidgets[0].append(value)

            # secondary items are optional
            for prop in order[1]:
                if prop in items:
                    subwidgets[1].append(items[prop])

            self.entries.append(subwidgets)

    def setCurrentValue(self, value):
        """
        Sets the current value to 'value'
        """
        button = self.buttongroup.button(value)
        if button is not None:
            button.setChecked(True)

    def getValue(self):
        """
        Gets the current value
        """
        return self.buttongroup.checkedId()

    def search(self, text):
        """
        Only show the elements fulfilling the search for text
        """
        # TODO: maybe let another thread handle this...
        # Don't do anything if you search for fewer than 2 characters
        if len(text) < 2:
            return

        matches = lambda haystack, needle: haystack.lower().find(needle.lower()) >= 0

        matching = []
        for i, entry in enumerate(self.entries):
            for property in entry[0]: # primary
                if matches(str(property), text):
                    matching.append(i)
                    break
            else:
                for property in entry[1]: # secondary
                    if matches(str(property), text):
                        matching.append(i)
                        break

        self.updateVisibleRows(matching)

    def updateVisibleRows(self, new):
        """
        Makes sure we only show the correct rows
        """

        layout = self.widget.layout()
        if layout is None or not isinstance(layout, QtWidgets.QVBoxLayout):
            return

        # clear layout
        self.clearLayout(layout)

        # add back the correct ones
        for id in new:
            row = self.widgets[id]

            # add row to the layout
            layout.addWidget(row)

        # add stretch so the items align to the top
        layout.addStretch()

        self.visibleEntries = new

    def clearLayout(self, layout):
        """
        Removes all rows of the layout
        """
        while True:
            item = layout.takeAt(0)
            if item is None:
                break

            wid = item.widget()
            del item

            if wid is None:
                continue

            # don't delete the widget, since we might need to show it again later
            wid.setParent(None)
