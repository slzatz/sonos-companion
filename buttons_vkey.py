#!/usr/bin/env python

#should be used with vkey_sketch3.ino

from time import sleep
from soco import SoCo
from soco import SonosDiscovery
import serial

#####ser = serial.Serial("/dev/ttyACM0", 9600, timeout=1)
#ser = serial.Serial("/dev/ttyACM0", 9600, timeout=0.5)
#ser = serial.Serial("COM19", 9600, timeout=0.5)

DEBUG = 1

sonos_devices = SonosDiscovery()

speakers = {SoCo(ip).player_name: SoCo(ip) for ip in sonos_devices.get_speaker_ips()}

# As far as I can tell player_name == get_speaker_info()['zone_name]    
for name,speaker in speakers.items():
    a = speaker.get_current_track_info()['artist']
    #print "player_name: {}; ip: {}; zone name: {}; artist: {}".format(name, speaker.speaker_ip, speaker.get_speaker_info()['zone_name'], a)
    print "player_name: {}; ip: {}; artist: {}".format(name, speaker.speaker_ip, a)
    
    # using the presence of an artist to decide that is the master speaker - seems to work
    if a:
        master = speaker  


print "\nmaster speaker = {}: {}".format(master.player_name,master.speaker_ip)

master_uid = master.get_speaker_info()['uid']
print "master_uid = {}\n".format(master_uid)

for speaker in speakers.values():
    if speaker != master:
        speaker.join(master_uid)

def play_uri(uri, name):
    try:
        master.play_uri(uri)
        # for some reason and I don't think I'd seen this before but thi sis ungrouping the master from the rest of the speakers
        #for speaker in speakers.values():
        #    if speaker != master:
        #        speaker.join(master_uid)
    except:
        #print traceback.format_exc()
        print "had a problem switching to {}!".format(name)
    else:
        print "switched to {}".format(name)

stations = [
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

for i,s in enumerate(stations):
    print "{:d} - {}".format(i+1,s[0])

tolerance = 0       # prevent volume from being too sensitive - right now being taken care of on the arduino

def main():
    n = 0               # counter in while loop
    last_read = 0       # this keeps track of the last potentiometer value

    while True:
        arduino_serial = ser.readline()
        #print "arduino_serial=",arduino_serial
        if arduino_serial:
            if arduino_serial[0] == 'b':
                button = int(arduino_serial[1:])
                print "button pushed = {}".format(button)
                if 0 < button < 13:
                    n = button-1
                    play_uri(stations[n][1], stations[n][0]) 
                        
            elif arduino_serial[0] == 'v':
                volume = int(arduino_serial[1:])
                if abs(volume - last_read) > tolerance:
         
                    set_volume = int(round(volume / 10.24))         # convert (0-1024) trimpot read into 0-100 volume level

                    if set_volume > 75:
                        set_volume = 75
                        print "volume set to over 75 was reset to 75"
                    
                    for s in speakers.values():
                        s.volume = set_volume
                        
                    print "volume = {}%".format(set_volume)
                            
                    last_read = volume
       
        sleep(.1)

try:
    main()
except KeyboardInterrupt:
    print "Keyboard Interrupt"
