import sys

import qdarktheme
from PySide6.QtWidgets import QApplication

from nnmm.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication()
    qdarktheme.setup_theme()
    window_main = MainWindow()
    window_main.show()
    sys.exit(app.exec())
