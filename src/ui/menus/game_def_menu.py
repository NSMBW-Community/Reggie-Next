from PyQt6 import QtWidgets, QtCore, QtGui

from src.ui.theme.reggie_theme import GetIcon
from dirty import setting

import globals_

from src.ui.widgets.game_def_viewer import GameDefViewer
from src.data.common.gamedef import getAvailableGameDefs, loadNewGameDef, ReggieGameDefinition

class GameDefMenu(QtWidgets.QMenu):
    """
    A menu which lets the user pick gamedefs
    """
    game_changed = QtCore.pyqtSignal()
    update_flag = False

    def __init__(self):
        """
        Creates and initializes the menu
        """
        QtWidgets.QMenu.__init__(self)
        self.createActions()

    def createActions(self):
        """
        Creates all the actions for the menu
        """
        # Add the gamedef viewer widget
        self.game_def_view = GameDefViewer()
        self.game_def_view.setMinimumHeight(100)
        self.game_changed.connect(self.game_def_view.set_info)

        v = QtWidgets.QWidgetAction(self)
        v.setDefaultWidget(self.game_def_view)
        self.addAction(v)
        self.addSeparator()

        # Add entries for each gamedef
        self.GameDefs = getAvailableGameDefs()

        self.actGroup = QtGui.QActionGroup(self)
        loaded = setting('LastGameDef')
        for folder in self.GameDefs:
            def_ = ReggieGameDefinition(folder)

            act = QtGui.QAction(self)
            act.setText(def_.name)
            act.setToolTip(def_.description)
            act.setData(folder)
            act.setActionGroup(self.actGroup)
            act.setCheckable(True)
            act.setChecked(folder == loaded)
            act.toggled.connect(self.handleGameDefClicked)

            self.addAction(act)

        self.addSeparator()

        # Add the reload button
        act = QtGui.QAction(self)
        act.setText(globals_.trans.string('Gamedefs', 19))
        act.setData('reload_gamedef')
        act.setActionGroup(self.actGroup)
        act.setIcon(GetIcon('reload'))
        act.setCheckable(False)
        act.setChecked(False)
        act.triggered.connect(self.handleReloadClicked)

        self.addAction(act)

    def handleGameDefClicked(self, checked):
        """
        Handles the user clicking a gamedef
        """
        if not checked or self.update_flag:
            return

        action = self.actGroup.checkedAction()
        if action is None:
            return

        name = action.data()
        success = loadNewGameDef(name)
        if success:
            self.game_changed.emit()
            return

        # Setting the new gamedef failed for some reason, so load back the old one
        real_gamedef = setting('LastGameDef')
        success = loadNewGameDef(real_gamedef)
        if not success:
            raise Exception("Restoring the previous game def (%r) failed after failing to load new game def (%r)" % (real_gamedef, name))

        self.update_flag = True
        for act in self.actGroup.actions():
            act.setChecked(act.data() == real_gamedef)
        self.update_flag = False

    def handleReloadClicked(self):
        """
        Handles the user clicking the Reload button
        """
        self.clear()
        self.createActions()

    def mouseReleaseEvent(self, a0):
        """
        Handles mouse press events
        """
        if a0 is None:
            return

        action = self.actionAt(a0.pos())

        # If this is the Reload button, don't close the menu when clicked
        if action and action.data() == 'reload_gamedef':
            action.trigger()
            a0.accept()
        else:
            super().mouseReleaseEvent(a0)
