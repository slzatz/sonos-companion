#!/usr/bin/env python

#note needs to be run as sudo python buttons.py to access GPIO 
from time import sleep
import os
import RPi.GPIO as GPIO
from soco import SoCo

WNYC = 24
PANDORA = 23 

GPIO.setmode(GPIO.BCM)

for n in [WNYC, PANDORA]:

    GPIO.setup(n, GPIO.IN)

sonos = SoCo('192.168.1.103')
 
while True:
    if GPIO.input(WNYC)==False:
        sonos.play_uri('aac://204.93.192.135:80/wnycfm-tunein.aac')
        print "switched to wnyc"
    if GPIO.input(PANDORA)==False:
        # that is Patty Griffin Radio; seems like meta can be blank and it still works
        sonos.play_uri('pndrradio:52876609482614338', meta='')

    sleep(0.1)


z = '''{'R.E.M. Radio': '637630342339192386', 'Nick Drake Radio': '409866109213435458', 'Dar Williams Radio': '1823409579416053314', 'My Morning Jacket Radio': '1776327778550113858', 'Patty
 Griffin Radio': '52876609482614338', 'Lucinda Williams Radio': '360878777387148866', 'Neil Young Radio': '52876154216080962', 'Wilco Radio': '1025897885568558658', 'The Decemberists
 Radio': '686295066286974530', 'The Innocence Mission Radio': '686869410788632130', 'Kris Delmhorst Radio': '610111769614181954', 'Counting Crows Radio': '1727297518525703746', 'Iron
 & Wine Radio': '686507220491527746', 'Bob Dylan Radio': '1499257703118366274', "slzatz's QuickMix": 'qm86206018', 'Ray LaMontagne Radio': '1726130468537198146', 'Vienna Teng Radio':
 '138764603804051010'}
'''

meta = '&lt;DIDL-Lite xmlns:dc=&quot;http://purl.org/dc/elements/1.1/&quot; xmlns:upnp=&quot;urn:schemas-upnp-org:metadata-1-0/upnp/&quot;xmlns:r=&quot;urn:schemas-rinconnetworks-com:metadata-1-0/&quot; xmlns=&quot;urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/&quot;&gt;&lt;item id=&quot;OOOX{music_service_station_id}&quot; parentID=&quot;0&quot; restricted=&quot;true&quot;&gt;&lt;dc:title&gt;{music_service_station_title}&lt;/dc:title&gt;&lt;upnp:class&gt;object.item.audioItem.audioBroadcast&lt;/upnp:class&gt;&lt;desc id=&quot;cdudn&quot; nameSpace=&quot;urn:schemas-rinconnetworks-com:metadata-1-0/&quot;&gt;SA_RINCON3_{music_service_email}&lt;/desc&gt;&lt;/item&gt;&lt;/DIDL-Lite&gt;'.format(music_service = 'pndrradio', music_service_station_title = 'Patty Griffin Radio', music_service_station_id = '52876154216080962', music_service_email = 'slzatz@gmail.com')

