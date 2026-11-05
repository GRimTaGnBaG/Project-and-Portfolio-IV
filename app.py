"""Desktop entry point. Run with the configured Python environment: python app.py.

QApplication owns Qt's event loop. Keeping a named reference to MainWindow
prevents Python from collecting the window while the application is running.
"""
import sys
from PySide6.QtWidgets import QApplication
from parentvault.gui import MainWindow

# DEMO 01 | Start the desktop app
# QApplication owns the event loop. MainWindow builds the screens, and
# application.exec() keeps listening for clicks, repaint events, and worker results.
if __name__ == '__main__':
    application=QApplication(sys.argv)
    window=MainWindow()
    window.show()
    sys.exit(application.exec())
