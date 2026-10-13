from PyQt6 import QtCore, QtGui

from data import globals_


def setting[T](name: str, default: T | None = None) -> T | None:
    """
    Thin wrapper around QSettings, fixes the type=bool bug
    """
    types_str = {str: 'str', int: 'int', float: 'float', dict: 'dict', bool: 'bool', QtCore.QByteArray: 'QByteArray',
                 type(None): 'NoneType', QtGui.QKeySequence.StandardKey: 'StandardKey'}
    types = {'str': str, 'int': int, 'float': float, 'dict': dict, 'bool': bool, 'QByteArray': QtCore.QByteArray,
             'StandardKey': QtGui.QKeySequence.StandardKey}

    type_ = globals_.settings.value(f'typeof({name})', types_str[type(default)], str)
    if type_ == 'NoneType':
        return None

    return globals_.settings.value(name, default, types[type_])


def setSetting[T](name: str, value: object) -> None:
    """
    Thin wrapper around QSettings
    """
    types_str = {str: 'str', int: 'int', float: 'float', dict: 'dict', bool: 'bool', QtCore.QByteArray: 'QByteArray',
                 type(None): 'NoneType', QtGui.QKeySequence.StandardKey: 'StandardKey'}
    assert isinstance(name, str) and type(value) in types_str

    globals_.settings.setValue(name, value)
    globals_.settings.setValue(f'typeof({name})', types_str[type(value)])


def delSetting(name: str) -> None:
    """
    Thin wrapper around QSettings, removes both the setting and its type identifier
    """
    assert isinstance(name, str)

    globals_.settings.remove(name)
    globals_.settings.remove(f'typeof({name})')
