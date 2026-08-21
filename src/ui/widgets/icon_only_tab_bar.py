from PyQt6 import QtWidgets

import globals_

class IconsOnlyTabBar(QtWidgets.QTabBar):
    """
    A QTabBar subclass that is designed to only display icons.

    On macOS Mojave (and probably other versions around there),
    QTabWidget tabs are way too wide when only displaying icons.
    This ultimately causes the Reggie palette itself to have a really
    high minimum width.

    This subclass limits tab widths to fix the problem.
    """
    def tabSizeHint(self, index):
        res = super().tabSizeHint(index)
        if globals_.app is None:
            return res

        style = globals_.app.style()
        if style is None:
            return res

        meta_obj = style.metaObject()
        if meta_obj is None:
            return res

        if meta_obj.className() == 'QMacStyle':
            res.setWidth(res.height() * 2)

        return res
