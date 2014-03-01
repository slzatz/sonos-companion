#!/usr/bin/env python

#note needs to be run as sudo python buttons.py to access GPIO 
from time import sleep
import traceback
import RPi.GPIO as GPIO
from soco import SoCo

DEBUG = 1

WSHU = 23 #18
WNYC = 24
PANDORA = 18 #23 

GPIO.setmode(GPIO.BCM)

# set up the button interface pins
for n in [WSHU, WNYC, PANDORA]:
    GPIO.setup(n, GPIO.IN)

sonos = SoCo('192.168.1.103')

def play_uri(uri, name):
    try:
        sonos.play_uri(uri)
    except:
        print traceback.format_exc()
        print name
    else:
        if DEBUG:
            print "switched to "+name

#mcp3008 pins
SPICLK = 22 #18
SPIMISO = 17 #23
SPIMOSI = 4 #24
SPICS = 25

# set up the SPI interface pins
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)

# 10k trim pot connected to adc #0
potentiometer_adc = 0;

last_read = 0       # this keeps track of the last potentiometer value
tolerance = 5       # to keep from being jittery we'll only change volume when the pot has moved more than 5 'counts'
n = 0               # counter in while loop

# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
    if ((adcnum > 7) or (adcnum < 0)):
        return -1

    GPIO.output(cspin, True)

    GPIO.output(clockpin, False)  # start clock low
    GPIO.output(cspin, False)     # bring CS low

    commandout = adcnum
    commandout |= 0x18  # start bit + single-ended bit
    commandout <<= 3    # we only need to send 5 bits here
    for i in range(5):
        if (commandout & 0x80):
            GPIO.output(mosipin, True)
        else:
            GPIO.output(mosipin, False)
            commandout <<= 1
            GPIO.output(clockpin, True)
            GPIO.output(clockpin, False)

    adcout = 0
    # read in one empty bit, one null bit and 10 ADC bits
    for i in range(12):
        GPIO.output(clockpin, True)
        GPIO.output(clockpin, False)
        adcout <<= 1
        if (GPIO.input(misopin)):
            adcout |= 0x1

    GPIO.output(cspin, True)
        
    adcout >>= 1       # first bit is 'null' so drop it
    return adcout

def main()     
 
    while True:

        # responding to push buttons
        if GPIO.input(WNYC)==False:
            station = 'wnyc'
            play_uri('aac://204.93.192.135:80/wnycfm-tunein.aac', 'wnyc')
                
        if GPIO.input(PANDORA)==False:
            station = 'quickmix'
            play_uri('pndrradio:52877953807377986', 'quickmix') #, meta='')
                
        if GPIO.input(WSHU)==False:
            station = 'wshu'
            play_uri('x-rincon-mp3radio://wshu.streamguys.org/wshu-news', 'wshu')


        # volume control code

        # read the analog pin
        trim_pot = readadc(potentiometer_adc, SPICLK, SPIMOSI, SPIMISO, SPICS)

        if abs(trim_pot - last_read) > tolerance:
 
            set_volume = trim_pot / 10.24           # convert 10bit adc0 (0-1024) trim pot read into 0-100 volume level
            set_volume = round(set_volume)          # round out decimal value
            set_volume = int(set_volume)            # cast volume as integer

            print 'Volume = {}%'.format(set_volume)
            #sonos.volume = set_volume
                    
            last_read = trim_pot

        n+=1
        if n == 1000:
            if DEBUG:
                print 'station: {}'.format(station)
                print 'volume: {}'.format(trim_pot)
            n = 0

        sleep(0.1)


try:
    main()
except KeyboardInterrupt:
    GPIO.cleanup()
    print "Keyboard Interrupt"

