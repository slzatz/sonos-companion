import os
import argparse
from time import sleep
import datetime
import random
import xml.etree.ElementTree as ET
import threading
import sys
import textwrap
from Adafruit_LCD_Plate.Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
import dropbox
import requests
from lcdscroll import Scroller
import config as c
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home,'SoCo')] + [os.path.join(home, 'pydub')] + sys.path
import soco
from soco import config
from pydub import AudioSegment
from amazon_music_db import *

config.CACHE_ENABLED = False

user_id = c.user_id
client = dropbox.client.DropboxClient(c.dropbox_code)

parser = argparse.ArgumentParser(description="Command line options ...")
parser.add_argument('player', default='all', help="This is the name of the player you want to control or all")
args = parser.parse_args()

uri = "x-rincon-mp3radio://translate.google.com/translate_tts?tl=en&q={}"

n = 0
while 1:
    n+=1
    print "attempt "+str(n)
    try:
        speakers = list(soco.discover())
    except TypeError:
        sleep(1)
    else:
        break

print speakers 

# appears that the property coordinator of s.group is not getting set properly and so can't use s.group.coordinator[.player_name]

for s in speakers:
    if s:
        #print "speaker: {} - master: {}".format(s.player_name, s.group)  #s.group.coordinator.player_name)
        print s.player_name
           
if args.player.lower() == 'all':

    for s in speakers:
        if s.is_coordinator:
            master = s
            print "\nNOTE: found coordinator and master =",master.player_name
            break
    else:
        master = speakers[0]
        print "\nALERT: id not find coordinator so took speaker[0] =",master.player_name

    for s in speakers:
        if s != master:
            s.join(master)
else:

    for s in speakers:
        if s:
            #print "speaker: {} - master: {}".format(s.player_name, s.group)  #s.group.coordinator.player_name)
            print s.player_name
            if s.player_name.lower() == args.player.lower():
                master = s
                print "The single master speaker is: ", master.player_name
                break
    else:
        print "Could not find the specified speaker"
        sys.exit()

print "\nprogram running ..."

lcd = Adafruit_CharLCDPlate()

lcd.clear()
lcd.message("Sonos-companion")

# backlight colors
col = (lcd.RED , lcd.YELLOW, lcd.GREEN, lcd.TEAL, lcd.BLUE, lcd.VIOLET, lcd.ON, lcd.OFF)

stations = [
#('WNYC', 'aac://204.93.192.135:80/wnycfm-tunein.aac'),
('WNYC-FM', 'x-sonosapi-stream:s21606?sid=254&flags=32', 'SA_RINCON65031_'), # this is from favorites
#('WSHU-FM', 'x-rincon-mp3radio://wshu.streamguys.org/wshu-news'),
('WSHU-FM', 'x-sonosapi-stream:s22803?sid=254&flags=32', 'SA_RINCON65031_'), # this is from favorites
('QuickMix', 'pndrradio:52877953807377986', 'SA_RINCON3_slzatz@gmail.com'),
('R.E.M. Radio', 'pndrradio:637630342339192386', 'SA_RINCON3_slzatz@gmail.com'), 
('Nick Drake Radio', 'pndrradio:409866109213435458', 'SA_RINCON3_slzatz@gmail.com'),
('Dar Williams Radio', 'pndrradio:1823409579416053314', 'SA_RINCON3_slzatz@gmail.com'),
('Patty Griffin Radio', 'pndrradio:52876609482614338', 'SA_RINCON3_slzatz@gmail.com'),
('Lucinda Williams Radio', 'pndrradio:360878777387148866', 'SA_RINCON3_slzatz@gmail.com'),
('Neil Young Radio', 'pndrradio:52876154216080962', 'SA_RINCON3_slzatz@gmail.com'),
('Kris Delmhorst Radio', 'pndrradio:610111769614181954', 'SA_RINCON3_slzatz@gmail.com'),
('Counting Crows Radio', 'pndrradio:1727297518525703746', 'SA_RINCON3_slzatz@gmail.com'), 
('Vienna Teng Radio', 'pndrradio:138764603804051010', 'SA_RINCON3_slzatz@gmail.com'),
('Random Amazon', 'amazon')]

#media_info = soco.avTransport.GetMediaInfo([('InstanceID', 0)])
#media_uri = media_info['CurrentURI']
#media_meta = media_info['CurrentURIMetaData']

meta_format_pandora = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="OOOX52876609482614338" parentID="0" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

meta_format_radio = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="-1" parentID="-1" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItem.audioBroadcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

def display_song_info():
        
    media_info = master.avTransport.GetMediaInfo([('InstanceID', 0)])
    meta = media_info['CurrentURIMetaData']
    if meta:
        root = ET.fromstring(meta)
        service = root[0][0].text
    else:
        service = ""
    
    message = '{}\n{} {}'.format(title.encode('ascii', 'ignore'), track['artist'].encode('ascii', 'ignore'), service.encode('ascii', 'ignore'))

    lcd.clear()
    lcd.backlight(col[random.randrange(0,6)])
    lcd.message(message)
    
    scroller.setLines(message)

def display_weather():
    
    # Tuesday :  Showers and thunderstorms. Lows overnight in the low 70s.
    # Tuesday Night :  Thunderstorms likely. Low 72F. Winds SSW at 5 to 10 mph. Chance of rain 90%.
            
    r = requests.get("http://api.wunderground.com/api/9862edd5de2d456c/forecast/q/10011.json")
    m1 = r.json()['forecast']['txt_forecast']['forecastday'][0]['title'] + ': ' + r.json()['forecast']['txt_forecast']['forecastday'][0]['fcttext']
    m2 = r.json()['forecast']['txt_forecast']['forecastday'][1]['title'] + ': ' + r.json()['forecast']['txt_forecast']['forecastday'][1]['fcttext']
    
    lcd.clear()
    lcd.backlight(lcd.RED)
    lcd.message([m1,m2])

    scroller.setLines([m1, m2])
            
    return textwrap.wrap(m1+m2,99)

def text2mp3(text, file_):
    tts_uri = "http://translate.google.com/translate_tts?tl=en&q={}"
    with open(file_, 'wb') as handle:
        for line in text:
            print line
            response = requests.get(tts_uri.format(line), stream=True)

            if not response.ok:
                sys.exit()

            for block in response.iter_content(1024):
                if not block:
                    break

                handle.write(block)

    output = AudioSegment.from_mp3(file_) #documentation suggests can use a file-like object
    return output

def play_uri(uri, meta, title):

    try:
        master.play_uri(uri, meta)
    except:
        print "Had the following problem: {} switching to {}!".format(sys.exc_info()[0], title)
    else:
        print "switched to {}".format(title)

def my_add_to_queue(uri, metadata):
    response = master.avTransport.AddURIToQueue([
            ('InstanceID', 0),
            ('EnqueuedURI', uri),
            ('EnqueuedURIMetaData', metadata),
            ('DesiredFirstTrackNumberEnqueued', 0),
            ('EnqueueAsNext', 1)
            ])
    qnumber = response['FirstTrackNumberEnqueued']
    return int(qnumber)

def play_pause():
    
    state = master.get_current_transport_info()['current_transport_state']
    if state == 'PLAYING':   #'PAUSED_PLAYBACK'
        master.pause()
    else:
        master.play()
        
    lcd.clear()
    lcd.backlight(lcd.YELLOW)
    lcd.message(state)

def cancel():
    global mode
    mode = 1

def forward():
    #master.next()
    
    #state = master.get_current_transport_info()['current_transport_state']
    #print "state = ",state
    #if state != 'PLAYING':
        
    meta = meta_format_radio.format(title='google', service='SA_RINCON65031_')

    text = display_weather()
    text.insert(0, datetime.datetime.today().strftime("%A %B %d"))
    print text
    for line in text:
        print line
        master.play_uri(uri.format(line), meta)
        sleep(.1)
        played = False
        while 1:
            state = master.get_current_transport_info()['current_transport_state']
            print "state = ", state
            if state == 'PLAYING':
                played = True
            elif played == False:
                continue 
            else:
                break
            sleep(.2)
    master.stop()

def forward2():

    for s in speakers:
        s.volume = 25

    meta = meta_format_radio.format(title='google', service='SA_RINCON65031_')

    s0 = text2mp3(["Good Morning, Steve"], 'good_morning.mp3')
    weather = display_weather()
    s1 = text2mp3(weather, 'weather.mp3')
    s2 = s0 + s1

    # there appears to be a problem saving as an mp3 on raspi pi
    s2.export('greeting.wav', format='wav')

    #this is the absolute key and involves taking the file created on the local machine and writing it to dropbox
    f = open('greeting.wav', 'rb')
    response = client.put_file('/Public/greeting.wav', f, overwrite=True) # the problem may be FFmpeg or avconv -- pydub can use either

    z = client.media("/Public/greeting.wav")
    public_streaming_url = z['url']
    print "public_streaming_url =", public_streaming_url
    master.play_uri(public_streaming_url,'')
    sleep(.1)
    played = False
    while 1:
        state = master.get_current_transport_info()['current_transport_state']
        if state == 'PLAYING':
            played = True
        elif played == False:
            continue 
        else:
            break
        sleep(.2)

    #sleep(15)

    station = stations[0]
    uri = station[1]
    uri = uri.replace('&', '&amp;') # need to escape '&' in radio URIs
    meta = meta_format_radio.format(title=station[0], service=station[2])
    play_uri(uri, meta, station[0]) # station[0] is the title of the station

def dec_volume():
    
    volume = master.volume
    
    new_volume = volume - 10
    
    if new_volume > 75:
        new_volume = 75
        print "volume set to over 75 was reset to 75"
                    
    if args.player == 'all':
        for s in speakers:
            s.volume = new_volume
    else:
        master.volume = new_volume

    lcd.clear()
    lcd.message("Volume: {}".format(new_volume))
    lcd.backlight(lcd.YELLOW)
    
def inc_volume():
    
    volume = master.volume
    
    new_volume = volume + 10
    
    if new_volume > 75:
        new_volume = 75
        print "volume set to over 75 was reset to 75"
                    
    if args.player == 'all':
        for s in speakers:
            s.volume = new_volume
    else:
        master.volume = new_volume
        
    lcd.clear()
    lcd.message("Volume: {}".format(new_volume))
    lcd.backlight(lcd.YELLOW)
    
def scroll_up():
    global station_index
    max = len(stations) 
    station_index+=1
    station_index = station_index if station_index < max else 0
    
    lcd.clear()
    lcd.backlight(lcd.YELLOW)
    lcd.message(stations[station_index][0])

def scroll_down():
    global station_index
    
    station_index-=1
    station_index = station_index if station_index > -1 else 0
    
    lcd.clear()
    lcd.backlight(lcd.YELLOW)
    lcd.message(stations[station_index][0])
    
def change_mode():
    global mode 
    mode = 0

def select():
    global mode

    station = stations[station_index]
    uri = station[1]
    
    if uri.startswith('pndrradio'):
        meta = meta_format_pandora.format(title=station[0], service=station[2])
        play_uri(uri, meta, station[0]) # station[0] is the title of the station
    elif uri.startswith('x-sonosapi-stream'):
        uri = uri.replace('&', '&amp;') # need to escape '&' in radio URIs
        meta = meta_format_radio.format(title=station[0], service=station[2])
        play_uri(uri, meta, station[0]) # station[0] is the title of the station
    elif uri.startswith('amazon'):
        master.stop()
        master.clear_queue()

        rows = session.query(Song).count()

        for n in range(10):
            r = random.randrange(0,rows-1)
            song = session.query(Song).get(r)
            print song.id
            print song.artist
            print song.album
            print song.title
            print song.uri
            i = song.uri.find('amz')
            ii = song.uri.find('.')
            id_ = song.uri[i:ii]
            print id_
            meta = didl_amazon.format(id_=id_)
            my_add_to_queue('', meta)
            print "---------------------------------------------------------------"
            
        master.play_from_queue(0)

    #display_song_info() ##### trying to make this happen faster - for some reason did not work
    print "uri=",uri
    print "meta=",meta
    print "\n"
        
    mode = 1

def list_stations():
    z = ""
    for i,s in enumerate(stations):
        print "{:d} - {}".format(i+1,s[0])
        z+= "{:d} - {}<br>".format(i+1,s[0])
        
    return z

def thread_scroller():

    while 1:
        if scroll:
            message = scroller.scroll()
            lcd.clear()
            lcd.message(message)
        sleep(.5)

#2 = forward: lcd.RIGHT
#4 = volume lower: lcd.DOWN
#8 = volume higher: lcd.UP
#16 = pause: lcd.LEFT
#1 = change mode: lcd.SELECT
#0 = no button

btns = {
           1: ( lcd.SELECT,   'Choose Station',           lcd.YELLOW, change_mode,         select),
           2: ( lcd.RIGHT,    'Next',                         lcd.VIOLET,    forward2, cancel),
           4: ( lcd.DOWN,    'Decrease\nVolume',    lcd.GREEN,    dec_volume, scroll_down),
           8: ( lcd.UP,       'Increase\nVolume',        lcd.BLUE,       inc_volume,  scroll_up),
          16: ( lcd.LEFT,    'Play/Pause',                 lcd.RED,        play_pause,  cancel)
         } 

if __name__ == '__main__':
    
    #globals that are modified by functions and declared as global
    mode = 1
    scroll = True
    station_index = 0
    ###############
    
    scroll = True
    prev_title = '0'
    prev_hour = -1
    scroller = Scroller()
    scroller.setLines("Hello Steve")
    t = threading.Thread(target=thread_scroller)
    t.daemon = True # quits when main thread is terminated
    t.start()

    while 1:

        try:
            b = btns.get(lcd.buttons())

            if b:
                scroll = False
                if mode:
                    lcd.clear()
                    lcd.backlight(b[2])
                    b[3]()
                    lcd.message('\n'+b[1]) #\n puts the text on the lcd's second line
                    prev_title = ""
                    sleep(2)
                    if mode: # may look odd but the functions called [b[3]()] can change mode
                        scroll = True
                else:
                    b[4]()
                    sleep(0.2) # debounce
                    if mode:
                        scroll = True

                continue

            else:

                if mode:
                            
                    state = master.get_current_transport_info()['current_transport_state']
                    if state != 'PLAYING':
                        
                        hour = datetime.datetime.now().hour
                        if hour != prev_hour:
                            
                            display_weather()
                            prev_hour = hour
                                                
                    else:
                        track = master.get_current_track_info()
                        title = track['title']
                        if prev_title != title:
                            scroll = False      
                            display_song_info()
                            prev_title = title
                            sleep(1) 
                            scroll = True
                            
                sleep(0.1)
                #end if mode and not b:

        except KeyboardInterrupt:
            raise
        except:
            print "Experienced exception during while loop: ", sys.exc_info()[0]

