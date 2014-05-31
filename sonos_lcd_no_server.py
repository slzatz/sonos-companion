#@+leo-ver=5-thin
#@+node:slzatz.20140531060812.1710: * @file /home/slzatz/sonos-companion/sonos_lcd_no_server.py
#@@language python
#@@tabwidth -4
#@+others
#@+node:slzatz.20140105160722.1552: ** imports etc
from soco import SoCo
from soco import SonosDiscovery

from time import sleep
from Adafruit_LCD_Plate.Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
import random

# use master speaker code that is used in buttons_vkey.py
sonos_devices = SonosDiscovery()
speakers = {SoCo(ip).player_name: SoCo(ip) for ip in sonos_devices.get_speaker_ips()}

# As far as I can tell player_name == get_speaker_info()['zone_name]    
for name,speaker in speakers.items():
    a = speaker.get_current_track_info()['artist']
    print "player_name: {}; ip: {}; artist: {}".format(name, speaker.speaker_ip, a)
    
    # using the presence of an artist to decide that is the master speaker - seems to work
    if a:
        master = speaker
        break
else:
    master = speakers.values()[0]

print 'sonos master speaker = {}: {}'.format(master.player_name, master.speaker_ip)
master_uid = master.get_speaker_info()['uid']


lcd = Adafruit_CharLCDPlate()

# Clear display and show greeting, pause 1 sec
lcd.clear()
lcd.message("Sonos-companion")

# backlight colors
col = (lcd.RED , lcd.YELLOW, lcd.GREEN, lcd.TEAL, lcd.BLUE, lcd.VIOLET, lcd.ON, lcd.OFF)

# Poll buttons, display message & set backlight accordingly

#@+node:slzatz.20140421213753.2449: ** stations
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

#for i,s in enumerate(stations):
    #print "{:d} - {}".format(i+1,s[0])

#@+node:slzatz.20140421213753.2448: ** play_uri
def play_uri(uri, name):
    try:
        master.play_uri(uri)
    except:
        print "had a problem switching to {}!".format(name)
    else:
        print "switched to {}".format(name)
#@+node:slzatz.20140120090653.1358: ** Sonos controls
#@+node:slzatz.20140105160722.1554: *3* play_pause
def play_pause():
    
    z = master.get_current_transport_info()
    if z['current_transport_state'] == 'PLAYING':   #'PAUSED_PLAYBACK'
        master.pause()
    else:
        master.play()

    


#@+node:slzatz.20140105160722.1556: *3* next
def next():
    master.next()


#@+node:slzatz.20140105160722.1557: *3* previous
def previous():
    
    #try:
    #     master.previous()
    #except:
    #    lcd.clear()
    #    lcd.message("Previous\nNot Available")
    #   lcd.backlight(lcd.RED)
    mode = 0
    lcd.clear()
    lcd.backlight(lcd.YELLOW)
    lcd.message(stations[station_index][0])
    


#@+node:slzatz.20140531105648.1725: *3* dec_volume
def dec_volume():
    
    volume = master.volume
    
    new_volume = volume - 10
    
    if new_volume > 75:
        new_volume = 75
        print "volume set to over 75 was reset to 75"
                    
    for s in speakers.values():
        s.volume = new_volume
    

    lcd.clear()
    lcd.message("Volume: {}".format(new_volume))
    lcd.backlight(lcd.YELLOW)
    
    
#@+node:slzatz.20140420093643.2447: *3* inc_volume
def inc_volume():
    
    volume = master.volume
    
    new_volume = volume + 10
    
    if new_volume > 75:
        new_volume = 75
        print "volume set to over 75 was reset to 75"
                    
    for s in speakers.values():
        s.volume = new_volume
        
    lcd.clear()
    lcd.message("Volume: {}".format(new_volume))
    lcd.backlight(lcd.YELLOW)
    

    
    
#@+node:slzatz.20140419192833.2446: ** buttons
def show_button(button):
    print "button: {}".format(button)
    
    #note that using 12 right now to gracefully disconnect cc3000 from WiFi
    if 0 < button < 13:
        n = button-1
        play_uri(stations[n][1], stations[n][0]) 
    
    return "button: {}".format(button)
    

#@+node:slzatz.20140531105648.1726: ** station list
#@+node:slzatz.20140531105648.1727: *3* scroll_up
def scroll_up():
    station_index+=1
    station_index = station_index if station_index < 12 else 0
    
    lcd.clear()
    lcd.backlight(lcd.YELLOW)
    lcd.message(stations[station_index][0])

#@+node:slzatz.20140531105648.1728: *3* scroll_down
def scroll_down():
       
    station_index-=1
    station_index = station_index if station_index > -1 else 0
    
    lcd.clear()
    lcd.backlight(lcd.YELLOW)
    lcd.message(stations[station_index][0])
    
#@+node:slzatz.20140531105648.1729: *3* select
def select():
    
    global mode
    
    if mode:
        mode = 0
        sleep(2)
    else:
        play_uri(stations[station_index][1], stations[station_index][0])
        mode = 1
        sleep(2)
        
#@+node:slzatz.20140510101301.2452: ** list_stations
def list_stations():
    z = ""
    for i,s in enumerate(stations):
        print "{:d} - {}".format(i+1,s[0])
        z+= "{:d} - {}<br>".format(i+1,s[0])
        
    return z
    
    
        
    
    
    
    
#@+node:slzatz.20140131181451.1211: ** main
btn = ((lcd.LEFT  , 'Play/Pause'              , lcd.RED, play_pause), #previous
       (lcd.UP    , 'Increase\nVolume'     , lcd.BLUE, inc_volume, scroll_up),
       (lcd.DOWN  , 'Decrease\nVolume'    , lcd.GREEN, dec_volume ,scroll_down),
       (lcd.RIGHT , 'Next',               lcd.VIOLET, next),
       (lcd.SELECT, 'Change Mode'   , lcd.YELLOW, select, select))

mode = 1
station_index = 0

if __name__ == '__main__':
    
    prev_title = ""
    
    while 1:
        
        track = master.get_current_track_info()
        
        title = track['title']
        
        if prev_title != title:
        
            lcd.clear()
            lcd.backlight(col[random.randrange(0,6)])
            lcd.message(title + '\n' + track['artist'])
            
            prev_title = title
            
        
        if mode:
            for b in btn:
                if lcd.buttonPressed(b[0]):
                    lcd.clear()
                    lcd.message(b[1])
                    lcd.backlight(b[2])
                        
                    b[3]()
                        
                    break
        else:
            for b in btn:
                if lcd.buttonPressed(b[0]):
                    
                    b[4]()
                        
                    break
            
        
        sleep(0.5)
#@-others


#@-leo
