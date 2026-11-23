from PyQt6 import QtWidgets


class AbstractEditorWidget(QtWidgets.QWidget):
    """
    Abstract base class for the Editor Widget(s). Provides basic properties for required instance checks and usages.
    """
    def __init__(self, defaultmode: bool = False) -> None:
        super().__init__()
        self.AutoFlag = False
        self.DefaultMode = defaultmode

        # comments
        self.com_box = QtWidgets.QGroupBox()
        self.com_main = QtWidgets.QTextEdit()
        self.com_more = QtWidgets.QPushButton()
        self.com_dep = QtWidgets.QPushButton()
        self.com_extra = QtWidgets.QTextEdit()

    def ShowMoreComments(self) -> None:
        pass

    def DependencyToggle(self) -> None:
        pass
