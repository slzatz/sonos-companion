#@+leo-ver=5-thin
#@+node:slzatz.20140603064654.2793: * @file C:/home/slzatz/sonos-companion/sonos_lcd_no_server2.py
#@@language python
#@@tabwidth -4
#@+others
#@+node:slzatz.20140603064654.2794: ** imports etc
import soco
from soco.services import zone_group_state_shared_cache

from time import sleep

from Adafruit_LCD_Plate.Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
import random

speakers = list(soco.discover())

for s in speakers:
    print "speaker: {} - master: {}".format(s.player_name, s.group.coordinator.player_name)
           
for s in speakers:
    if s.is_coordinator:
        master = s
        break
else:
    master = speakers[0]
    
for s in speakers:
    if s != master:
        s.join(master)
    
print "\n"
for s in speakers:
    print "speaker: {} - master: {}".format(s.player_name, s.group.coordinator.player_name)

lcd = Adafruit_CharLCDPlate()

lcd.clear()
lcd.message("Sonos-companion")

# backlight colors
col = (lcd.RED , lcd.YELLOW, lcd.GREEN, lcd.TEAL, lcd.BLUE, lcd.VIOLET, lcd.ON, lcd.OFF)

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

#2 = forward: lcd.RIGHT
#4 = volume lower: lcd.DOWN
#8 = volume higher: lcd.UP
#16 = pause: lcd.LEFT
#1 = change mode: lcd.SELECT
#0 = no button

btns = {
           1: ( lcd.SELECT,   'Change Mode',           lcd.YELLOW,  select,         select),
           2: ( lcd.RIGHT,    'Next',                         lcd.VIOLET,    next),
           4: ( lcd.DOWN,    'Decrease\nVolume',    lcd.GREEN,    dec_volume, scroll_down),
           8: ( lcd.UP,       'Increase\nVolume',        lcd.BLUE,       inc_volume,  scroll_up),
          16: ( lcd.LEFT,    'Play/Pause',                 lcd.RED,        play_pause,  cancel)
         } 
         
#         btns = {
#           0: {1:no_button, 0:pass},
#           1: {1:select, 0:select},
#           2: {1:next, 0:pass},
#           4: {1:dec_volume, 0:scroll_down},
#           8: {1:inc_volume, 0:scroll_up},
#          16: {1:play_pause, 0:cancel}
#         } 

#btns.get(lcd.buttons())[mode]()
 
mode = 1
station_index = 0

#@+node:slzatz.20140709142803.2452: ** display_song_info (future use)
def display_song_info():

    state = master.get_current_transport_info()['current_transport_state']
    if state != 'PLAYING':
        lcd.clear()
        lcd.backlight(lcd.YELLOW)
        lcd.message(state)
        sleep(0.2)
        return
    
    track = master.get_current_track_info()
    
    title = track['title']
    
    if prev_title != title:
    
        lcd.clear()
        lcd.backlight(col[random.randrange(0,6)])
        lcd.message(title + '\n' + track['artist'])
        
        prev_title = title
        
    else:                              ############################### 7/9
        lcd.scrollDisplayLeft()   ################################ 7/9
        
    sleep(0.2)
#@+node:slzatz.20140603064654.2795: ** play_uri
def play_uri(uri, name):
    try:
        master.play_uri(uri)
    except:
        print "had a problem switching to {}!".format(name)
    else:
        print "switched to {}".format(name)

#@+node:slzatz.20140603064654.2796: ** play_pause
def play_pause():
    
    z = master.get_current_transport_info()
    if z['current_transport_state'] == 'PLAYING':   #'PAUSED_PLAYBACK'
        master.pause()
    else:
        master.play()

#@+node:slzatz.20140622201640.2450: ** cancel
def cancel():
    
    global mode
    
    mode = 1
    
    

#@+node:slzatz.20140603064654.2797: ** next
def next():
    master.next()

#@+node:slzatz.20140603064654.2798: ** previous (not in use)
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
    
#@+node:slzatz.20140603064654.2799: ** dec_volume
def dec_volume():
    
    volume = master.volume
    
    new_volume = volume - 10
    
    if new_volume > 75:
        new_volume = 75
        print "volume set to over 75 was reset to 75"
                    
    for s in speakers:
        s.volume = new_volume
    

    lcd.clear()
    lcd.message("Volume: {}".format(new_volume))
    lcd.backlight(lcd.YELLOW)
    
#@+node:slzatz.20140603064654.2800: ** inc_volume
def inc_volume():
    
    volume = master.volume
    
    new_volume = volume + 10
    
    if new_volume > 75:
        new_volume = 75
        print "volume set to over 75 was reset to 75"
                    
    for s in speakers:
        s.volume = new_volume
        
    lcd.clear()
    lcd.message("Volume: {}".format(new_volume))
    lcd.backlight(lcd.YELLOW)
    
#@+node:slzatz.20140603064654.2802: ** scroll_up
def scroll_up():
    
    global station_index
    
    station_index+=1
    station_index = station_index if station_index < 12 else 0
    
    lcd.clear()
    lcd.backlight(lcd.YELLOW)
    lcd.message(stations[station_index][0])

#@+node:slzatz.20140603064654.2803: ** scroll_down
def scroll_down():
       
    global station_index
    
    station_index-=1
    station_index = station_index if station_index > -1 else 0
    
    lcd.clear()
    lcd.backlight(lcd.YELLOW)
    lcd.message(stations[station_index][0])
    
#@+node:slzatz.20140603064654.2804: ** select
def select():
    
    global mode
    
    if mode:
        mode = 0
        sleep(.5)
    else:
        play_uri(stations[station_index][1], stations[station_index][0])
        mode = 1
        sleep(.5)
        
#@+node:slzatz.20140603064654.2805: ** list_stations (not in use)
def list_stations():
    z = ""
    for i,s in enumerate(stations):
        print "{:d} - {}".format(i+1,s[0])
        z+= "{:d} - {}<br>".format(i+1,s[0])
        
    return z
    
#@+node:slzatz.20140709142803.2451: ** if __name__ == '__main__':
if __name__ == '__main__':
    
    prev_title = ""
    
    while 1:

        b = btns.get(lcd.buttons())

        if  mode and not b:
                        
            state = master.get_current_transport_info()['current_transport_state']
            if state != 'PLAYING':
                lcd.clear()
                lcd.backlight(lcd.YELLOW)
                lcd.message(state)
                sleep(0.2)
                continue
            
            track = master.get_current_track_info()
            
            title = track['title']
            
            if prev_title != title:
            
                lcd.clear()
                lcd.backlight(col[random.randrange(0,6)])
                lcd.message(title + '\n' + track['artist'])
                
                prev_title = title
                
            else:                              ############################### 7/9
                lcd.scrollDisplayLeft() ################################ 7/9
                
            sleep(0.2)
            continue
        #end if mode and not b:
        
        if mode:
            lcd.clear()
            lcd.message(b[1])
            lcd.backlight(b[2])
            b[3]()
            prev_title = ""
            sleep(0.2)
            
        else:

            b[4]()
            sleep(0.2)

#@-others

#@-leo
