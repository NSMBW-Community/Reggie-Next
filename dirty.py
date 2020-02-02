from PyQt5 import QtCore

import globals_

def SetDirty(noautosave = False):
    if globals_.DirtyOverride > 0: return

    if not noautosave: globals_.AutoSaveDirty = True
    if globals_.Dirty: return

    globals_.Dirty = True
    try:
        globals_.mainWindow.UpdateTitle()
    except Exception:
        pass


def setting(name, default=None):
    """
    Thin wrapper around QSettings, fixes the type=bool bug
    """
    types_str = {str: 'str', int: 'int', float: 'float', dict: 'dict', bool: 'bool', QtCore.QByteArray: 'QByteArray', type(None): 'NoneType'}
    types = {'str': str, 'int': int, 'float': float, 'dict': dict, 'bool': bool, 'QByteArray': QtCore.QByteArray}

    type_ = globals_.settings.value('typeof(%s)' % name, types_str[type(default)], str)
    if type_ == 'NoneType':
        return None

    return globals_.settings.value(name, default, types[type_])


def setSetting(name, value):
    """
    Thin wrapper around QSettings
    """
    types_str = {str: 'str', int: 'int', float: 'float', dict: 'dict', bool: 'bool', QtCore.QByteArray: 'QByteArray', type(None): 'NoneType'}
    assert isinstance(name, str) and type(value) in types_str

    globals_.settings.setValue(name, value)
    globals_.settings.setValue('typeof(%s)' % name, types_str[type(value)])

