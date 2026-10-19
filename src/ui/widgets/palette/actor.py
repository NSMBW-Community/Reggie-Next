from PyQt6 import QtWidgets, QtCore
Qt = QtCore.Qt

from data import globals_

from ui.theme.reggie_theme import GetIcon
from data.common.loaders import LoadActorCategories
from data.level.dirty import SetDirty

from ui.widgets.sidelists.actor_picker import ActorPickerWidget
from ui.widgets.sidelists.sprite_list import ActorList
from ui.widgets.sidelists.actor_order import ActorOrderList

from data.level.items.actor import ActorItem
from actorlib import ActorImage

class ActorTab(QtWidgets.QTabWidget):
    """
    Represents the Actors tab in the palette
    """
    def __init__(self):
        super().__init__(None)
        self.currentChanged.connect(self.tab_changed)

        # Add Actors tab
        self.add_actor_tab = QtWidgets.QWidget()
        self.addTab(self.add_actor_tab, GetIcon('rocket-plus'), globals_.trans.string('Palette', 25))

        view_lyt = QtWidgets.QHBoxLayout()
        view_lyt.addWidget(QtWidgets.QLabel(globals_.trans.string('Palette', 4)))

        self.search_lyt = QtWidgets.QHBoxLayout()
        self.search_lyt.addWidget(QtWidgets.QLabel(globals_.trans.string('Palette', 5)))

        LoadActorCategories()

        self.view_picker = QtWidgets.QComboBox()
        for view in globals_.ActorCategories:
            self.view_picker.addItem(view.name)
        self.view_picker.currentIndexChanged.connect(self.curr_view_changed)

        view_lyt.addWidget(self.view_picker, 1)

        self.search_box = QtWidgets.QLineEdit()
        self.search_box.textChanged.connect(self.set_search_string)
        self.search_lyt.addWidget(self.search_box, 1)

        self.actor_picker = ActorPickerWidget()
        self.actor_picker.ActorChanged.connect(self.actor_selected)
        self.actor_picker.ActorReplace.connect(self.actor_replaced)
        self.actor_picker.SwitchView(globals_.ActorCategories[0])

        self.default_prop_button = QtWidgets.QPushButton(globals_.trans.string('Palette', 6))
        self.default_prop_button.setEnabled(False)
        self.default_prop_button.clicked.connect(self.show_default_props_dock)

        sdpl = QtWidgets.QHBoxLayout()
        sdpl.addStretch(1)
        sdpl.addWidget(self.default_prop_button)
        sdpl.addStretch(1)

        add_actor_lyt = QtWidgets.QVBoxLayout(self.add_actor_tab)
        add_actor_lyt.addLayout(view_lyt)
        add_actor_lyt.addLayout(self.search_lyt)
        add_actor_lyt.addWidget(self.actor_picker, 1)
        add_actor_lyt.addLayout(sdpl)


        # Current actors
        self.current_actor_tab = QtWidgets.QWidget()
        self.addTab(self.current_actor_tab, GetIcon('rocket-document-list'), globals_.trans.string('Palette', 26))

        curr_label = QtWidgets.QLabel(globals_.trans.string('Palette', 11))
        curr_label.setWordWrap(True)

        self.actor_list = ActorList()

        curr_actor_lyt = QtWidgets.QVBoxLayout(self.current_actor_tab)
        curr_actor_lyt.addWidget(curr_label)
        curr_actor_lyt.addWidget(self.actor_list)


        # Actor Order
        self.actor_order_tab = QtWidgets.QWidget()
        self.addTab(self.actor_order_tab, GetIcon('rocket-arrow'), globals_.trans.string('Palette', 39))

        order_label = QtWidgets.QLabel(globals_.trans.string('Palette', 40))
        order_label.setWordWrap(True)
        self.actor_order_list = ActorOrderList()

        order_layout = QtWidgets.QVBoxLayout(self.actor_order_tab)
        order_layout.addWidget(order_label)
        order_layout.addWidget(self.actor_order_list)

    def tab_changed(self, new_tab):
        """
        Handles the selected tab changing
        """
        if new_tab == 0:
            paint_type = 4 # Actors
        else:
            paint_type = -1 # None

        globals_.CurrentPaintType = paint_type

    def actor_selected(self, actor_num):
        """
        Handles a new actor being chosen
        """
        if globals_.mainWindow is None:
            return

        globals_.CurrentActor = actor_num

        if actor_num != 1000 and actor_num >= 0:
            globals_.mainWindow.defaultDataEditor.setActor(actor_num, initial_data=bytes(10))
            self.default_prop_button.setEnabled(True)
        else:
            self.default_prop_button.setEnabled(False)
            globals_.mainWindow.defaultPropDock.setVisible(False)
            globals_.mainWindow.defaultDataEditor.updateFields()

    def actor_replaced(self, actor_num):
        """
        Handles a new actor type being chosen to replace the selected actors
        """
        if globals_.mainWindow is None:
            return

        items = globals_.mainWindow.scene.selectedItems()
        changed = False

        for spr in items:
            if isinstance(spr, ActorItem):
                # Reset actordata
                spr.actordata = globals_.mainWindow.defaultDataEditor.data
                spr.SetType(actor_num)
                spr.update()

                # Assign the new actor image class
                image_classes = globals_.gamedef.getImageClasses()
                if actor_num in image_classes:
                    spr.setImageObj(image_classes[actor_num])
                else:
                    spr.setImageObj(ActorImage)
                changed = True

        if changed:
            # Fixes any issues from outdated types
            globals_.Area.InitialiseIdTypes()
            SetDirty()

        globals_.mainWindow.ChangeSelectionHandler()

    def curr_view_changed(self, type):
        """
        Handles a new actor view being chosen
        """
        cat = globals_.ActorCategories[type]
        self.actor_picker.SwitchView(cat)

        isSearch = (type == 0)
        layout = self.search_lyt

        # Show/hide the searchbar
        # Item 0 is "Search:", 1 is the box itself
        for i in range(2):
            item = layout.itemAt(i)
            if item is None:
                return

            widget = item.widget()
            if widget is None:
                return

            widget.setVisible(isSearch)

    def set_search_string(self, text):
        """
        Handles a new actor search term being entered
        """
        self.actor_picker.SetSearchString(text)

    def show_default_props_dock(self):
        """
        Handles the Show Default Properties button being clicked
        """
        if globals_.mainWindow is not None:
            globals_.mainWindow.defaultPropDock.setVisible(True)

    def prepare_batch_add(self):
        """
        Helper to prepare adding actors in batch
        """
        self.actor_list.prepareBatchAdd()
        self.actor_order_list.prepareBatchAdd()

    def add_actor(self, actor):
        """
        Helper to add an actor to the lists
        """
        self.actor_list.addActor(actor)
        self.actor_order_list.addActor(actor)

    def end_batch_add(self):
        """
        Helper to end batch-adding
        """
        self.actor_list.endBatchAdd()
        self.actor_order_list.endBatchAdd()
