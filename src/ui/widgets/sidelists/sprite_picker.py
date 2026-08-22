from PyQt6 import QtCore, QtWidgets

from reggie import globals_
from src.data.common.loaders import LoadSpriteCategories, LoadSpriteData
from src.data.sprite.sprite_category import SpriteCategory


class SpritePickerWidget(QtWidgets.QTreeWidget):
    """
    Widget that shows a list of available sprites
    """

    def __init__(self):
        """
        Initializes the widget
        """
        super().__init__()
        self.setColumnCount(1)
        self.setHeaderHidden(True)
        self.setIndentation(16)
        self.currentItemChanged.connect(self.HandleItemChange)

        LoadSpriteData()
        LoadSpriteCategories()
        self.LoadItems()

    def UpdateSpriteNames(self):
        """
        Updates all spritenames
        """
        for cat in globals_.SpriteCategories:
            for cnode in cat.nodes:
                for i in range(cnode.childCount()):
                    snode = cnode.child(i)

                    if snode is None or snode == self.NoSpritesFound:
                        # Don't change the name of the "no sprites found" marker
                        continue

                    id_ = snode.data(0, QtCore.Qt.ItemDataRole.UserRole)

                    if 0 <= id_ < globals_.NumSprites:
                        sdef = globals_.Sprites[id_]
                    else:
                        sdef = None

                    if sdef is None:
                        name = 'UNKNOWN'
                    else:
                        name = sdef.name

                    snode.setText(0, globals_.trans.string('Sprites', 18, '[id]', id_, '[name]', name))

    def LoadItems(self):
        """
        Loads tree widget items
        """
        self.clear()

        SearchableItems = []
        for cat in globals_.SpriteCategories:
            for n in cat.nodes: cat.nodes.remove(n)
            for view in cat.sub_categories:
                cnode = QtWidgets.QTreeWidgetItem()
                cnode.setText(0, view.name)
                cnode.setData(0, QtCore.Qt.ItemDataRole.UserRole, -1)

                isSearch = (view.name == globals_.trans.string('Sprites', 16))
                if isSearch:
                    self.SearchResultsCategory = cnode

                for id_ in view.sprite_ids:
                    snode = QtWidgets.QTreeWidgetItem()
                    if id_ == 9999:
                        snode.setText(0, globals_.trans.string('Sprites', 17))
                        snode.setData(0, QtCore.Qt.ItemDataRole.UserRole, -2)
                        self.NoSpritesFound = snode
                    else:
                        if 0 <= id_ < globals_.NumSprites:
                            sdef = globals_.Sprites[id_]
                        else:
                            sdef = None

                        if sdef is None:
                            sname = "UNKNOWN"
                        else:
                            sname = sdef.name

                        snode.setText(0, globals_.trans.string('Sprites', 18, '[id]', id_, '[name]', sname))
                        snode.setData(0, QtCore.Qt.ItemDataRole.UserRole, id_)

                    if isSearch:
                        SearchableItems.append(snode)

                    cnode.addChild(snode)

                self.addTopLevelItem(cnode)
                cnode.setHidden(True)
                cat.nodes.append(cnode)

        self.ShownSearchResults = SearchableItems
        self.NoSpritesFound.setHidden(True)

        self.itemClicked.connect(self.HandleSprReplace)

        self.SwitchView(globals_.SpriteCategories[0])

    def SwitchView(self, view: SpriteCategory):
        """
        Changes the selected sprite view
        """
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item is None:
                continue
            item.setHidden(True)

        for node in view.nodes:
            node.setHidden(False)

    def HandleItemChange(self, current, previous):
        """
        Throws a signal when the selected object changed
        """
        if current is None: return
        id_ = current.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if id_ != -1:
            self.SpriteChanged.emit(id_)

    def SetSearchString(self, searchfor):
        """
        Shows the items containing that string
        """
        check = self.SearchResultsCategory

        rawresults = self.findItems(searchfor, QtCore.Qt.MatchFlag.MatchContains | QtCore.Qt.MatchFlag.MatchRecursive)
        results = list(filter((lambda x: x.parent() == check), rawresults))

        for x in self.ShownSearchResults: x.setHidden(True)
        for x in results: x.setHidden(False)
        self.ShownSearchResults = results

        self.NoSpritesFound.setHidden(bool(results))
        self.SearchResultsCategory.setExpanded(True)

    def HandleSprReplace(self, item, column):
        """
        Throws a signal when the selected sprite is used as a replacement
        """
        if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.KeyboardModifier.AltModifier:
            id_ = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if id_ != -1:
                self.SpriteReplace.emit(id_)

    SpriteChanged = QtCore.pyqtSignal(int)
    SpriteReplace = QtCore.pyqtSignal(int)
