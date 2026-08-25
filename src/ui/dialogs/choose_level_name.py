from PyQt6 import QtCore, QtWidgets

import globals_
from src.data.common.loaders import LoadLevelNames
from src.ui.theme.reggie_theme import GetIcon

class ChooseLevelNameDialog(QtWidgets.QDialog):
    """
    Dialog which lets you choose a level from a list
    """

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle(globals_.trans.string('OpenFromNameDlg', 0))
        self.setWindowIcon(GetIcon('open'))

        LoadLevelNames()
        self.current_level = None

        # Create the tree
        tree = QtWidgets.QTreeWidget()
        tree.setColumnCount(1)
        tree.setHeaderHidden(True)
        tree.setIndentation(16)
        tree.currentItemChanged.connect(self.handle_item_change)
        tree.itemActivated.connect(self.handle_item_activated)

        # Add items (LevelNames is effectively a big category)
        tree.addTopLevelItems(self.parse_category(globals_.LevelNames))
        self.level_tree = tree

        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        ok_button = self.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        if ok_button is not None:
            ok_button.setEnabled(False)

        # Create the layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.level_tree)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

        # Wide enough to fit "World 5: Freezeflame Volcano/Freezeflame Glacier"
        self.setMinimumWidth(320)
        self.setMinimumHeight(384)

    def parse_category(self, items: tuple[str, ...]):
        """
        Parses an XML category
        """
        nodes = []
        for item in items:
            node = QtWidgets.QTreeWidgetItem()
            node.setText(0, item[0])

            # Check if it's a category or a level
            if isinstance(item[1], str):
                # Level
                node.setData(0, QtCore.Qt.ItemDataRole.UserRole, item[1])
                node.setToolTip(0, item[1])
            else:
                # Category
                children = self.parse_category(item[1])
                for cnode in children:
                    node.addChild(cnode)
                node.setToolTip(0, item[0])

            nodes.append(node)

        return tuple(nodes)

    def handle_item_change(self, current, previous):
        """
        Catch the selected level and enable/disable OK button as needed
        """
        self.current_level = current.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if self.current_level is not None:
            self.current_level = str(self.current_level)

        ok_button = self.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        if ok_button is not None:
            ok_button.setEnabled(self.current_level is not None)

    def handle_item_activated(self, item, column):
        """
        Handle a double-click on a level
        """
        self.current_level = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if self.current_level is not None:
            self.current_level = str(self.current_level)
            self.accept()
