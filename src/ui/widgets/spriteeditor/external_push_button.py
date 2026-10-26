from PyQt6 import QtWidgets
from data.sprite.external_note import ExternalNote

class ExternalPushButtonWidget(QtWidgets.QPushButton):
    """
    Wrapper for QPushButton that includes an ExternalNote object
    """

    def __init__(self, text: str | None, parent: QtWidgets.QWidget | None, note: ExternalNote) -> None:
        super().__init__(text, parent)
        self.note = note
