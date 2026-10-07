from PyQt6 import QtWidgets
from data.common import archive
from libs import lh, lz77
import os

from data import globals_
from ui.theme.reggie_theme import GetIcon

class AreaImportDialog(QtWidgets.QDialog):
    """
    Dialog which lets you choose an area to import
    """

    def __init__(self):
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

    def load_source_level(self):
        """
        Loads the source level and returns the number of areas.
        """
        filetypes = ''
        filetypes += globals_.trans.string('FileDlgs', 1) + ' (*' + '.arc' + ');;'  # *.arc
        filetypes += globals_.trans.string('FileDlgs', 5) + ' (*' + '.arc' + '.LH);;'  # *.arc.LH
        filetypes += globals_.trans.string('FileDlgs', 10) + ' (*' + '.arc' + '.LZ);;'  # *.arc.LZ
        filetypes += globals_.trans.string('FileDlgs', 2) + ' (*)'  # *

        fn = QtWidgets.QFileDialog.getOpenFileName(self, globals_.trans.string('FileDlgs', 0), '', filetypes)[0]
        if fn == '':
            return 0

        self.file_name = os.path.basename(fn)

        with open(str(fn), 'rb') as fileobj:
            arcdata = fileobj.read()

        if (arcdata[0] & 0xF0) == 0x40:  # If LH-compressed
            try:
                arcdata = lh.UncompressLH(arcdata)
            except IndexError:
                QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_Decompress', 0),
                                                globals_.trans.string('Err_Decompress', 1, '[file]', str(fn)))
                return 0
        elif not arcdata.startswith(b"U\xAA8-"):  # If LZ-compressed
            try:
                arcdata = lz77.UncompressLZ77(arcdata)
            except IndexError:
                QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_Decompress', 0),
                                                globals_.trans.string('Err_Decompress', 2, '[file]', str(fn)))
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
                    if max_area > area_count:
                        area_count = max_area

        return area_count

    def level_selected(self):
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
