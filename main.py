from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer, QThread
from PyQt5 import uic
import sys
import serial
import numpy as np 
import os
import time
import threading
import signal
import time
import binascii
import queue
import cv2

class radar(QThread):
    def __init__(self, radar_uart, radar_string):
        super().__init__()
        self.radar_uart = radar_uart
        self.radar_string = radar_string

    def run(self):
        while True:
            string_byte = self.radar_uart.readline()
            string = str(string_byte)
            self.radar_string.setText(string)

class thermal(QThread):
    def __init__(self, uart, main_queue):
        super().__init__()
        self.uart = uart
        self.main_queue = main_queue
        sending_1 = [0x02, 0x00, 0x04, 0x00, 0x01, 0x55, 0xaa, 0x03, 0xFA]
        sending_2 = [0x02, 0x00, 0x04, 0x01, 0x01, 0x00, 0x5, 0x03, 0x01]
        # sending_2 = [0x02, 0x00, 0x04, 0x01, 0x01, 0x00, 0x0a, 0x03, 0x0E]
        sending_3 = [0x02, 0x00, 0x04, 0x02, 0x01, 0x00, 0x01, 0x03, 0x06]
        sending_4 = [0x02, 0x00, 0x04, 0x02, 0x01, 0x01, 0x01, 0x03, 0x07]
        self.cnt1 = 0
        self.frame2 = np.zeros(4800)
        cnt = 0
        time.sleep(0.1)
        print("second command to fly")
        self.uart.write(sending_2)
        time.sleep(0.1)
        self.first = 1
        self.image_cnt = 0
        passFlag = np.zeros(6)
        start_frame = 0
        self.uart.write(sending_4)
        self.begin = 0
        check_cnt = 0

        self.uart.write(sending_1)
        while True:
            line = self.uart.read()
            cnt = cnt + 1
            if cnt >= 9:
                cnt = 0
                break
        self.uart.write(sending_4)

    def run(self):
        
        while True:
        
            try:
                # global fvs # FileVideoStream
                line = self.uart.read()
                self.cnt1 = self.cnt1 + 1
                if self.begin == 0 and self.cnt1 == 1:
                    rawDataHex = binascii.hexlify(line)
                    rawDataDecimal = int(rawDataHex, 16)
                    if rawDataDecimal == 2:
                        self.begin = 1
                    else:
                        self.begin = 0
                        self.cnt1 = 0
                        continue
                if self.begin == 1 and self.cnt1 == 20:
                    for i in range(0, 9600):
                        line = self.uart.read()
                        self.cnt1 = self.cnt1 + 1
                        rawDataHex = binascii.hexlify(line)
                        rawDataDecimal = int(rawDataHex, 16)
                        if self.first == 1:
                            dec_10 = rawDataDecimal * 256
                            self.first = 2
                        elif self.first == 2:
                            self.first = 1
                            dec = rawDataDecimal
                            self.frame2[self.image_cnt] = dec + dec_10
                            self.image_cnt = self.image_cnt + 1

                        if self.image_cnt >= 4800:
                            self.image_cnt = 0
                            error = np.mean(self.frame2)
                            if error > 7 and error < 8:
                                continue
                            self.main_queue.put(self.frame2)
                            #print("send the frame\n")

                if self.cnt1 == 2 and self.begin == 1:
                    rawDataHex = binascii.hexlify(line)
                    rawDataDecimal = int(rawDataHex, 16)
                    if rawDataDecimal == 0x25:
                        self.begin = 1
                    else:
                        self.begin = 0
                        self.cnt1 = 0
                        continue
                if self.cnt1 == 3 and self.begin == 1:
                    rawDataHex = binascii.hexlify(line)
                    rawDataDecimal = int(rawDataHex, 16)
                    if rawDataDecimal == 0xA1:
                        self.begin = 1
                    else:
                        self.begin = 0
                        self.cnt1 = 0
                        continue

                if self.cnt1 == 9638 and self.begin == 1:
                    self.begin = 0
                    self.cnt1 = 0
                else:
                    continue

            except:
                continue

class vision(QThread):
    def __init__(self, cap, vision_widget):
        super().__init__()
        self.cap = cap
        self.vision_widget = vision_widget

    def run(self):
        while True:
            ret, frame = self.cap.read()
            frame = cv2.resize(frame, (640, 480))
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            qpixmap = QPixmap.fromImage(convert_to_Qt_format)
            self.vision_widget.setPixmap(qpixmap)
            
            self.vision_widget.show()
            
class thermal_main(QThread):
    def __init__(self, main_queue, thermal):
        super().__init__()
        self.main_queue = main_queue
        self.thermal = thermal


    def run(self):
        while True:
            frame1 = self.main_queue.get()
            max = np.max(frame1)
            min = np.min(frame1)

            nfactor = 255 / (max - min)
            pTemp = frame1 - min
            nTemp = pTemp * nfactor
            frame1 = nTemp
            image = frame1.reshape(60, 80)
            #image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
            uint_img = np.array(image).astype('uint8')
            
            grayImage = cv2.cvtColor(uint_img, cv2.COLOR_GRAY2BGR)
            grayImage = cv2.resize(grayImage, (640, 480))
            grayImage = cv2.flip(grayImage, 1)
            image = QImage(grayImage.data, grayImage.shape[1], grayImage.shape[0], QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            self.thermal.setPixmap(pixmap)         
            self.thermal.show()

class monitor(QMainWindow):
    def __init__(self):
        super(monitor, self).__init__()
        uic.loadUi("monitor.ui", self)
        self.show()

        #self.thermal.setScaledContents(True)
        #self.vision.setScaledContents(True)

        self.main_queue = queue.Queue()

        self.radar_uart = serial.Serial(port='/dev/ttyUSB0', baudrate=115200)
        self.thermal_uart = serial.Serial(port='/dev/ttyACM0', baudrate=115200)
        self.cap = cv2.VideoCapture("/dev/video0")

        self.tRadar = radar(self.radar_uart, self.radar)
        self.tRadar.start()
        self.tThermal = thermal(self.thermal_uart, self.main_queue)
        self.tThermal.start()
        self.tVision = vision(self.cap, self.vision)
        self.tVision.start()
        self.tThermal_main = thermal_main(self.main_queue, self.thermal)
        self.tThermal_main.start()

        #self.timer = QTimer()
        #self.timer.setInterval(100)
        #self.timer.timeout.connect(self.timerthermalService)
        #self.timer.start()

    def timerthermalService(self):
        frame1 = self.main_queue.get()
        max = np.max(frame1)
        min = np.min(frame1)

        nfactor = 255 / (max - min)
        pTemp = frame1 - min
        nTemp = pTemp * nfactor
        frame1 = nTemp
        image = frame1.reshape(60, 80)
        #image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        uint_img = np.array(image).astype('uint8')
        
        grayImage = cv2.cvtColor(uint_img, cv2.COLOR_GRAY2BGR)
        grayImage = cv2.resize(grayImage, (320, 240))
        grayImage = cv2.flip(grayImage, 1)
        image = QImage(grayImage.data, grayImage.shape[1], grayImage.shape[0], QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image)
        self.thermal.setPixmap(pixmap)
        self.thermal.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = monitor()
    window.show()
    sys.exit(app.exec_())