"""Desktop entry point. Run with the configured Python environment: python app.py.

QApplication owns Qt's event loop. Keeping a named reference to MainWindow
prevents Python from collecting the window while the application is running.
"""
# Load sys for use in this module.
import sys
# Bring in QApplication from PySide6.QtWidgets.
from PySide6.QtWidgets import QApplication
# Bring in MainWindow from parentvault.gui.
from parentvault.gui import MainWindow

# Run the entry point only when the file is launched directly.
if __name__ == '__main__':
    # Qt needs one application object before any widgets are created.
    application=QApplication(sys.argv)
    # Create the controller and its widgets before entering the event loop.
    window=MainWindow()
    # Use show on window.
    window.show()
    # exec() dispatches clicks and repaint events until the window closes. Pass its exit code back to Windows.
    sys.exit(application.exec())
