#!/usr/bin/env python
 
from time import sleep
import os
import RPi.GPIO as GPIO
from soco import SoCo

WNYC = 24
OTHER = 23 


GPIO.setmode(GPIO.BCM)

for n in [WNYC, OTHER]:

    GPIO.setup(n, GPIO.IN)

sonos = SoCo('192.168.1.103')
 
while True:
    if GPIO.input(WNYC)==False:
        sonos.play_uri('aac://204.93.192.135:80/wnycfm-tunein.aac')
        print "switched to wnyc"
    if GPIO.input(OTHER)==False:
        print "pushed other"

    sleep(0.1);
