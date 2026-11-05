"""Desktop entry point. Run with the configured Python environment: python app.py.

QApplication owns Qt's event loop. Keeping a named reference to MainWindow
prevents Python from collecting the window while the application is running.
"""
import sys
from PySide6.QtWidgets import QApplication
from parentvault.gui import MainWindow

if __name__ == '__main__':
    # Qt needs one application object before any widgets are created.
    application=QApplication(sys.argv)
    # Create the controller and its widgets before entering the event loop.
    window=MainWindow()
    window.show()
    # exec() dispatches clicks and repaint events until the window closes. Pass its exit code back to Windows.
    sys.exit(application.exec())
