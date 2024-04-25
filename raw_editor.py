import typing
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QStackedWidget, QSizePolicy, QComboBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFontMetrics, QFont

from raw_data import RawData


class FormattedLineEdit(QLineEdit):
    def __init__(self, size: int) -> None:
        super().__init__()
        self._size = size

        text_format = (('x' * min(size, 4) + ' ') * (size // 4) + 'x' * (size % 4)).strip()

        min_valid_width = QFontMetrics(QFont()).horizontalAdvance(text_format)
        # self.setInputMask(text_format)

        self.setMinimumWidth(min_valid_width + 2 * 11)  # add padding
        self.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed))


    def text(self) -> str:
        return super().text().replace(' ', '')


    def setText(self, text: str) -> None:
        text = text.replace(' ', '')
        super().setText((' '.join(text[i:i + 4] for i in range(0, len(text), 4))).strip())


def is_raw_data_valid(text: str, size: int) -> bool:
    '''
    Triggered when the raw data textbox is edited
    '''

    raw = text.replace(' ', '')
    if len(raw) != size: return False

    try: _ = bytes.fromhex(text)
    except ValueError: return False

    return True



class OldSpriteRawEditor(QWidget):
    '''
    Widget for editing raw sprite data with the old sprite data format
    '''
    data_edited = pyqtSignal(RawData)

    def __init__(self) -> None:
        super().__init__()

        self._data = FormattedLineEdit(RawData.Format.Vanilla.value)
        self._data.textEdited.connect(self._data_edited)

        layout = QHBoxLayout()
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
        self._data.setText(data.blocks[0].hex())


    def _data_edited(self, text: str) -> None:
        '''
        Emits the data_edited signal
        '''
        if is_raw_data_valid(text, 16):
            self.data_edited.emit(self.data)
            self._data.setStyleSheet('')

        else:
            self._data.setStyleSheet('background-color: #ffd2d2;')



class NewSpriteRawEditor(QWidget):
    '''
    Widget for editing raw sprite data with the new sprite data format
    '''
    data_edited = pyqtSignal(RawData)


    def __init__(self) -> None:
        super().__init__()
        self._size = 0

        self._events = FormattedLineEdit(RawData.Format.Extended.value)
        self._events.textEdited.connect(self._events_edited)

        self._block_combo = QComboBox()
        self._block_combo.currentIndexChanged.connect(self._block_changed)
        self._block_combo.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))

        self._stack = QStackedWidget()
        self._stack.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))

        layout = QHBoxLayout()
        layout.addWidget(self._events)
        layout.addWidget(self._block_combo)
        layout.addWidget(self._stack)
        self.setLayout(layout)


    def _set_size(self, size: int) -> None:
        '''
        Sets the size of the sprite data
        '''
        self._size = size

        self._block_combo.clear()
        for i in range(size):
            self._block_combo.addItem(f'Block {i}')

        self._stack.clear()
        for i in range(size):
            self._stack.addWidget(FormattedLineEdit(8))

        if size > 0:
            self._block_combo.setCurrentIndex(0)
            self._stack.setCurrentIndex(0)

        self._block_combo.setDisabled(size == 0)
        self._stack.setDisabled(size == 0)


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
        self._set_size(len(data.blocks) - 1)

        self._events.setText(data.events.hex())
        for i, block in enumerate(data.blocks[1:]):
            self._stack.widget(i).setText(block.hex())


    def _events_edited(self, text: str) -> None:
        '''
        Emits the data_edited signal
        '''
        if is_raw_data_valid(text, 8):
            self.data_edited.emit(-1, self.data)
            self._events.setStyleSheet('')

        else:
            self._events.setStyleSheet('background-color: #ffd2d2;')


    def _block_changed(self, index: int) -> None:
        '''
        Shows the block at the new index
        '''
        self._stack.setCurrentIndex(index)


    def _block_edited(self, index: int, text: str) -> None:
        '''
        Emits the data_edited signal
        '''
        if is_raw_data_valid(text, 8):
            self.data_edited.emit(index, text)
            self._stack.widget(index).setStyleSheet('')

        else:
            self._stack.widget(index).setStyleSheet('background-color: #ffd2d2;')

        self.data_edited.emit(index, text)



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
        try:
            self.layout().removeWidget(self._data_widget)
            self._data_widget.deleteLater()
        except: pass

        if data.format == RawData.Format.Vanilla: self._data_widget = OldSpriteRawEditor()
        else: self._data_widget = NewSpriteRawEditor()

        self._data_widget.data = data
        self._data_widget.data_edited.connect(self.data_edited)
        self.layout().addWidget(self._data_widget)
