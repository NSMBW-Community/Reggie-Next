from PyQt6 import QtWidgets


class AbstractSpriteEditorWidget(QtWidgets.QWidget):
    """Abstract base class for the Sprite Editor Widget. Provides basic properties for required instance checks and usages."""
    def __init__(self, defaultmode=False) -> None:
        super().__init__()
        self.AutoFlag = False
        self.DefaultMode = defaultmode

        # comments
        self.com_box = QtWidgets.QGroupBox()
        self.com_main = QtWidgets.QTextEdit()
        self.com_more = QtWidgets.QPushButton()
        self.com_dep = QtWidgets.QPushButton()
        self.com_extra = QtWidgets.QTextEdit()

    def ShowMoreComments(self):
        pass

    def DependencyToggle(self):
        pass
