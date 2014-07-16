#@+leo-ver=5-thin
#@+node:slzatz.20140603064654.2793: * @file C:/home/slzatz/sonos-companion/sonos_lcd_no_server2.py
#@@language python
#@@tabwidth -4
#@+others
#@+node:slzatz.20140603064654.2794: ** imports etc
import soco
from soco.services import zone_group_state_shared_cache

from time import sleep
import datetime
import random

from Adafruit_LCD_Plate.Adafruit_CharLCDPlate import Adafruit_CharLCDPlate

import requests
from lcdscroll import Scroller

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

#globals
mode = 1
station_index = 0

#@+node:slzatz.20140709142803.2452: ** display_song_info (future use)
def display_song_info():

    track = master.get_current_track_info()
    
    title = track['title']
    if g.prev_title != title:
    
        lcd.clear()
        lcd.backlight(col[random.randrange(0,6)])
        lcd.message([title, track['artist']])
        
        scroller = Scroller(lines = [title, track['artist']])
        prev_title = title
        
        sleep(.8) # have it linger when song changes before it starts scrolling
        
    else: 
        
        message = scroller.scroll()
        lcd.clear()
        lcd.message(message)
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
    
    state = master.get_current_transport_info()['current_transport_state']
    if state == 'PLAYING':   #'PAUSED_PLAYBACK'
        master.pause()
    else:
        master.play()
        
    lcd.clear()
    lcd.backlight(lcd.YELLOW)
    lcd.message(state)

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
    
#@+node:slzatz.20140712195238.2453: ** display_weather
def display_weather():
    
    hour = datetime.datetime.now().hour
    if hour != g.prev_hour:
        
        r = requests.get("http://api.wunderground.com/api/9862edd5de2d456c/conditions/q/10011.json")
        m1 = r.json()['current_observation']['temperature_string']
        m2 = r.json()['current_observation']['wind_string']
        
        lcd.clear()
        lcd.backlight(lcd.RED)
        lcd.message([m1,m2])
 
        scroller = Scroller(lines = [m1, m2])
        
        g.prev_hour = hour
    
    else:
         
        message = scroller.scroll()
        lcd.clear()
        lcd.backlight(lcd.RED)
        lcd.message(message)
         
#@+node:slzatz.20140710210012.2452: ** btns
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
#@+node:slzatz.20140709142803.2451: ** if __name__ == '__main__':
if __name__ == '__main__':
    
    prev_title = '0'
    prev_hour = -1
    
    while 1:

        b = btns.get(lcd.buttons())
    
        if  mode and not b:
                        
            state = master.get_current_transport_info()['current_transport_state']
            
            if state != 'PLAYING':
                #lcd.clear()
                #lcd.backlight(lcd.YELLOW)
                #lcd.message(state)
                
                #begin display_weather() ########################################
                hour = datetime.datetime.now().hour
                if hour != prev_hour:
                    
                    #r = requests.get("http://api.wunderground.com/api/9862edd5de2d456c/forecast/q/10011.json")
                    #>>> for x in r.json()['forecast']['txt_forecast']['forecastday']:
                    #print x['title'],': ',x['fcttext'],'\n'

                    # Tuesday :  Showers and thunderstorms. Lows overnight in the low 70s.
                    # Tuesday Night :  Thunderstorms likely. Low 72F. Winds SSW at 5 to 10 mph. Chance of rain 90%.
                    # Wednesday :  Mostly cloudy with rain ending in the afternoon. High 81F. Winds NW at 5 to 10 mph. Chance of rain 80%. Rainfall around a quarter of an inch.
                    # Wednesday Night :  Mostly cloudy skies early, then partly cloudy after midnight. Low 66F. Winds light and variable.
                    # Thursday :  Partly cloudy. High 82F. Winds NW at 5 to 10 mph.
                    # Thursday Night :  Mainly clear. Low around 65F. Winds NW at 5 to 10 mph.
                    # Friday :  Intervals of clouds and sunshine. High 82F. Winds NNE at 5 to 10 mph.
                    # Friday Night :  Partly cloudy. Low 68F. Winds S at 5 to 10 mph.
                    
                    #r = requests.get("http://api.wunderground.com/api/9862edd5de2d456c/conditions/q/10011.json")
                    #m1 = r.json()['current_observation']['temperature_string']
                    #m2 = r.json()['current_observation']['wind_string']
                    
                    r = requests.get("http://api.wunderground.com/api/9862edd5de2d456c/forecast/q/10011.json")
                    m1 = r.json()['forecast']['txt_forecast']['forecastday'][0]['title'],': ',r.json()['forecast']['txt_forecast']['forecastday'][0]['fcttext']
                    m2 = r.json()['forecast']['txt_forecast']['forecastday'][1]['title'],': ',r.json()['forecast']['txt_forecast']['forecastday'][1]['fcttext']

                    
                    lcd.clear()
                    lcd.backlight(lcd.RED)
                    lcd.message([m1,m2])
             
                    weather_scroller = Scroller(lines = [m1, m2])
                    
                    prev_hour = hour
                
                else:
                     
                    message = weather_scroller.scroll()
                    lcd.clear()
                    lcd.backlight(lcd.RED)
                    lcd.message(message)
                
               #end display_weather()
                
            else:
               #begin display_song_info() ###########################################
                track = master.get_current_track_info()
                
                title = track['title']
                
                if prev_title != title:
                
                    lcd.clear()
                    lcd.backlight(col[random.randrange(0,6)])
                    
                    message = title + '\n' + track['artist']
                    lcd.message(message)
                    
                    prev_title = title
                    
                    track_scroller = Scroller(lines = message)
                    
                    sleep(.8)
                    
                else: 
                    
                    message = track_scroller.scroll()
                    lcd.clear()
                    lcd.message(message)
                
                #end display_song_info() ##########################################
                    
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
            continue
            
        if b: #if mode would have been caught by above
    
            b[4]()
            sleep(0.2)
       
    ###################################################
    # below works - different approach to scrolling
    
    # prev_title = ""
    
    # while 1:

        # b = btns.get(lcd.buttons())

        # if  mode and not b:
                        
            # state = master.get_current_transport_info()['current_transport_state']
            # if state != 'PLAYING':
                # lcd.clear()
                # lcd.backlight(lcd.YELLOW)
                # lcd.message(state)
                # sleep(0.2)
                # continue
            
            # track = master.get_current_track_info()
            
            # title = track['title']
            
            # if prev_title != title:
            
                # lcd.clear()
                # lcd.backlight(col[random.randrange(0,6)])
                # lcd.message(title + '\n' + track['artist'])
                
                # prev_title = title
                # n=0
                # length = len(title) if len(title) > len(track['artist']) else len(track['artist'])
                # delta = length - 16
                
                # sleep(1)
                
            # else: 
                # if delta <= 0: #if delta0 <= 0 m0shift = m0
                    # pass      
                # elif n <= delta:                     
                    # lcd.scrollDisplayLeft() #m0shift = m0[n0:] m1shift = m1[n1:]
                    # n+=1
                # else:
                    # lcd.clear()
                    # lcd.message(title + '\n' + track['artist'])
                    # n = 0
                    # sleep(1)
                    
            # sleep(0.2)
            # continue
        # #end if mode and not b:
        
        # if mode: 
            # lcd.clear()
            # lcd.message(b[1])
            # lcd.backlight(b[2])
            # b[3]()
            # prev_title = ""
            # sleep(0.2)
            # continue
            
        # if b: #if mode would have been caught by above

            # b[4]()
            # sleep(0.2)

#@-others

#@-leo
