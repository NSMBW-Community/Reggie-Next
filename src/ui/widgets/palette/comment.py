from PyQt6 import QtWidgets

from src.data import globals_

from src.data.level.items.comment import CommentItem
from src.ui.widgets.generic.list_with_tool_tip_signal import ListWidgetWithToolTipSignal

class CommentTab(QtWidgets.QWidget):
    """
    Represents the Comments tab in the palette
    """
    def __init__(self):
        super().__init__(None)
        label = QtWidgets.QLabel(globals_.trans.string('Palette', 34))
        label.setWordWrap(True)

        self.comment_list = ListWidgetWithToolTipSignal()
        self.comment_list.itemActivated.connect(self.comment_selected)
        self.comment_list.toolTipAboutToShow.connect(self.comment_hovered)
        self.comment_list.setSortingEnabled(True)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(label)
        main_layout.addWidget(self.comment_list)

    def comment_selected(self, item):
        """
        Handle a comment being selected
        """
        if globals_.mainWindow is None:
            return

        comment: CommentItem
        for comment in globals_.Area.comments:
            if comment.listitem == item:
                comment.ensureVisible(xMargin=192, yMargin=192)
                globals_.mainWindow.scene.clearSelection()
                comment.setSelected(True)
                break

    def comment_hovered(self, item):
        """
        Handle a comment being hovered in the list
        """
        comment: CommentItem
        for comment in globals_.Area.comments:
            if comment.listitem == item:
                comment.UpdateListItem(True)
                break
