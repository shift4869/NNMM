import sys

from PySide6.QtWidgets import QApplication

from nnmm.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication()
    window_main = MainWindow()
    window_main.show()
    sys.exit(app.exec())
