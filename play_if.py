from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
import numpy as np 
import sys
import cv2

class wrong_input(QDialog):
    def __init__(self):
        super(wrong_input,self).__init__()
        uic.loadUi(r"wrong_input.ui", self)
        self.show()      

class input(QDialog):
    signal_input = pyqtSignal(str)
    def __init__(self):
        super(input,self).__init__()
        uic.loadUi(r"input.ui", self)
        self.show()      
        self.input.clicked.connect(self.text)
        

    def text(self):
        self.value = self.input_text.text()
        self.signal_input.emit(self.value)
        self.close()

class bPlay(QThread):
    def __init__(self, cap, vision, s_Widget):
        super().__init__()
        self.cap = cap
        self.vision = vision
        self.cnt = 0
        self.s_Widget1 = s_Widget

    def run(self):
        cnt = 0
        if not self.cap.isOpened():
            self.d = wrong_input()
            self.s_Widget1.setCurrentIndex(0)
            self.exit()

        while True:
            try:
                ret, frame = self.cap.read()
                self.frame = cv2.resize(frame, (640, 480))
                h, w, ch = self.frame.shape
                bytes_per_line = ch * w
                convert_to_Qt_format = QImage(self.frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                qpixmap = QPixmap.fromImage(convert_to_Qt_format)
                self.vision.setPixmap(qpixmap)
                self.vision.show()
            except:
                continue

    def take(self):
        cv2.imwrite('vision_{}.png'.format(self.cnt), self.frame)
        self.cnt = self.cnt + 1


class vision_play(QMainWindow):
    def __init__(self):
        super(vision_play, self).__init__()
        uic.loadUi("vision.ui", self)
        self.show()

        self.first = 1
        self.s_Widget.setCurrentIndex(0)

        self.mOpen.clicked.connect(self.open)
        self.mPlay.clicked.connect(self.play)
        self.mClose.clicked.connect(self.close)
        self.mTaken.clicked.connect(self.taken)

    def open(self):
        self.inp = input()
        self.inp.signal_input.connect(self.input_text)
        

    @pyqtSlot(str)
    def input_text(self, input_string):
        self.string = input_string
        print(self.string)
        if self.first == 1:
            self.first = 0
            self.cap = cv2.VideoCapture(self.string)
        else:
            self.cap.release()
            self.cap = cv2.VideoCapture(self.string)

    def play(self):
        self.t_0 = bPlay(self.cap, self.vision, self.s_Widget)
        self.t_0.start()
        self.s_Widget.setCurrentIndex(1)

    def taken(self):
        self.t_0.take()

    def close(self):
        if self.first == 1:
            pass
        else:
            print("cap release")
            self.cap.release()
        self.s_Widget.setCurrentIndex(0)
        self.t_0.exit()
        


app = QApplication(sys.argv)
window = vision_play()
window.show()
sys.exit(app.exec_())
