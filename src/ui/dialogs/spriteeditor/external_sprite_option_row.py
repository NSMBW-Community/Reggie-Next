from PyQt6 import QtWidgets


class ExternalSpriteOptionRow(QtWidgets.QWidget):
    def __init__(self, button, primary, secondary):
        QtWidgets.QWidget.__init__(self)

        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.addWidget(button, 0, 0, 1, 1)
        self.setLayout(self.gridLayout)

        for i, text in enumerate(primary):
            label = QtWidgets.QLabel(str(text))
            self.gridLayout.addWidget(label, 0, i + 1, 1, 1)

        self.secondary = []

        if not secondary:
            return

        placedText = False
        for i, text in enumerate(secondary):
            if str(text) == "":
                continue

            placedText = True
            label = QtWidgets.QLabel(str(text))
            label.setWordWrap(True)

            self.secondary.append(label)

        if placedText:
            more = QtWidgets.QPushButton("v")
            more.clicked.connect(self.handleButtonClick)

            self.gridLayout.addWidget(more, 0, len(primary) + 1, 1, 1)

    def handleButtonClick(self, e):
        """
        Handles button click
        """

        layout = self.gridLayout
        cols = layout.columnCount()
        layoutItem = layout.itemAtPosition(0, cols - 1)
        button = layoutItem.widget() if layoutItem is not None else None
        if button is None or not isinstance(button, QtWidgets.QPushButton):
            return

        width = (cols - 1) // len(self.secondary)

        if button.text() == "v":
            button.setText("^")

            for i, label in enumerate(self.secondary):
                layout.addWidget(label, 1, i + 1, 1, width)
        else:
            button.setText("v")

            for label in self.secondary:
                label.setParent(None)
