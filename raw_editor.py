from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QStackedWidget, QSizePolicy, QComboBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFontMetrics, QFont, QFocusEvent

from raw_data import RawData


class FormattedLineEdit(QLineEdit):
    data_edited = pyqtSignal()


    def __init__(self, size: int) -> None:
        super().__init__()
        self._size = size

        text_format = (('x' * min(size, 4) + ' ') * (size // 4) + 'x' * (size % 4)).strip()
        self._last_good_text = text_format.replace('x', '0')

        min_valid_width = QFontMetrics(QFont()).horizontalAdvance(text_format)
        # self.setInputMask(text_format)

        self.setMinimumWidth(min_valid_width + 2 * 11)  # add padding
        self.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed))

        self.textEdited.connect(self._text_edited)


    def text(self) -> str:
        return super().text().replace(' ', '')


    def setText(self, text: str) -> None:
        text = text.replace(' ', '')
        super().setText((' '.join(text[i:i + 4] for i in range(0, len(text), 4))).strip())
        self._last_good_text = text
        self.setStyleSheet('')


    def _text_edited(self, text: str) -> None:
        if self._is_raw_data_valid(text):
            self.data_edited.emit()
            self.setStyleSheet('')

        else:
            self.setStyleSheet('background-color: #ffd2d2;')


    def _is_raw_data_valid(self, text: str) -> bool:
        '''
        Triggered when the raw data textbox is edited
        '''

        raw = text.replace(' ', '')
        if len(raw) != self._size: return False

        try: _ = bytes.fromhex(text)
        except ValueError: return False

        self._last_good_text = text

        return True


    def focusOutEvent(self, a0: QFocusEvent) -> None:
        if not self._is_raw_data_valid(self.text()):
            self.setText(self._last_good_text)

        return super().focusOutEvent(a0)



class OldSpriteRawEditor(QWidget):
    '''
    Widget for editing raw sprite data with the old sprite data format
    '''
    data_edited = pyqtSignal(RawData)

    def __init__(self) -> None:
        super().__init__()

        self._data = FormattedLineEdit(RawData.Format.Vanilla.value)
        self._data.data_edited.connect(lambda: self.data_edited.emit(self.data))

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._data)
        self.setLayout(layout)


    @property
    def data(self) -> RawData:
        '''
        Returns the data
        '''
        return RawData(bytes.fromhex(self._data.text()), format = RawData.Format.Vanilla)

    @data.setter
    def data(self, data: RawData) -> None:
        '''
        Sets the data
        '''
        self._data.setText(data.original.hex())



class NewSpriteRawEditor(QWidget):
    '''
    Widget for editing raw sprite data with the new sprite data format
    '''
    data_edited = pyqtSignal(RawData)


    def __init__(self) -> None:
        super().__init__()
        self._size = 0

        self._events = FormattedLineEdit(RawData.Format.Vanilla.value)
        self._events.data_edited.connect(lambda: self.data_edited.emit(self.data))

        self._block_combo = QComboBox()
        self._block_combo.currentIndexChanged.connect(self._block_changed)
        self._block_combo.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))

        self._stack = QStackedWidget()
        self._stack.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed))

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self._events)
        layout.addWidget(self._block_combo)
        layout.addWidget(self._stack)
        self.setLayout(layout)


    def _set_size(self, size: int) -> None:
        '''
        Sets the size of the sprite data
        '''
        self._size = size
        last_selected_index = self._block_combo.currentIndex()

        self._block_combo.clear()
        for i in range(size):
            self._block_combo.addItem(f'Block {i + 1}')

        for i in range(self._stack.count()):
            self._stack.removeWidget(self._stack.widget(0))

        for i in range(size):
            w = FormattedLineEdit(8)
            self._stack.addWidget(w)
            w.data_edited.connect(lambda: self.data_edited.emit(self.data))

        if size > 0:
            self._block_combo.setCurrentIndex(0)
            self._stack.setCurrentIndex(0)

        self._block_combo.setDisabled(size == 0)
        self._stack.setDisabled(size == 0)

        self._block_combo.setCurrentIndex(min(last_selected_index, size - 1) if last_selected_index != -1 else 0)


    @property
    def data(self) -> RawData:
        '''
        Returns the data
        '''
        return RawData(
            bytes.fromhex(self._events.text()),
            *(bytes.fromhex(self._stack.widget(i).text()) for i in range(self._size)),
            format = RawData.Format.Extended
        )


    @data.setter
    def data(self, data: RawData) -> None:
        '''
        Sets the data
        '''
        if len(data.blocks) != len(self.data.blocks): self._set_size(len(data.blocks))

        self._events.setText(data.original.hex())
        for i, block in enumerate(data.blocks):
            self._stack.widget(i).setText(block.hex())


    def _block_changed(self, index: int) -> None:
        '''
        Shows the block at the new index
        '''
        self._stack.setCurrentIndex(index)



class RawEditor(QWidget):
    '''
    Widget for editing raw sprite data
    '''

    data_edited = pyqtSignal(RawData)

    def __init__(self) -> None:
        '''
        Constructor
        '''
        super().__init__()
        self.setSizePolicy(QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred))

        self._data_widget = OldSpriteRawEditor()

        layout = QHBoxLayout()
        layout.addWidget(self._data_widget)
        self.setLayout(layout)


    @property
    def data(self) -> RawData:
        '''
        Returns the data
        '''
        return self._data_widget.data

    @data.setter
    def data(self, data: RawData) -> None:
        '''
        Sets the data
        '''
        if self._data_widget.data.format != data.format:
            try:
                self.layout().removeWidget(self._data_widget)
                self._data_widget.deleteLater()
            except: pass

            if data.format == RawData.Format.Vanilla: self._data_widget = OldSpriteRawEditor()
            else: self._data_widget = NewSpriteRawEditor()

            self._data_widget.data_edited.connect(lambda: self.data_edited.emit(self.data))
            self.layout().addWidget(self._data_widget)

        self._data_widget.data = data
