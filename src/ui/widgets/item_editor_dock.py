from PyQt6 import QtWidgets

from data import globals_

class ItemEditorDockWidget(QtWidgets.QDockWidget):
    """
    DockWidget subclass that switches between show/hide and
    enable/disable depending on docking status
    """
    def __init__(self, title: str | None, parent: QtWidgets.QWidget | None) -> None:
        super().__init__(title, parent)
        self.topLevelChanged.connect(self.top_level_changed)

        # Disable automatically
        self.set_active(False)

        # During the very first launch (empty QSettings), the following
        # sequence of things happens:
        # - initialization
        # - .setActive(False), with self.isFloating() == False
        # - .handleTopLevelChanged(True)
        # Normally, we would leave the widget visible in that case,
        # since it corresponds to the user undocking an item editor for
        # an unselected type of object (and of course they'd want to
        # continue to see it while they drag it somewhere). But during
        # the first launch, all of the docks need to be hidden. So we
        # special-case this using self.initial_setup.
        self.initial_setup = (not globals_.settings.contains('MainWindowGeometry'))

    def top_level_changed(self, top_level: bool) -> None:
        if self.initial_setup:
            self.setVisible(False)
            self.initial_setup = False

    def set_active(self, active: bool) -> None:
        """
        Sets the dock as active/visible depending on the docking status
        """
        if self.isFloating():
            self.setVisible(active)
            self.setEnabled(True)
        else:
            self.setVisible(True)
            self.setEnabled(active)

            # If multiple docks are in one place (tabbed), then we
            # should switch to the triggered one automatically
            if active:
                self.raise_()
                self.setFocus()

    def is_active(self) -> bool:
        """
        Returns the current active/visibility state
        """
        if self.isFloating():
            return self.isVisible()
        else:
            return self.isEnabled()
