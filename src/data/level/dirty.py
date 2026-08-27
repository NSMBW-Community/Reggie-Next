import globals_


def SetDirty(noautosave=False):
    if globals_.DirtyOverride > 0:
        return

    if not noautosave:
        globals_.AutoSaveDirty = True
    if globals_.Dirty:
        return

    globals_.Dirty = True
    try:
        if globals_.mainWindow is not None:
            globals_.mainWindow.UpdateTitle()
    except Exception:
        pass
