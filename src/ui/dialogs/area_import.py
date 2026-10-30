import os

from PyQt6 import QtWidgets

from data import globals_
from data.common import archive
from data.common.loaders import DecompressLevel
from libs import lh, lz77
from ui.theme.reggie_theme import GetIcon


class AreaImportDialog(QtWidgets.QDialog):
    """
    Dialog which lets you choose an area to import
    """

    def __init__(self) -> None:
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(globals_.trans.string('AreaImportDlg', 0))
        self.setWindowIcon(GetIcon('wooden-box--arrow'))

        curr_area_count = len(globals_.Level.areas) + 1
        info = QtWidgets.QLabel()
        info.setText(globals_.trans.string('AreaImportDlg', 4, '[num]', curr_area_count))

        self.level_button = QtWidgets.QPushButton(globals_.trans.string('AreaImportDlg', 6))
        self.level_button.clicked.connect(self.level_selected)

        self.area_combo = QtWidgets.QComboBox()
        self.area_combo.setEnabled(False)

        self.stay_in_area = QtWidgets.QCheckBox()

        form_lyt = QtWidgets.QFormLayout()
        form_lyt.addRow(globals_.trans.string('AreaImportDlg', 5), self.level_button)
        form_lyt.addRow(globals_.trans.string('AreaImportDlg', 3), self.area_combo)
        form_lyt.addRow(globals_.trans.string('AreaImportDlg', 7), self.stay_in_area)

        self.ok_button = QtWidgets.QPushButton()
        self.ok_button.setText(globals_.trans.string('AreaImportDlg', 8))
        self.ok_button.setEnabled(False)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        button_box.addButton(self.ok_button, QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(form_lyt)
        main_layout.addWidget(info)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)

    def load_source_level(self) -> int:
        """
        Loads the source level and returns the number of areas.
        """
        filter = (
            f'{globals_.trans.string('FileDlgs', 9)} (*.arc *.arc.LH *.arc.LZ);;'
            f'{globals_.trans.string('FileDlgs', 1)} (*.arc);;'
            f'{globals_.trans.string('FileDlgs', 5)} (*.arc.LH);;'
            f'{globals_.trans.string('FileDlgs', 10)} (*.arc.LZ);;'
            f'{globals_.trans.string('FileDlgs', 2)} (*)'
        )

        fn = QtWidgets.QFileDialog.getOpenFileName(self, globals_.trans.string('FileDlgs', 0), '', filter)[0]
        if fn == '':
            return 0

        self.file_name = os.path.basename(fn)

        with open(str(fn), 'rb') as fileobj:
            arcdata = fileobj.read()

        arcdata = DecompressLevel(arcdata, str(fn))
        if arcdata is None:
            return 0

        self.archive = archive.U8.load(arcdata)

        # Get the area count
        area_count = 0

        for item, val in self.archive.files:
            if val is not None:
                # It's a file
                fname = item[item.rfind('/') + 1:]
                if fname.startswith('course'):
                    max_area = int(fname[6])
                    area_count = max(area_count, max_area)

        return area_count

    def level_selected(self) -> None:
        """
        Handles updating everything when a level is selected
        """
        area_count = self.load_source_level()

        self.area_combo.clear()
        self.area_combo.setEnabled(area_count != 0)
        self.ok_button.setEnabled(area_count != 0 and self.archive is not None)

        # Level is invalid or nothing was picked
        if area_count == 0:
            return

        self.level_button.setText(self.file_name)
        for i in range(area_count):
            self.area_combo.addItem(globals_.trans.string('AreaImportDlg', 1, '[num]', i + 1))

    def import_area(self) -> None:
        """
        Handles importing the area into the level
        """
        area = self.area_combo.currentIndex() + 1

        # Get the required files
        reqcourse = f'course{area}.bin'
        reqL0 = f'course{area}_bgdatL0.bin'
        reqL1 = f'course{area}_bgdatL1.bin'
        reqL2 = f'course{area}_bgdatL2.bin'
        req_meta = f'course{area}_metadata.json'

        course = None
        L0 = None
        L1 = None
        L2 = None
        meta = None

        for item, val in self.archive.files:
            if val is not None:
                fname = item.split('/')[-1]
                if fname == reqcourse:
                    course = val
                elif fname == reqL0:
                    L0 = val
                elif fname == reqL1:
                    L1 = val
                elif fname == reqL2:
                    L2 = val
                elif fname == req_meta:
                    meta = val

        # Add the area to our level
        globals_.Level.appendArea(course, L0, L1, L2, meta)
        new_id = globals_.Level.areas[-1].areanum

        if self.stay_in_area.isChecked():
            new_id = globals_.Area.areanum

        path = globals_.mainWindow.fileSavePath
        globals_.mainWindow.load_level(path, True, new_id)
