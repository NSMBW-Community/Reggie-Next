
from PyQt5 import QtWidgets, QtGui, QtCore

from ui import GetIcon, clipStr
import globals_
import spritelib as SLib
from levelitems import ListWidgetItem_SortsByOther, SpriteItem, ZoneItem
from dirty import SetDirty
from zones import CameraModeZoomSettingsLayout
from ui import createHorzLine

class AboutDialog(QtWidgets.QDialog):
    """
    The About info for Reggie
    """

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle(globals_.trans.string('AboutDlg', 0))
        self.setWindowIcon(GetIcon('reggie'))

        # Open the readme file
        readme = ""
        with open('readme.md', 'r') as f:
            readme = f.read()

        # Logo
        logo = QtGui.QPixmap('reggiedata/about.png')
        logoLabel = QtWidgets.QLabel()
        logoLabel.setPixmap(logo)
        logoLabel.setContentsMargins(16, 4, 32, 4)

        # Description
        description = '<html><head><style type="text/CSS">'
        description += 'body {font-family: Calibri}'
        description += '.main {font-size: 12px}'
        description += '</style></head><body>'
        description += '<center><h1><i>Reggie Next</i> Level Editor</h1><div class="main">'
        description += '<i>Reggie Next Level Editor</i> is an open-source project, started by Treeki in 2010 and forked by RoadrunnerWMC in 2013, that aims to bring you the fun of designing original New Super Mario Bros. Wii&trade;-compatible levels.<br>'
        description += 'Interested? Join the <a href="https://discord.gg/XnQJnwa">Discord server</a> to get in touch with the current developer(s).<br>'
        description += '</div></center></body></html>'

        # Description label
        descLabel = QtWidgets.QLabel()
        descLabel.setText(description)
        descLabel.setMinimumWidth(512)
        descLabel.setWordWrap(True)

        # Readme.md viewer
        readmeView = QtWidgets.QPlainTextEdit()
        readmeView.setPlainText(readme)
        readmeView.setReadOnly(True)

        # Buttonbox
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.accept)

        # Main layout
        L = QtWidgets.QGridLayout()
        L.addWidget(logoLabel, 0, 0, 2, 1)
        L.addWidget(descLabel, 0, 1)
        L.addWidget(readmeView, 1, 1)
        L.addWidget(buttonBox, 2, 0, 1, 2)
        L.setRowStretch(1, 1)
        L.setColumnStretch(1, 1)
        self.setLayout(L)


class ObjectShiftDialog(QtWidgets.QDialog):
    """
    Lets you pick an amount to shift selected items by
    """

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle(globals_.trans.string('ShftItmDlg', 0))
        self.setWindowIcon(GetIcon('move'))

        self.XOffset = QtWidgets.QSpinBox()
        self.XOffset.setRange(-16384, 16383)

        self.YOffset = QtWidgets.QSpinBox()
        self.YOffset.setRange(-8192, 8191)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        moveLayout = QtWidgets.QFormLayout()
        offsetlabel = QtWidgets.QLabel(globals_.trans.string('ShftItmDlg', 2))
        offsetlabel.setWordWrap(True)
        moveLayout.addWidget(offsetlabel)
        moveLayout.addRow(globals_.trans.string('ShftItmDlg', 3), self.XOffset)
        moveLayout.addRow(globals_.trans.string('ShftItmDlg', 4), self.YOffset)

        moveGroupBox = QtWidgets.QGroupBox(globals_.trans.string('ShftItmDlg', 1))
        moveGroupBox.setLayout(moveLayout)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(moveGroupBox)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)


class ObjectTilesetSwapDialog(QtWidgets.QDialog):
    """
    Lets you pick tilesets to swap objects to
    """

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle('Swap Objects\' Tilesets')
        self.setWindowIcon(GetIcon('swap'))

        # Create widgets
        self.FromTS = QtWidgets.QSpinBox()
        self.FromTS.setRange(1, 4)

        self.ToTS = QtWidgets.QSpinBox()
        self.ToTS.setRange(1, 4)

        # Swap layouts
        swapLayout = QtWidgets.QFormLayout()

        swapLayout.addRow('From Tileset:', self.FromTS)
        swapLayout.addRow('To Tileset:', self.ToTS)

        self.DoExchange = QtWidgets.QCheckBox('Exchange (perform 2-way conversion)')

        # Buttonbox
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        # Main layout
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(swapLayout)
        mainLayout.addWidget(self.DoExchange)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)


class ObjectTypeSwapDialog(QtWidgets.QDialog):
    """
    Lets you pick object types to swap objects to
    """

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle(globals_.trans.string("MenuItems", 106))
        self.setWindowIcon(GetIcon('swap'))

        # Create widgets
        self.FromType = QtWidgets.QSpinBox()
        self.FromType.setRange(0, 255)

        self.ToType = QtWidgets.QSpinBox()
        self.ToType.setRange(0, 255)

        self.FromTileset = QtWidgets.QSpinBox()
        self.FromTileset.setRange(1, 4)

        self.ToTileset = QtWidgets.QSpinBox()
        self.ToTileset.setRange(1, 4)

        self.DoExchange = QtWidgets.QCheckBox('Exchange (perform 2-way conversion)')

        # Swap layout
        swapLayout = QtWidgets.QGridLayout()

        swapLayout.addWidget(QtWidgets.QLabel('From Object:'), 0, 0)
        swapLayout.addWidget(self.FromType, 0, 1)

        swapLayout.addWidget(QtWidgets.QLabel('From Tileset:'), 1, 0)
        swapLayout.addWidget(self.FromTileset, 1, 1)

        swapLayout.addWidget(QtWidgets.QLabel('To Object:'), 0, 2)
        swapLayout.addWidget(self.ToType, 0, 3)

        swapLayout.addWidget(QtWidgets.QLabel('To Tileset:'), 1, 2)
        swapLayout.addWidget(self.ToTileset, 1, 3)

        # Buttonbox
        self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Apply | QtWidgets.QDialogButtonBox.Close)
        self.buttons.clicked.connect(self.button_clicked)

        # Main layout
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(swapLayout)
        mainLayout.addWidget(self.DoExchange)
        mainLayout.addWidget(self.buttons)
        self.setLayout(mainLayout)

    def button_clicked(self, button):
        """
        Handles one of the buttons being pressed and calls the correct handler.
        """
        role = self.buttons.buttonRole(button)

        if role == QtWidgets.QDialogButtonBox.RejectRole:
            # The close button was pressed
            self.reject()
        elif role == QtWidgets.QDialogButtonBox.ApplyRole:
            # The apply button was pressed
            self.swap_tiles()
        else:
            raise ValueError("ObjectTypeSwapDialog: Unknown role on pressed button. " + repr(role))

    def swap_tiles(self):
        """
        Actually does the swapping
        """
        from_type = self.FromType.value()
        from_tileset = self.FromTileset.value() - 1
        to_type = self.ToType.value()
        to_tileset = self.ToTileset.value() - 1
        do_exchange = self.DoExchange.isChecked()

        # If we don't need to do anything, don't do anything.
        if from_type == to_type and from_tileset == to_tileset:
            return

        for layer in globals_.Area.layers:
            for nsmbobj in layer:
                if nsmbobj.type == from_type and nsmbobj.tileset == from_tileset:
                    nsmbobj.SetType(to_tileset, to_type)
                    SetDirty()
                elif do_exchange and nsmbobj.type == to_type and nsmbobj.tileset == to_tileset:
                    nsmbobj.SetType(from_tileset, from_type)
                    SetDirty()


class MetaInfoDialog(QtWidgets.QDialog):
    """
    Allows the user to enter in various meta-info to be kept in the level for display
    """

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle(globals_.trans.string('InfoDlg', 0))
        self.setWindowIcon(GetIcon('info'))

        title = globals_.Area.Metadata.strData('Title')
        author = globals_.Area.Metadata.strData('Author')
        group = globals_.Area.Metadata.strData('Group')
        website = globals_.Area.Metadata.strData('Website')
        creator = globals_.Area.Metadata.strData('Creator')
        password = globals_.Area.Metadata.strData('Password')
        if title is None: title = '-'
        if author is None: author = '-'
        if group is None: group = '-'
        if website is None: website = '-'
        if creator is None: creator = '(unknown)'
        if password is None: password = ''

        self.levelName = QtWidgets.QLineEdit()
        self.levelName.setMaxLength(128)
        self.levelName.setReadOnly(True)
        self.levelName.setMinimumWidth(320)
        self.levelName.setText(title)

        self.Author = QtWidgets.QLineEdit()
        self.Author.setMaxLength(128)
        self.Author.setReadOnly(True)
        self.Author.setMinimumWidth(320)
        self.Author.setText(author)

        self.Group = QtWidgets.QLineEdit()
        self.Group.setMaxLength(128)
        self.Group.setReadOnly(True)
        self.Group.setMinimumWidth(320)
        self.Group.setText(group)

        self.Website = QtWidgets.QLineEdit()
        self.Website.setMaxLength(128)
        self.Website.setReadOnly(True)
        self.Website.setMinimumWidth(320)
        self.Website.setText(website)

        self.Password = QtWidgets.QLineEdit()
        self.Password.setMaxLength(128)
        self.Password.textChanged.connect(self.PasswordEntry)
        self.Password.setMinimumWidth(320)

        self.changepw = QtWidgets.QPushButton(globals_.trans.string('InfoDlg', 1))

        if password != '':
            self.levelName.setReadOnly(False)
            self.Author.setReadOnly(False)
            self.Group.setReadOnly(False)
            self.Website.setReadOnly(False)
            self.changepw.setDisabled(False)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.addButton(self.changepw, buttonBox.ActionRole)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        self.changepw.clicked.connect(self.ChangeButton)
        self.changepw.setDisabled(True)

        self.lockedLabel = QtWidgets.QLabel(globals_.trans.string('InfoDlg', 2))

        infoLayout = QtWidgets.QFormLayout()
        infoLayout.addWidget(self.lockedLabel)
        infoLayout.addRow(globals_.trans.string('InfoDlg', 3), self.Password)
        infoLayout.addRow(globals_.trans.string('InfoDlg', 4), self.levelName)
        infoLayout.addRow(globals_.trans.string('InfoDlg', 5), self.Author)
        infoLayout.addRow(globals_.trans.string('InfoDlg', 6), self.Group)
        infoLayout.addRow(globals_.trans.string('InfoDlg', 7), self.Website)

        self.PasswordLabel = infoLayout.labelForField(self.Password)

        levelIsLocked = password != ''
        self.lockedLabel.setVisible(levelIsLocked)
        self.PasswordLabel.setVisible(levelIsLocked)
        self.Password.setVisible(levelIsLocked)

        infoGroupBox = QtWidgets.QGroupBox(globals_.trans.string('InfoDlg', 8, '[name]', creator))
        infoGroupBox.setLayout(infoLayout)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(infoGroupBox)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.PasswordEntry('')

    def PasswordEntry(self, text):
        pswd = globals_.Area.Metadata.strData('Password')
        if pswd is None: pswd = ''
        if text == pswd:
            self.levelName.setReadOnly(False)
            self.Author.setReadOnly(False)
            self.Group.setReadOnly(False)
            self.Website.setReadOnly(False)
            self.changepw.setDisabled(False)
        else:
            self.levelName.setReadOnly(True)
            self.Author.setReadOnly(True)
            self.Group.setReadOnly(True)
            self.Website.setReadOnly(True)
            self.changepw.setDisabled(True)


        #   To all would be crackers who are smart enough to reach here:
        #
        #   Make your own damn levels.
        #
        #
        #
        #       - The management
        #

    def ChangeButton(self):
        """
        Allows the changing of a given password
        """

        class ChangePWDialog(QtWidgets.QDialog):
            """
            Dialog
            """

            def __init__(self):
                QtWidgets.QDialog.__init__(self)
                self.setWindowTitle(globals_.trans.string('InfoDlg', 9))
                self.setWindowIcon(GetIcon('info'))

                self.New = QtWidgets.QLineEdit()
                self.New.setMaxLength(64)
                self.New.textChanged.connect(self.PasswordMatch)
                self.New.setMinimumWidth(320)

                self.Verify = QtWidgets.QLineEdit()
                self.Verify.setMaxLength(64)
                self.Verify.textChanged.connect(self.PasswordMatch)
                self.Verify.setMinimumWidth(320)

                self.Ok = QtWidgets.QPushButton('OK')
                self.Cancel = QtWidgets.QDialogButtonBox.Cancel

                buttonBox = QtWidgets.QDialogButtonBox()
                buttonBox.addButton(self.Ok, buttonBox.AcceptRole)
                buttonBox.addButton(self.Cancel)

                buttonBox.accepted.connect(self.accept)
                buttonBox.rejected.connect(self.reject)
                self.Ok.setDisabled(True)

                infoLayout = QtWidgets.QFormLayout()
                infoLayout.addRow(globals_.trans.string('InfoDlg', 10), self.New)
                infoLayout.addRow(globals_.trans.string('InfoDlg', 11), self.Verify)

                infoGroupBox = QtWidgets.QGroupBox(globals_.trans.string('InfoDlg', 12))

                infoLabel = QtWidgets.QVBoxLayout()
                infoLabel.addWidget(QtWidgets.QLabel(globals_.trans.string('InfoDlg', 13)), 0, QtCore.Qt.AlignCenter)
                infoLabel.addLayout(infoLayout)
                infoGroupBox.setLayout(infoLabel)

                mainLayout = QtWidgets.QVBoxLayout()
                mainLayout.addWidget(infoGroupBox)
                mainLayout.addWidget(buttonBox)
                self.setLayout(mainLayout)

            def PasswordMatch(self, text):
                self.Ok.setDisabled(self.New.text() != self.Verify.text() and self.New.text() != '')

        dlg = ChangePWDialog()
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.lockedLabel.setVisible(True)
            self.Password.setVisible(True)
            self.PasswordLabel.setVisible(True)
            pswd = str(dlg.Verify.text())
            globals_.Area.Metadata.setStrData('Password', pswd)
            self.Password.setText(pswd)
            SetDirty()

            self.levelName.setReadOnly(False)
            self.Author.setReadOnly(False)
            self.Group.setReadOnly(False)
            self.Website.setReadOnly(False)
            self.changepw.setDisabled(False)


class ScreenCapChoiceDialog(QtWidgets.QDialog):
    """
    Dialog which lets you choose which zone to take a pic of
    """

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle(globals_.trans.string('ScrShtDlg', 0))
        self.setWindowIcon(GetIcon('screenshot'))

        self.zoneCombo = QtWidgets.QComboBox()
        self.zoneCombo.addItem(globals_.trans.string('ScrShtDlg', 1))
        self.zoneCombo.addItem(globals_.trans.string('ScrShtDlg', 2))
        for i in range(len(globals_.Area.zones)):
            self.zoneCombo.addItem(globals_.trans.string('ScrShtDlg', 3, '[zone]', i + 1))

        self.hide_background = QtWidgets.QCheckBox()
        self.save_img = QtWidgets.QRadioButton()
        self.save_clip = QtWidgets.QRadioButton()

        self.save_img.setChecked(True)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QtWidgets.QFormLayout()
        mainLayout.addRow("Target", self.zoneCombo)
        mainLayout.addRow("Hide background", self.hide_background)
        mainLayout.addRow("Save image to file", self.save_img)
        mainLayout.addRow("Copy image", self.save_clip)
        mainLayout.addRow(buttonBox)
        self.setLayout(mainLayout)


class AutoSavedInfoDialog(QtWidgets.QDialog):
    """
    Dialog which lets you know that an auto saved level exists
    """

    def __init__(self, filename):
        """
        Creates and initializes the dialog
        """
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle(globals_.trans.string('AutoSaveDlg', 0))
        self.setWindowIcon(GetIcon('save'))

        mainlayout = QtWidgets.QVBoxLayout(self)

        hlayout = QtWidgets.QHBoxLayout()

        icon = QtWidgets.QLabel()
        hlayout.addWidget(icon)

        label = QtWidgets.QLabel(globals_.trans.string('AutoSaveDlg', 1, '[path]', filename))
        label.setWordWrap(True)
        hlayout.addWidget(label)
        hlayout.setStretch(1, 1)

        buttonbox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.No | QtWidgets.QDialogButtonBox.Yes)
        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)

        mainlayout.addLayout(hlayout)
        mainlayout.addWidget(buttonbox)


class AreaChoiceDialog(QtWidgets.QDialog):
    """
    Dialog which lets you choose an area
    """

    def __init__(self, areacount):
        """
        Creates and initializes the dialog
        """
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle(globals_.trans.string('AreaChoiceDlg', 0))
        self.setWindowIcon(GetIcon('areas'))

        self.areaCombo = QtWidgets.QComboBox()
        for i in range(areacount):
            self.areaCombo.addItem(globals_.trans.string('AreaChoiceDlg', 1, '[num]', i + 1))

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.areaCombo)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)


class DiagnosticToolDialog(QtWidgets.QDialog):
    """
    Dialog which checks for errors within the level
    """

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle(globals_.trans.string('Diag', 0))
        self.setWindowIcon(GetIcon('diagnostics'))

        # CheckFunctions: (icon, description, function, iscritical)
        self.CheckFunctions = (('objects', globals_.trans.string('Diag', 2), self.ObjsInTileset, True),
                               ('sprites', globals_.trans.string('Diag', 3), self.CrashSprites, False),
                               ('sprites', globals_.trans.string('Diag', 4), self.CrashSpriteSettings, True),
                               ('sprites', globals_.trans.string('Diag', 5), self.TooManySprites, False),
                               ('entrances', globals_.trans.string('Diag', 6), self.DuplicateEntranceIDs, True),
                               ('entrances', globals_.trans.string('Diag', 7), self.NoStartEntrance, True),
                               ('entrances', globals_.trans.string('Diag', 8), self.EntranceTooCloseToZoneEdge, False),
                               ('entrances', globals_.trans.string('Diag', 9), self.EntranceOutsideOfZone, False),
                               ('zones', globals_.trans.string('Diag', 10), self.TooManyZones, True),
                               ('zones', globals_.trans.string('Diag', 11), self.NoZones, True),
                               ('zones', globals_.trans.string('Diag', 12), self.ZonesTooClose, True),
                               ('zones', globals_.trans.string('Diag', 13), self.ZonesTooCloseToAreaEdges, True),
                               ('zones', globals_.trans.string('Diag', 14), self.BiasNotEnabled, False),
                               ('zones', globals_.trans.string('Diag', 15), self.ZonesTooBig, True),
                               )

        box = QtWidgets.QGroupBox(globals_.trans.string('Diag', 17))
        self.errorLayout = QtWidgets.QVBoxLayout()
        result, numErrors = self.populateLists()
        box.setLayout(self.errorLayout)

        self.updateHeader(result)
        hW = QtWidgets.QWidget()
        hW.setLayout(self.header)

        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addWidget(hW)
        self.mainLayout.addWidget(box)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)

    def updateHeader(self, testresult, secondTime=False):
        """
        Creates the header
        """
        self.header = QtWidgets.QGridLayout()
        self.header.addWidget(QtWidgets.QLabel(globals_.trans.string('Diag', 18)), 0, 0, 1, 3)

        pointsize = 14  # change this if you don't like it
        if testresult is None:  # good
            L = QtWidgets.QLabel()
            L.setPixmap(GetIcon('check', True).pixmap(64, 64))
            self.header.addWidget(L, 1, 0)

            px = QtGui.QPixmap(64, pointsize)
            px.fill(QtGui.QColor(0, 0, 0, 0))
            p = QtGui.QPainter(px)
            f = p.font()
            f.setPointSize(pointsize)
            p.setFont(f)
            p.setPen(QtGui.QColor(0, 200, 0))
            p.drawText(0, pointsize, globals_.trans.string('Diag', 19))
            del p
            L = QtWidgets.QLabel()
            L.setPixmap(px)
            self.header.addWidget(L, 1, 1)

            self.header.addWidget(QtWidgets.QLabel(globals_.trans.string('Diag', 20)), 1, 2)
        elif not testresult:  # warnings
            L = QtWidgets.QLabel()
            L.setPixmap(GetIcon('warning', True).pixmap(64, 64))
            self.header.addWidget(L, 1, 0)

            px = QtGui.QPixmap(128, int(pointsize * 3 / 2))
            px.fill(QtGui.QColor(0, 0, 0, 0))
            p = QtGui.QPainter(px)
            f = p.font()
            f.setPointSize(pointsize)
            p.setFont(f)
            p.setPen(QtGui.QColor(210, 210, 0))
            p.drawText(0, pointsize, globals_.trans.string('Diag', 21))
            del p
            L = QtWidgets.QLabel()
            L.setPixmap(px)
            self.header.addWidget(L, 1, 1)

            self.header.addWidget(QtWidgets.QLabel(globals_.trans.string('Diag', 22)), 1, 2)
        else:  # bad
            L = QtWidgets.QLabel()
            L.setPixmap(GetIcon('delete', True).pixmap(64, 64))
            self.header.addWidget(L, 1, 0)

            px = QtGui.QPixmap(72, pointsize)
            px.fill(QtGui.QColor(0, 0, 0, 0))
            p = QtGui.QPainter(px)
            f = p.font()
            f.setPointSize(pointsize)
            p.setFont(f)
            p.setPen(QtGui.QColor(255, 0, 0))
            p.drawText(0, pointsize, globals_.trans.string('Diag', 23))
            del p
            L = QtWidgets.QLabel()
            L.setPixmap(px)
            self.header.addWidget(L, 1, 1)

            self.header.addWidget(QtWidgets.QLabel(globals_.trans.string('Diag', 24)), 1, 2)

        if secondTime:
            w = QtWidgets.QWidget()
            w.setLayout(self.header)
            self.mainLayout.takeAt(0).widget().hide()
            self.mainLayout.insertWidget(0, w)

    def populateLists(self):
        """
        Runs the check functions and adds items to the list if needed
        """
        self.buttonHandlers = []

        self.errorList = QtWidgets.QListWidget()
        self.errorList.setSelectionMode(self.errorList.MultiSelection)

        foundAnything = False
        foundCritical = False
        for ico, desc, fxn, isCritical in self.CheckFunctions:
            if fxn('c'):

                foundAnything = True
                if isCritical: foundCritical = True

                item = QtWidgets.QListWidgetItem()
                item.setText(desc)
                if isCritical:
                    item.setForeground(QtGui.QColor(255, 0, 0))
                else:
                    item.setForeground(QtGui.QColor(172, 172, 0))
                item.setIcon(GetIcon(ico))
                item.fix = fxn

                self.errorList.addItem(item)

        self.fixBtn = QtWidgets.QPushButton(globals_.trans.string('Diag', 25))
        self.fixBtn.setToolTip(globals_.trans.string('Diag', 26))
        self.fixBtn.clicked.connect(self.FixSelected)
        if not foundAnything: self.fixBtn.setEnabled(False)

        self.errorLayout.addWidget(self.errorList)
        self.errorLayout.addWidget(self.fixBtn)

        if foundCritical:
            return True, len(self.buttonHandlers)
        elif foundAnything:
            return False, len(self.buttonHandlers)
        return None, len(self.buttonHandlers)

    def FixSelected(self):
        """
        Fixes the selected items
        """

        # Ask the user to make sure
        btn = QtWidgets.QMessageBox.warning(None, globals_.trans.string('Diag', 27), globals_.trans.string('Diag', 28),
                                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if btn != QtWidgets.QMessageBox.Yes: return

        # Show the 'Fixing...' box while fixing
        pleasewait = QtWidgets.QProgressDialog()
        pleasewait.setLabelText(globals_.trans.string('Diag', 29))  # Fixing...
        pleasewait.setMinimum(0)
        pleasewait.setMaximum(100)
        pleasewait.setAutoClose(True)
        pleasewait.open()
        pleasewait.show()
        pleasewait.setValue(0)

        # Fix them
        for index, item in enumerate(self.errorList.selectedIndexes()[:]):
            listItem = self.errorList.itemFromIndex(item)
            try:
                listItem.fix()
                SetDirty()
            except Exception:
                pass  # fail silently
            self.errorList.takeItem(item.row())

            total = len(self.errorList.selectedIndexes()[:])
            if total != 0: pleasewait.setValue(int(float(index) / total * 100))

        # Remove the 'Fixing...' box
        pleasewait.setValue(100)
        del pleasewait

        # Gray out the Fix button if there are no more problems
        if self.errorList.count() == 0: self.fixBtn.setEnabled(False)

    def ObjsInTileset(self, mode='f'):
        """
        Checks for any objects which cannot be found in the tilesets
        """
        deletions = []
        for layer in globals_.Area.layers:
            for obj in layer:

                if globals_.ObjectDefinitions[obj.tileset] is None:
                    deletions.append(obj)
                elif globals_.ObjectDefinitions[obj.tileset][obj.type] is None:
                    deletions.append(obj)

        has_problem = bool(deletions)
        if mode == 'c':
            return has_problem

        if not has_problem: return

        for obj in deletions:
            obj.delete()
            obj.setSelected(False)
            globals_.mainWindow.scene.removeItem(obj)

        globals_.mainWindow.levelOverview.update()

    def CrashSprites(self, mode='f'):
        """
        Checks if there are any sprites which are known to be crashy and cause problems often
        """
        problems = (121,  # en reverse
                    475)  # will crash if you use a looped path

        founds = []
        for sprite in globals_.Area.sprites:
            if sprite.type in problems: founds.append(sprite)

        if mode == 'c':
            return bool(founds)
        else:
            for sprite in founds:
                sprite.delete()
                sprite.setSelected(False)
                globals_.mainWindow.scene.removeItem(sprite)
                globals_.mainWindow.levelOverview.update()

    def CrashSpriteSettings(self, mode='f'):
        """
        Checks for sprite settings which are known to cause major glitches and crashes
        """
        checkfor = []
        problem = False
        for sprite in globals_.Area.sprites:
            # ask somebody about 153 for clarification, the add it to the fixers
            if sprite.type == 166 and (sprite.spritedata[2] & 0xF0) >> 4 == 4: problem = True
            #           also double-check nyb10, then add it to the fixers
            if sprite.type == 171 and sprite.spritedata[4] & 0xF != 1: problem = True
            if sprite.type == 203 and sprite.spritedata[4] & 0xF == 1:
                if [454, 432] not in checkfor: checkfor.append([454, 432])
            if sprite.type == 247 and sprite.spritedata[5] & 0xF == 1: problem = True
            if sprite.type == 323:
                if sprite.spritedata[4] & 0xF == 4: problem = True
                if sprite.spritedata[2] & 0xF < (sprite.spritedata[3] & 0xF0) >> 4: problem = True
            if sprite.type == 449 and (sprite.spritedata[5] & 0xF0) >> 4 == 1: problem = True
            if sprite.type == 479 and sprite.spritedata[4] & 0xF == 1: problem = True
            if sprite.type == 481:
                if sprite.spritedata[5] & 0xF > 2: problem = True
                if [419] not in checkfor: checkfor.append([419])

        # check for sprites which are depended on by other sprites
        new = list(checkfor)
        for item in checkfor:
            for sprite in globals_.Area.sprites:
                if sprite.type in item:
                    try:
                        new.remove(item)
                    except Exception:
                        pass  # probably already removed it
        checkfor = new
        if checkfor: problem = True

        if mode == 'c':
            return problem
        elif problem:
            addsprites = []
            for sprite in globals_.Area.sprites:
                # :(
                if sprite.type == 166 and (
                    sprite.spritedata[2] & 0xF0) >> 4 == 4: sprite.spritedata = sprite.spritedata[
                                                                                0:2] + ' ' + sprite.spritedata[3:]
                if sprite.type == 171 and sprite.spritedata[4] & 0xF != 1: sprite.spritedata = sprite.spritedata[
                                                                                               0:4] + chr(
                    1) + sprite.spritedata[5:]
                if sprite.type == 203 and sprite.spritedata[4] & 0xF == 1:
                    if [454, 432] in checkfor:
                        addsprites.append((454, sprite.objx - 128, sprite.objy - 128))
                if sprite.type == 247 and sprite.spritedata[5] & 0xF == 1: sprite.spritedata = sprite.spritedata[
                                                                                               0:5] + chr(
                    0) + sprite.spritedata[6:]
                if sprite.type == 323:
                    if sprite.spritedata[4] & 0xF == 4: sprite.spritedata = sprite.spritedata[0:4] + chr(
                        1) + sprite.spritedata[5:]
                    if sprite.spritedata[2] & 0xF < (sprite.spritedata[3] & 0xF0) >> 4:
                        sprite.spritedata = sprite.spritedata[0:2] + chr(
                            (sprite.spritedata[3] & 0xF0) >> 4) + sprite.spritedata[3:]
                if sprite.type == 449 and (
                    sprite.spritedata[5] & 0xF0) >> 4 == 1: sprite.spritedata = sprite.spritedata[0:5] + chr(
                    0) + sprite.spritedata[6:]
                if sprite.type == 479 and sprite.spritedata[4] & 0xF == 1:
                    if (sprite.spritedata[4] & 0xF0) >> 4 == 1:
                        sprite.spritedata = sprite.spritedata[0:4] + chr(0x10) + sprite.spritedata[5:]
                    else:
                        sprite.spritedata = sprite.spritedata[0:4] + chr(0) + sprite.spritedata[5:]
                if sprite.type == 481:
                    if sprite.spritedata[5] & 0xF > 2: sprite.spritedata = sprite.spritdata[0:5] + chr(
                        2) + sprite.spritedata[6:]
                    addsprites.append((419, sprite.objx - 128, sprite.objy - 128))

            for id_, x, y in addsprites:
                globals_.mainWindow.CreateSprite(x, y, id_, bytes(8))

            globals_.mainWindow.scene.update()

    def TooManySprites(self, mode='f'):
        """
        Determines if the # of sprites in the current area is > max_
        """
        max_ = 1000

        problem = len(globals_.Area.sprites) > max_

        if mode == 'c':
            return problem

        if not problem:
            return None

        for spr in globals_.Area.sprites[max_:]:
            spr.delete()
            spr.setSelected(False)
            globals_.mainWindow.scene.removeItem(spr)

        globals_.Area.sprites = globals_.Area.sprites[:max_]
        globals_.mainWindow.scene.update()
        globals_.mainWindow.levelOverview.update()

    def DuplicateEntranceIDs(self, mode='f'):
        """
        mode 'c': Checks for the prescence of multiple entrances with the same ID
        mode 'f': Fixes the entrance id of the duplicate entrances
        """
        ids = []
        for ent in globals_.Area.entrances:
            if ent.entid in ids:
                if mode == 'c':
                    return False

                # find the lowest available ID
                getids = [False for _ in range(256)]
                for check in globals_.Area.entrances:
                    getids[check.entid] = True

                minimumID = getids.index(False)

                ent.entid = minimumID
                ent.UpdateTooltip()
                ent.UpdateListItem()

            ids.append(ent.entid)

        return False

    def NoStartEntrance(self, mode='f'):
        """
        Determines if there is a start entrance or not
        """
        # global Area
        if globals_.Area.areanum != 1:
            return False

        start = None
        for ent in globals_.Area.entrances:
            if ent.entid == globals_.Area.startEntrance:
                start = ent
            else:
                problem = False
        problem = start is None

        if mode == 'c':
            return problem
        elif problem:
            # make an entrance at 1024, 512 with an ID of globals_.Area.startEntrance
            globals_.mainWindow.CreateEntrance(1024, 512, globals_.Area.startEntrance)

    def EntranceTooCloseToZoneEdge(self, mode='f'):
        """
        Checks if the main entrance is too close to the left zone edge
        """
        offset = 24 * 8  # 8 blocks away from the left zone edge
        if not globals_.Area.zones: return False

        # if the ent isn't even in the zone, return
        if self.EntranceOutsideOfZone('c'): return False

        start = None
        for ent in globals_.Area.entrances:
            if ent.entid == globals_.Area.startEntrance: start = ent
        if start is None: return False

        firstzone_idx = SLib.MapPositionToZoneID(globals_.Area.zones, start.objx, start.objy)

        if firstzone_idx == -1: return False

        firstzone = globals_.Area.zones[firstzone_idx]

        problem = start.objx < firstzone.objx + offset
        if mode == 'c':
            return problem
        elif problem:
            start.setPos((firstzone.objx + offset) * 1.5, start.objy * 1.5)

    def EntranceOutsideOfZone(self, mode='f'):
        """
        Checks if any entrances are not inside of a zone
        """
        left_offset = 24 * 8  # 8 blocks away from the left zone edge
        if not globals_.Area.zones: return False

        for ent in globals_.Area.entrances:
            x = ent.objx
            y = ent.objy
            zone_idx = SLib.MapPositionToZoneID(globals_.Area.zones, x, y)

            if zone_idx == -1: return False
            zone = globals_.Area.zones[zone_idx]

            if x < zone.objx:
                problem = True
            elif x > zone.objx + zone.width:
                problem = True
            elif y < zone.objy - 64:
                problem = True
            elif y > zone.objy + zone.height + 192:
                problem = True
            else:
                problem = False

            if problem and mode == 'c':
                return True
            elif problem:
                if x < zone.objx:
                    newx = zone.objx + left_offset
                elif x > zone.objx + zone.width:
                    newx = zone.objx + zone.width - 16
                else:
                    newx = ent.objx
                if y < (zone.objy - 64):
                    newy = zone.objy - 64  # entrances can be placed a few blocks above the top zone border
                elif y > zone.objy + zone.height:
                    newy = zone.objy + zone.height - 32
                else:
                    newy = ent.objy
                ent.objx = newx
                ent.objy = newy
                ent.setPos(int(newx * 1.5), int(newy * 1.5))
                globals_.mainWindow.scene.update()

        return False

    def TooManyZones(self, mode='f'):
        """
        Checks if there are too many zones in this area
        """
        problem = len(globals_.Area.zones) > 6

        if mode == 'c':
            return problem
        elif problem:
            globals_.Area.zones = globals_.Area.zones[:6]

            globals_.mainWindow.scene.update()
            globals_.mainWindow.levelOverview.update()

    def NoZones(self, mode='f'):
        """
        Checks if there are no zones in this area
        """
        problem = not globals_.Area.zones
        if mode == 'c':
            return problem

        if not problem:
            return

        # make a default zone
        globals_.mainWindow.CreateZone(16, 16)

    def ZonesTooClose(self, mode='f'):
        """
        Checks for any zones which are too close together or are overlapping
        """
        # global Area
        padding = 4  # minimum blocks between zones

        for check in reversed(
                globals_.Area.zones):  # reversed because generally zone 0 is most important, 1 is less, 2 is lesser, etc.
            crect = check.ZoneRect
            for against in globals_.Area.zones:
                if check is against: continue
                arect = against.ZoneRect.adjusted(-16 * padding, -16 * padding, 16 * padding, 16 * padding)

                if crect.intersects(arect):
                    if mode == 'c':
                        return True
                    else:
                        # AAAAAAAAAAA
                        center = crect.center()

                        if arect.contains(crect) or crect.contains(arect):
                            # one inside the other
                            axes = [None, 'both']
                        elif abs(center.x() - arect.center().x()) > abs(center.y() - arect.center().y()):
                            # horizontally positioned
                            if arect.center().x() > center.x():
                                # shrink the right
                                axes = [None, 'w']
                            else:
                                # shrink the left
                                axes = ['x', 'w']
                        else:
                            # vertically positioned
                            if arect.center().y() < center.y():
                                # shrink the top
                                axes = ['y', 'h']
                            else:
                                # shrink the bottom
                                axes = [None, 'h']

                        # the simplest method :D
                        checkzone = check.ZoneRect
                        oldCoords = checkzone.getCoords()
                        while checkzone.intersects(arect):
                            if axes[0] is None:
                                pass
                            elif axes[0] == 'x':
                                check.objx += 1
                            else:
                                check.objy += 1

                            if axes[1] == 'both':
                                check.objx += 1
                                check.objy += 1
                            elif axes[1] == 'w':
                                check.width -= 1
                            else:
                                check.height -= 1
                            if check.width < 300: check.width = 300
                            if check.height < 200: check.height = 200

                            check.UpdateRects()
                            check.setPos(int(check.objx * 1.5), int(check.objy * 1.5))
                            globals_.mainWindow.scene.update()
                            checkzone = check.ZoneRect

                            if oldCoords == checkzone.getCoords(): break
                            oldCoords = checkzone.getCoords()

                        globals_.mainWindow.scene.update()

        return False

    def ZonesTooCloseToAreaEdges(self, mode='f'):
        """
        Checks for any zones which are too close to the area edges, and moves them
        """
        # global Area
        areaw = 16384
        areah = 8192

        for z in globals_.Area.zones:
            if (z.objx < 16) or (z.objy < 16) or (z.objx + z.width > areaw - 16) or (z.objy + z.height > areah - 16):
                if mode == 'c':
                    return False
                else:
                    if z.objx < 16: z.objx = 16
                    if z.objy < 16: z.objy = 16
                    if z.objx + z.width > areaw - 16: z.width = areaw - z.objx - 16
                    if z.objy + z.height > areah - 16: z.height = areah - z.objy - 16
                    z.UpdateRects()
                    globals_.mainWindow.scene.update()

        return False

    def BiasNotEnabled(self, mode='f'):
        """
        Checks for any zones which do not have bias enabled
        """
        # global Area
        fix = {'0 0': (0, 1),
               '0 7': (0, 6),
               '0 11': (0, 4),
               '3 2': (0, 3),
               '3 7': (3, 3),  # This doesn't always appear
               '6 0': (6, 2),  # to work due to inconsistencies
               '6 7': (6, 6),  # in the editor, but I'm pretty
               '6 11': (6, 4),  # sure it's written correctly.
               '1 0': (1, 1),
               '1 7': (1, 10),
               '1 11': (1, 4),
               '4 2': (1, 3),
               '4 7': (4, 3)}

        for z in globals_.Area.zones:
            check = str(z.cammode) + ' ' + str(z.camzoom)
            if check in fix:
                if mode == 'c':
                    return False
                else:
                    z.cammode = fix[check][0]
                    z.camzoom = fix[check][1]

        return False

    def ZonesTooBig(self, mode='f'):
        """
        Checks for any zones which may be too large
        """
        # global Area
        maxarea = 16384  # blocks (approximated value)

        for z in globals_.Area.zones:
            if int((z.width / 32) * (z.height / 32)) > maxarea * 8:
                if mode == 'c':
                    return False
                else:  # shrink it by whichever dimension is larger
                    if z.width > z.height:
                        z.width = int(256 * maxarea / z.height)
                    else:
                        z.height = int(256 * maxarea / z.width)
                    z.UpdateRects()
                    globals_.mainWindow.scene.update()

        return False

    def ZonesTooSmall(self, mode='f'):
        """
        Checks for any zones which may be too small for their zoom level
        """
        # global Area
        MinimumSize = (484, 272)
        ##                        (484, 272), # -1
        ##                        (484, 272), # 0
        ##                        (484, 272), # 1
        ##                        (540, 304), # 2
        ##                        (596, 336), # 3
        ##                        (796, 448)) # 4
        ##        ZoomLevels = (3,
        ##                      3,
        ##                      6,
        ##                      6,
        ##                      5,
        ##                      None,
        ##                      4,
        ##                      4,
        ##                      0,
        ##                      1,
        ##                      None,
        ##                      5)

        fixes = []
        for z in globals_.Area.zones:
            if z.width < MinimumSize[0]:
                fixes.append(z)
            elif z.height < MinimumSize[1]:
                fixes.append(z)

        if mode == 'c':
            return bool(fixes)

        for z in fixes:
            if z.width < MinimumSize[0]: z.width = MinimumSize[0]
            if z.height < MinimumSize[1]: z.height = MinimumSize[1]
            z.prepareGeometryChange()
            z.UpdateRects()

        globals_.mainWindow.scene.update()
        globals_.mainWindow.levelOverview.update()


class InfoPreviewWidget(QtWidgets.QWidget):
    """
    Widget that shows a preview of the level metadata info - available in vertical & horizontal flavors
    """

    def __init__(self, direction):
        """
        Creates and initializes the widget
        """
        QtWidgets.QWidget.__init__(self)
        self.direction = direction

        self.Label1 = QtWidgets.QLabel('')
        if self.direction == QtCore.Qt.Horizontal: self.Label2 = QtWidgets.QLabel('')
        self.updateLabels()

        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.addWidget(self.Label1)
        if self.direction == QtCore.Qt.Horizontal: self.mainLayout.addWidget(self.Label2)
        self.setLayout(self.mainLayout)

        if self.direction == QtCore.Qt.Horizontal: self.setMinimumWidth(256)

    def updateLabels(self):
        """
        Updates the widget labels
        """
        if (not globals_.Area) or not hasattr(globals_.Area, 'filename'):  # can't get level metadata if there's no level
            self.Label1.setText('')
            if self.direction == QtCore.Qt.Horizontal: self.Label2.setText('')
            return

        a = [  # MUST be a list, not a tuple
            globals_.mainWindow.fileTitle,
            globals_.Area.Title,
            globals_.trans.string('InfoDlg', 8, '[name]', globals_.Area.Creator),
            globals_.trans.string('InfoDlg', 5) + ' ' + globals_.Area.Author,
            globals_.trans.string('InfoDlg', 6) + ' ' + globals_.Area.Group,
            globals_.trans.string('InfoDlg', 7) + ' ' + globals_.Area.Webpage,
        ]

        for b, section in enumerate(a):  # cut off excessively long strings
            if self.direction == QtCore.Qt.Vertical:
                short = clipStr(section, 128)
            else:
                short = clipStr(section, 184)
            if short is not None: a[b] = short + '...'

        if self.direction == QtCore.Qt.Vertical:
            str1 = a[0] + '<br>' + a[1] + '<br>' + a[2] + '<br>' + a[3] + '<br>' + a[4] + '<br>' + a[5]
            self.Label1.setText(str1)
        else:
            str1 = a[0] + '<br>' + a[1] + '<br>' + a[2]
            str2 = a[3] + '<br>' + a[4] + '<br>' + a[5]
            self.Label1.setText(str1)
            self.Label2.setText(str2)

        self.update()


class CustomSortableListWidgetItem(QtWidgets.QListWidgetItem):
    """
    ListWidgetItem subclass that allows sorting by arbitrary key
    """
    sortKey = 0

    def __lt__(self, other):
        if hasattr(self, 'sortKey') and hasattr(other, 'sortKey'):
            return self.sortKey < other.sortKey

        return False


class CameraProfilesDialog(QtWidgets.QDialog):
    """
    Dialog for editing camera profiles
    """

    def __init__(self):
        """
        Creates and initialises the dialog
        """
        super(CameraProfilesDialog, self).__init__()
        self.setWindowTitle('Camera Profiles')
        self.setWindowIcon(GetIcon('camprofile'))
        self.setMinimumHeight(450)

        self.list = QtWidgets.QListWidget()
        self.list.itemSelectionChanged.connect(self.handleSelectionChanged)
        self.list.setSortingEnabled(True)

        self.addButton = QtWidgets.QPushButton('Add')
        self.addButton.clicked.connect(self.handleAdd)
        self.removeButton = QtWidgets.QPushButton('Remove')
        self.removeButton.clicked.connect(self.handleRemove)
        self.removeButton.setEnabled(False)

        listLayout = QtWidgets.QGridLayout()
        listLayout.addWidget(self.addButton, 0, 0)
        listLayout.addWidget(self.removeButton, 0, 1)
        listLayout.addWidget(self.list, 1, 0, 1, 2)

        self.eventid = QtWidgets.QSpinBox()
        self.eventid.setRange(0, 255)
        self.eventid.setToolTip("<b>Triggering Event ID:</b><br>Sets the event ID that will trigger the camera profile. If switching away from a different profile, the previous profile's event ID will be automatically deactivated (so the game doesn't instantly switch back to it).")
        self.eventid.valueChanged.connect(self.handleEventIDChanged)

        self.camsettings = CameraModeZoomSettingsLayout(False)
        self.camsettings.setValues(0, 0)
        self.camsettings.edited.connect(self.handleCamSettingsChanged)

        profileLayout = QtWidgets.QFormLayout()
        profileLayout.addRow('Triggering Event ID:', self.eventid)
        profileLayout.addRow(createHorzLine())
        profileLayout.addRow(self.camsettings)

        self.profileBox = QtWidgets.QGroupBox('Modify Selected Camera Profile Properties')
        self.profileBox.setLayout(profileLayout)
        self.profileBox.setEnabled(False)
        self.profileBox.setToolTip('<b>Modify Selected Camera Profile Properties:</b><br>Camera Profiles can only be used with the "Event-Controlled" camera mode in the "Zones" dialog.<br><br>Transitions between zoom levels are instant, but can be hidden through careful use of zoom sprites (206).')

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        Layout = QtWidgets.QGridLayout()
        Layout.addLayout(listLayout, 0, 0)
        Layout.addWidget(self.profileBox, 0, 1)
        Layout.addWidget(buttonBox, 1, 0, 1, 2)
        self.setLayout(Layout)

        for profile in globals_.Area.camprofiles:
            item = CustomSortableListWidgetItem()
            item.setData(QtCore.Qt.UserRole, profile)
            item.sortKey = profile[0]
            self.updateItemTitle(item)
            self.list.addItem(item)

        self.list.sortItems()

    def handleAdd(self, item=None):
        new_id = 1
        for row in range(self.list.count()):
            item = self.list.item(row)
            values = item.data(QtCore.Qt.UserRole)
            new_id = max(new_id, values[0] + 1)

        item = CustomSortableListWidgetItem()
        item.setData(QtCore.Qt.UserRole, [new_id, 0, 0])
        self.updateItemTitle(item)
        self.list.addItem(item)

    def handleRemove(self):
        self.list.takeItem(self.list.currentRow())

    def handleSelectionChanged(self):
        selItems = self.list.selectedItems()

        self.removeButton.setEnabled(bool(selItems))
        self.profileBox.setEnabled(bool(selItems))

        if selItems:
            selItem = selItems[0]
            values = selItem.data(QtCore.Qt.UserRole)

            self.eventid.setValue(values[0])
            self.camsettings.setValues(values[1], values[2])

    def handleEventIDChanged(self, eventid):
        selItem = self.list.selectedItems()[0]
        values = selItem.data(QtCore.Qt.UserRole)
        values[0] = eventid
        selItem.setData(QtCore.Qt.UserRole, values)
        selItem.sortKey = eventid
        self.updateItemTitle(selItem)

    def handleCamSettingsChanged(self):
        selItem = self.list.selectedItems()[0]
        values = selItem.data(QtCore.Qt.UserRole)
        values[1] = self.camsettings.modeButtonGroup.checkedId()
        values[2] = self.camsettings.screenSizes.currentIndex()
        selItem.setData(QtCore.Qt.UserRole, values)

    def updateItemTitle(self, item):
        item.setText('Camera Profile on Event %d' % item.data(QtCore.Qt.UserRole)[0])
