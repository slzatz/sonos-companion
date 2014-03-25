#!/usr/bin/env python

#should be used with vkey_sketch2.ino

from time import sleep
import traceback
from soco import SoCo
from soco import SonosDiscovery
import serial

#ser = serial.Serial("/dev/ttyACM0", 9600, timeout=1)
ser = serial.Serial("/dev/ttyACM0", 9600, timeout=0)
#ser.stopbits = 2
#a = ''
sonos_devices = SonosDiscovery()
speakers = [SoCo(ip) for ip in sonos_devices.get_speaker_ips()]
for s in speakers:
    print '{}: {}'.format(s.player_name,s.speaker_ip)

#{item: word.count(item) for item in set(word)}
d = {SoCo(ip).player_name: SoCo(ip).speaker_ip for ip in sonos_devices.get_speaker_ips()}
e = {SoCo(ip).player_name: SoCo(ip) for ip in sonos_devices.get_speaker_ips()}

print d

#print dir(speakers[0])

#sonos.partymode() #not sure this works - it didn't work
info = speakers[0].get_speaker_info() #'zone_name'
zone_name = info['zone_name']
master_ip = d[zone_name]

for s in speakers:
    if s.speaker_ip == master_ip:
        master = s
        break

print 'master = {}: {}'.format(master.player_name,master.speaker_ip)

master2 = e[zone_name]

print 'master2 = {}: {}'.format(master2.player_name,master2.speaker_ip)


uid = master.get_speaker_info()['uid']
print uid

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
    button = ser.read(2)
    if button:
        print "button pushed"
        print button
        #a = ''
        button = int(button)
        if 0 < button < 13:
            n = button-1
            play_uri(z[n][1], z[n][0])        
    sleep(.1)
    
