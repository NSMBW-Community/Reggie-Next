from PyQt6 import QtCore, QtGui, QtWidgets

from data import globals_
from data.common.game_def import LoadGameDef, ReggieGameDefinition, getAvailableGameDefs
from data.common.settings import setting
from ui.theme.reggie_theme import GetIcon
from ui.widgets.game_def_viewer import GameDefViewer


class GameDefMenu(QtWidgets.QMenu):
    """
    A menu which lets the user pick gamedefs
    """
    game_changed = QtCore.pyqtSignal()
    update_flag = False

    def __init__(self) -> None:
        """
        Creates and initializes the menu
        """
        super().__init__()
        self.aboutToShow.connect(self.setup_game_defs)
        self.createActions()

    def createActions(self) -> None:
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

    def handleGameDefClicked(self, checked: bool) -> None:
        """
        Handles the user clicking a gamedef
        """
        if not checked or self.update_flag:
            return

        action = self.actGroup.checkedAction()
        if action is None:
            return

        name = action.data()
        success = LoadGameDef(name)
        if success:
            self.game_changed.emit()
            return

        # Setting the new gamedef failed for some reason, so load back the old one
        real_gamedef = setting('LastGameDef')
        success = LoadGameDef(real_gamedef)
        if not success:
            QtWidgets.QMessageBox.warning(None, globals_.trans.string('error.title.error'), globals_.trans.string('error.game_def.restore_old'))
            LoadGameDef(None)
            return

        self.update_flag = True
        for act in self.actGroup.actions():
            act.setChecked(act.data() == real_gamedef)
        self.update_flag = False

    def setup_game_defs(self) -> None:
        """
        Handles setting up the game defs when the menu opens
        """
        self.clear()
        self.createActions()
