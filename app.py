"""Desktop entry point. Run with the configured Python environment: python app.py.

QApplication owns Qt's event loop. Keeping a named reference to MainWindow
prevents Python from collecting the window while the application is running.
"""
import sys
from PySide6.QtWidgets import QApplication
from parentvault.gui import MainWindow

if __name__ == '__main__':
    application=QApplication(sys.argv)
    window=MainWindow()
    window.show()
    sys.exit(application.exec())
