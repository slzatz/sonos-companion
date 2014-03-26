#!/usr/bin/env python

#should be used with vkey_sketch2.ino

from time import sleep
#import traceback
from soco import SoCo
from soco import SonosDiscovery
import serial

#ser = serial.Serial("/dev/ttyACM0", 9600, timeout=1)
ser = serial.Serial("/dev/ttyACM0", 9600, timeout=0.5)

sonos_devices = SonosDiscovery()

speakers = {SoCo(ip).player_name: SoCo(ip) for ip in sonos_devices.get_speaker_ips()}

for name,speaker in speakers.items():
    print '{}: {}'.format(name, speaker.speaker_ip)

#sonos.partymode() #not sure this works - it didn't work

info = speakers.values()[0].get_speaker_info()
zone_name = info['zone_name']
master = speakers[zone_name]

print 'master speaker = {}: {}'.format(master.player_name,master.speaker_ip)

master_uid = master.get_speaker_info()['uid']
print 'master_uid=',master_uid

#speakers[1].unjoin()
#speakers[1].join(uid)
#speakers[2].join(uid)

def play_uri(uri, name):
    try:
        master.play_uri(uri)
    except:
        print traceback.format_exc()
        print "had problem switching to "+name
    else:
        print "switched to "+name


z = [
('WNYC', 'aac://204.93.192.135:80/wnycfm-tunein.aac'),
('WSHU', 'x-rincon-mp3radio://wshu.streamguys.org/wshu-news'),
('QuickMix', 'pndrradio:52877953807377986'),
('R.E.M. Radio', 'pndrradio:637630342339192386'), 
('Nick Drake Radio', 'pndrradio:409866109213435458'),
('Dar Williams Radio', 'pndrradio:1823409579416053314'),
('Patty Griffin Radio', 'pndrradio:52876609482614338'),
('Lucinda Williams Radio', 'pndrradio:360878777387148866'),
('Neil Young Radio', 'pndrradio:52876154216080962'),
('Kris Delmhorst Radio', 'pndrradio:610111769614181954'),
('Counting Crows Radio', 'pndrradio:1727297518525703746'), 
('Vienna Teng Radio', 'pndrradio:138764603804051010')]

while True:
    button = ser.readline()
    if button:
        print "button pushed"
        print button
        try:
            button = int(button.strip())
        except:
            n = 0
        if 0 < button < 13:
            n = button-1
            play_uri(z[n][1], z[n][0])        
    sleep(.1)
    
