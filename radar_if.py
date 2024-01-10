import serial
import numpy as np 

radar = serial.Serial(port='/dev/ttyUSB0', baudrate=115200)

while True:
    string = radar.readline()
    print(string)
    
