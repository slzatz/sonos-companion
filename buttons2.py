#!/usr/bin/env python

#note needs to be run as sudo python buttons.py to access GPIO 
from time import sleep
import sys
import traceback
import RPi.GPIO as GPIO
from soco import SoCo

DEBUG = 1

WSHU = 23 #18
WNYC = 24
PANDORA = 18 #23 

GPIO.setmode(GPIO.BCM)

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
tolerance = 5       # to keep from being jittery we'll only change
                    # volume when the pot has moved more than 5 'counts'

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

n=0        
 
while True:

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
    # we'll assume that the pot didn't move
    trim_pot_changed = False

    # read the analog pin
    trim_pot = readadc(potentiometer_adc, SPICLK, SPIMOSI, SPIMISO, SPICS)
    # how much has it changed since the last read?
    pot_adjust = abs(trim_pot - last_read)

    if ( pot_adjust > tolerance ):
       trim_pot_changed = True

    if 0:
       print "trim_pot_changed", trim_pot_changed

    if ( trim_pot_changed ):
        set_volume = trim_pot / 10.24           # convert 10bit adc0 (0-1024) trim pot read into 0-100 volume level
        set_volume = round(set_volume)          # round out decimal value
        set_volume = int(set_volume)            # cast volume as integer

        print 'Volume = {volume}%' .format(volume = set_volume)
        set_vol_cmd = 'sudo amixer cset numid=1 -- {volume}% > /dev/null' .format(volume = set_volume)
        
        sonos.volume = set_volume
                

        if 0:
            print "set_volume", set_volume
            print "tri_pot_changed", set_volume

        # save the potentiometer reading for the next loop
        last_read = trim_pot

    n+=1
    if n == 1000:
        if DEBUG:
            print 'station set to '+station
            print "trim_pot:", trim_pot
            print "pot_adjust:", pot_adjust
            print "last_read", last_read

        n = 0

    sleep(0.1)

z = '''{'R.E.M. Radio': '637630342339192386', 'Nick Drake Radio': '409866109213435458', 'Dar Williams Radio': '1823409579416053314', 'My Morning Jacket Radio': '1776327778550113858', 'Patty
 Griffin Radio': '52876609482614338', 'Lucinda Williams Radio': '360878777387148866', 'Neil Young Radio': '52876154216080962', 'Wilco Radio': '1025897885568558658', 'The Decemberists
 Radio': '686295066286974530', 'The Innocence Mission Radio': '686869410788632130', 'Kris Delmhorst Radio': '610111769614181954', 'Counting Crows Radio': '1727297518525703746', 'Iron
 & Wine Radio': '686507220491527746', 'Bob Dylan Radio': '1499257703118366274', "slzatz's QuickMix": 'qm86206018', 'Ray LaMontagne Radio': '1726130468537198146', 'Vienna Teng Radio':
 '138764603804051010', 'QuickMix':'52877953807377986'}
'''

meta = '&lt;DIDL-Lite xmlns:dc=&quot;http://purl.org/dc/elements/1.1/&quot; xmlns:upnp=&quot;urn:schemas-upnp-org:metadata-1-0/upnp/&quot;xmlns:r=&quot;urn:schemas-rinconnetworks-com:metadata-1-0/&quot; xmlns=&quot;urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/&quot;&gt;&lt;item id=&quot;OOOX{music_service_station_id}&quot; parentID=&quot;0&quot; restricted=&quot;true&quot;&gt;&lt;dc:title&gt;{music_service_station_title}&lt;/dc:title&gt;&lt;upnp:class&gt;object.item.audioItem.audioBroadcast&lt;/upnp:class&gt;&lt;desc id=&quot;cdudn&quot; nameSpace=&quot;urn:schemas-rinconnetworks-com:metadata-1-0/&quot;&gt;SA_RINCON3_{music_service_email}&lt;/desc&gt;&lt;/item&gt;&lt;/DIDL-Lite&gt;'.format(music_service = 'pndrradio', music_service_station_title = 'Patty Griffin Radio', music_service_station_id = '52876154216080962', music_service_email = 'slzatz@gmail.com')

