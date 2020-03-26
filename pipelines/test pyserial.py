# Created by Medad Rufus Newman on 12/03/2020



import serial
ser = serial.Serial('COM14')
s = ser.read(100)       # read up to one hundred bytes
                        # or as much is in the buffer
print(s)