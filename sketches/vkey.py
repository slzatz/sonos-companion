import time
import serial
ser = serial.Serial("/dev/ttyACM0", 9600, timeout=1)
#ser.stopbits = 2
a = ''
while True:
    #while ser.read():
    a = ser.read()
    if a:
        #a+= repr(ser.readline())
        a+= ser.readline()
        #print repr(ser.read())
    #if a:
        print "button pushed"
        print a
        a = ''
    time.sleep(.1)
    
