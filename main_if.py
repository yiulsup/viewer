from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic
import sys

class monitor(QMainWindow):
    def __init__(self):
        super(monitor, self).__init__()
        uic.loadUi("monitor.ui", self)
        self.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = monitor()
    window.show()
    sys.exit(app.exec_())