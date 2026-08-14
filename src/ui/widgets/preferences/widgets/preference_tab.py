from PyQt6 import QtWidgets

class PreferenceTabWidget(QtWidgets.QWidget):
    """
    Simple wrapper for QTabWidget with an info string
    """
    def __init__(self, info_text: str | None):
        super().__init__()
        self.info = info_text
