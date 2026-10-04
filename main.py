import sys
from PyQt6.QtWidgets import QApplication
from ui.gui import CyberDorkGUI

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CyberDorkGUI()
    window.show()
    sys.exit(app.exec())
