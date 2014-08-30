import soco
from soco import config

import platform
import os

import pygame
#from pygame.locals import *
import txtlib # may still use this for weather, lyrics, bio

import time

from time import sleep
import datetime
import random
import xml.etree.ElementTree as ET
import requests
import textwrap
import json
from collections import OrderedDict
from functools import partial
import argparse
import sys
from operator import itemgetter
import lxml.html
#from PIL import Image
from StringIO import StringIO

import wand.image

if platform.machine() == 'armv6l':
    #from pitftgpio import PiTFT_GPIO
    #pitft = PiTFT_GPIO()
    import RPi.GPIO as GPIO
    PINS = [23,22,27,18] #pins 1 through 4
    GPIO.setmode(GPIO.BCM)
    for pin in PINS:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# google custom search api
from apiclient import discovery

# needed by the google custom search engine module apiclient
import httplib2

#using the musicbrainz db to find the release date and album (if a compilation)
import musicbrainzngs

parser = argparse.ArgumentParser(description='Command line options ...')

# for all of the following: if the command line option is not present then the value is True and startup is normal
parser.add_argument('-a', '--alternate', action='store_true', help="Alternate images and text") #default is opposite of action
args = parser.parse_args()

#if args.alternate ...

musicbrainzngs.set_useragent("Sonos", "0.1", contact="slzatz")

try:
  with open('artists.json', 'r') as f:
      artists = json.load(f)
except IOError:
      artists = {}

DISPLAY = OrderedDict([('artist','Artist'), ('album','Album'), ('title','Song'), ('date','Date'), ('service','Service')])
# need to add ('service', 'Service) to ordered dict

#last.fm - right now not using this at all - suspect it is providing bios
base_url = "http://ws.audioscrobbler.com/2.0/"
api_key = "1c55c0a239072889fa7c11df73ecd566"

wrapper = textwrap.TextWrapper(width=50, replace_whitespace=False) # may be able to be a little longer than 40

prev_track = ""

if platform.machine() == 'armv6l':
    # from https://github.com/adafruit/adafruit-pi-cam/blob/master/cam.py
    os.putenv('SDL_VIDEODRIVER', 'fbcon')
    os.putenv('SDL_FBDEV', '/dev/fb1')
elif platform.system() == 'Windows':
    os.environ['SDL_VIDEODRIVER'] = 'windib'
elif platform.system() == "Linux":
    os.putenv('SDL_VIDEODRIVER', 'x11')
else:
    sys.exit("Currently unsupported hardware/OS")


pygame.init()
pygame.mouse.set_visible(0)

screen = pygame.display.set_mode((320, 240))
screen.fill((0,0,0))

#img = wand.image.Image(filename = "test.bmp") #########
#img.transform(resize = '320x240^')#############
#img.save(filename = "test.bmp")
img = pygame.image.load("test.bmp").convert() ################

text = txtlib.Text((320, 240), 'freesans')
text.text = "Sonos-Companion TFT Edition"
text.update()
screen.blit(text.area, (0,0))
pygame.display.flip()
sleep(5)

font = pygame.font.SysFont('Sans', 20)
text = font.render("Welcome to Sonos-Companion", True, (255, 0, 0))
img.blit(text, (0,25)) 
screen.blit(img, (0,0))
pygame.display.flip()

config.CACHE_ENABLED = False

#speakers = list(soco.discover())
n = 0
while 1:
    n+=1
    print "attempt "+str(n)
    speakers = soco.discover()
    try:
        speakers = list(soco.discover())
    except TypeError:    
        sleep(1)       
    else:
        break 
    
print speakers ################

# appears that the property coordinator of s.group is not getting set properly and so can't use s.group.coordinator[.player_name]

for s in speakers:
    if s:
        #print "speaker: {} - master: {}".format(s.player_name, s.group)  #s.group.coordinator.player_name)
        print s.player_name
           
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
    
print "\n"
#for s in speakers:
#if s:  print "speaker: {} - master: {}".format(s.player_name, s.group.coordinator)

print "program running ..."

# backlight colors
#col = (lcd.RED , lcd.YELLOW, lcd.GREEN, lcd.TEAL, lcd.BLUE, lcd.VIOLET, lcd.ON, lcd.OFF)

#colors
colors = {
'red': (0,0,0),
'yellow': (0,0,0),
'green': (0,0,0),
'teal': (0,0,0),
'blue': (0,0,0),
'violet': (0,0,0),
}

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
('Vienna Teng Radio', 'pndrradio:138764603804051010', 'SA_RINCON3_slzatz@gmail.com')]

#globals
mode = 1
station_index = 0

meta_format_pandora = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="OOOX52876609482614338" parentID="0" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

meta_format_radio = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns=
"urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="-1" parentID="-1" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItem.audioBroadcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

def button_press(pin, b=0):
    global mode
    print "mode = ",mode
    print "Pressed GPIO: "+str(pin)+" = button: "+str(b)

    #font = pygame.font.SysFont('Sans', 16)
    #zzz = pygame.Surface((320,20)) 
    #zzz.fill((0,0,0))

    if b == 4:
        inc_volume()
        #print "increase volume"
        #text = font.render("Increase Volume", True, (255, 0, 0))
    elif b==3:
        dec_volume()
        #print "decrease volume"
        #text = font.render("Decrease Volume", True, (255, 0, 0))
    elif b==2:
        play_pause()
        #print "play_pause"
        #text = font.render("Play-Pause", True, (255, 0, 0))
    else:
        if mode:
            print "must have tried to change mode"
            url = get_url(artist, title)
            lyrics = get_lyrics(url)
            show_lyrics(lyrics)
            mode = 0
        else:
            mode = 1
        
        return

    #screen.blit(zzz, (0,220))                 
    #screen.blit(text, (0,220)) 
    #pygame.display.flip()
    
if platform.machine() == 'armv6l':
    #pitft.Button4Interrupt(callback=partial(button_press, b=4)) #18
    #pitft.Button3Interrupt(callback=partial(button_press, b=3)) #21
    #pitft.Button2Interrupt(callback=partial(button_press, b=2)) #22
    #pitft.Button1Interrupt(callback=partial(button_press, b=1)) #23
    GPIO.add_event_detect(18, GPIO.FALLING, callback=partial(button_press, b=4), bouncetime=300) 
    GPIO.add_event_detect(27, GPIO.FALLING, callback=partial(button_press, b=3), bouncetime=300) 
    GPIO.add_event_detect(22, GPIO.FALLING, callback=partial(button_press, b=2), bouncetime=300) 
    GPIO.add_event_detect(23, GPIO.FALLING, callback=partial(button_press, b=1), bouncetime=300)

def display_song_info(i):

    url = artist_image_list[i]['link']

    try:
        response = requests.get(url)
    except Exception as detail:
        print "response = requests.get(url) generated exception:", detail
        
    try:
        img = wand.image.Image(file=StringIO(response.content))
    except Exception as detail:
        img = wand.image.Image(filename = "test.bmp")
        print "img = wand.image.Image(file=StringIO(response.content)) generated exception:", detail

    img.transform(resize = '320x240^')
    img = img.convert('bmp')
    img.save(filename = "test1.bmp")
    img = pygame.image.load("test1.bmp").convert()
    img.set_alpha(75) # the lower the number the more faded - 75 seems too faded; try 100

    font = pygame.font.SysFont('Sans', 16)
    font.set_bold(True)
    
    text1 = font.render("Artist: "+track.get('artist'), True, (255, 0, 0))
    text2 = font.render("Album: "+track.get('album'), True, (255, 0, 0))
    text3 = font.render("Song: "+track.get('title'), True, (255, 0, 0))
    text4 = font.render("Release date: "+track.get('date'), True, (255, 0, 0))
    
    screen.fill((0,0,0)) ################################################## added this to alpha
    screen.blit(img, (0,0))      
    screen.blit(text1, (0,0))
    screen.blit(text2, (0,18))
    screen.blit(text3, (0,36))
    screen.blit(text4, (0,54))

    pygame.display.flip()
    
    os.remove("test1.bmp")
 
def display_song_info2(i):

    url = artist_image_list[i]['link']

    try:
        response = requests.get(url)
    except Exception as detail:
        print "response = requests.get(url) generated exception:", detail
        
    try:
        img = wand.image.Image(file=StringIO(response.content))
    except Exception as detail:
        img = wand.image.Image(filename = "test.bmp")
        print "img = wand.image.Image(file=StringIO(response.content)) generated exception:", detail

    img.transform(resize = '320x240^')
    img = img.convert('bmp')
    img.save(filename = "test1.bmp")
    img = pygame.image.load("test1.bmp").convert()
    #img.set_alpha(100) # the lower the number the more faded - 75 seems too faded; now not fading for display_images
    
    screen.fill((0,0,0)) 
    screen.blit(img, (0,0))      


    pygame.display.flip()
    
    os.remove("test1.bmp") 

def display_initial_song_info():

    url = artist_image_list[0]['link']
    
    try:
        response = requests.get(url)
    except Exception as detail:
        print "response = requests.get(url) generated exception:", detail
        
    try:
        img = wand.image.Image(file=StringIO(response.content))
    except Exception as detail:
        img = wand.image.Image(filename = "test.bmp")
        print "img = wand.image.Image(file=StringIO(response.content)) generated exception:", detail
    
    img.transform(resize = '320x240^')
    img = img.convert('bmp')
                    
    #f = StringIO() ###################### couldn't get these three lines to work hence why I am saving to disk
    #img.save(file = f) ####################
    #img = pygame.image.load(f, "z.bmp")
                    
    img.save(filename = "test1.bmp") #couldn't get it to save to StringIO object obviating need to save to disk
    img = pygame.image.load("test1.bmp").convert()
    #img.set_alpha(100) # the lower the number the more faded - 75 seems too faded; try 100
                    
    sub_img = img.subsurface((0,0,320,80))    #rect: (x1, y1, width, height)
    sub_img.set_alpha(100)
    zzz = pygame.Surface((320,80)) 
    zzz.fill((0,0,0))

    font = pygame.font.SysFont('Sans', 16)
    font.set_bold(True)
        
    text1 = font.render("Artist: "+track.get('artist'), True, (255, 0, 0))
    text2 = font.render("Album: "+track.get('album'), True, (255, 0, 0))
    text3 = font.render("Song: "+track.get('title'), True, (255, 0, 0))
    text4 = font.render("Release date: "+track.get('date'), True, (255, 0, 0))
    
    screen.fill((0,0,0)) 
    screen.blit(img, (0,0))
    screen.blit(zzz, (0,0))
    screen.blit(sub_img, (0,0))                    
    screen.blit(text1, (0,0)) 
    screen.blit(text2, (0,18)) 
    screen.blit(text3, (0,36)) 
    screen.blit(text4, (0,54)) 

    pygame.display.flip()
        
    os.remove("test1.bmp")
        
def get_release_date(artist, album, title):

    print "artist = {}; album = {} [not used in search], title = {} [in get_release_date]".format(artist, album, title)
    
    ## commented this out because I think in most circumstances where there is a legit album, there is an accompanying date
    ## (like for a ripped CD, a Rhapsody song, Pandora
    
    # try:
        # result = musicbrainzngs.search_releases(artist=artist, release=album, limit=20, strict=True)
    # except:
        # return "No date exception (search_releases)"
    
    # #release_list = result['release-list'] # can be missing
    
    # if 'release-list' in result:
            # release_list = result['release-list'] # can be missing
            # dates = [d['date'][0:4] for d in release_list if 'date' in d and int(d['ext:score']) > 90] 
    
            # if dates:
                # dates.sort()
                # return dates[0]  
        
    ### Generally if there was no date provided it's because there is also a bogus album (because it's a collection
    ### and so decided to comment out the above.  We'll see how that works over time.
    try:
        result = musicbrainzngs.search_recordings(artist=artist, recording=title, limit=20, offset=None, strict=False)
    except:
        return "No date exception (search_recordings)"
    
    recording_list = result.get('recording-list')
    
    if recording_list is None:
        return "No date (search of musicbrainzngs did not produce a recording_list)"
    
    dates = []
    for d in recording_list:
    #  if 'release-list' in d:
        if int(d['ext:score']) > 90 and 'release-list' in d:
            rel_dict = d['release-list'][0] # it's a list but seems to have one element and that's a dictionary
            date = rel_dict.get('date', '9999')[0:4]
            title = rel_dict.get('title','No title')
            if rel_dict.get('artist-credit-phrase') == 'Various Artists':  #possibly could also use status:promotion
                dates.append((date,title,'z'))
            else:
                dates.append((date,title,'a'))
                
                #dd = [x['date'][0:4] for x in d['release-list'] if 'date' in x and int(d['ext:score']) > 90]
                #dd = [(x['date'][0:4],x['title']) for x in d['release-list'] if 'date' in x and int(d['ext:score']) > 90]

                #dates.extend(dd)
            
    if dates:
        dates.sort(key=itemgetter(0,2)) # idea is to put albums by the artist ahead of albums by various artists
        return "{} - {}".format(dates[0][0], dates[0][1])   
    else:
        return "?" 
    
def play_uri(uri, meta, title):
    try:
        master.play_uri(uri, meta)
    except:
        print "had a problem switching to {}!".format(title)
    else:
        print "switched to {}".format(title)

def play_pause():
    
    state = master.get_current_transport_info()['current_transport_state']
    if state == 'PLAYING':   #'PAUSED_PLAYBACK'
        master.pause()
    else:
        master.play()

    display_action("Play-Pause")

def cancel():
    
    global mode
    
    mode = 1

def next():
    master.next()

def previous():
    
    mode = 0
    #lcd.clear()
    #lcd.backlight(lcd.YELLOW)
    #lcd.message(stations[station_index][0])
    
def dec_volume():
    
    volume = master.volume
    
    new_volume = volume - 10
    
    if new_volume > 75:
        new_volume = 75
        print "volume set to over 75 was reset to 75"
                    
    for s in speakers:
        s.volume = new_volume
   
    display_action("Decrease Volume")
    
def inc_volume():
    
    volume = master.volume
    
    new_volume = volume + 10
    
    if new_volume > 75:
        new_volume = 75
        print "volume set to over 75 was reset to 75"
                    
    for s in speakers:
        s.volume = new_volume

    display_action("Increase Volume")
        
def display_action(text):
    
    font = pygame.font.SysFont('Sans', 14)
    zzz = pygame.Surface((320,20)) 
    zzz.fill((0,0,0))
    text = font.render(text, True, (255, 0, 0))
    screen.blit(zzz, (0,224))                 
    screen.blit(text, (0,224)) 
    pygame.display.flip()

def scroll_up():
    
    global station_index
    
    station_index+=1
    station_index = station_index if station_index < 12 else 0
    
    #lcd.clear()
    #lcd.backlight(lcd.YELLOW)
    #lcd.message(stations[station_index][0])

def scroll_down():
       
    global station_index
    
    station_index-=1
    station_index = station_index if station_index > -1 else 0
    
    #lcd.clear()
    #lcd.backlight(lcd.YELLOW)
    #lcd.message(stations[station_index][0])
    
def select():
    
    global mode
    
    if mode:
        mode = 0
        sleep(.5)
    else:
        station = stations[station_index]
        uri = station[1]
        
        if uri.startswith("pndrradio"):
            meta = meta_format_pandora.format(title=station[0], service=station[2])
        else:
            uri = uri.replace('&', '&amp;') # need to escape '&' in radio URIs
            meta = meta_format_radio.format(title=station[0], service=station[2])
        
        print "uri=",uri
        print "meta=",meta
        print "\n"
  
        play_uri(uri, meta, station[0]) # station[0] is the title of the station
            
        mode = 1
        sleep(.5)
        
def list_stations():
    z = ""
    for i,s in enumerate(stations):
        print "{:d} - {}".format(i+1,s[0])
        z+= "{:d} - {}<br>".format(i+1,s[0])
        
    return z
    
def get_images(artist):
    '''
    10 is the max you can bring back on any individual search
    I think you  separate the orterms by a space
    orTerms='picture photo image'
    imgSize = 'large'
    start=1 or 11
    using link, height, width
    '''

    if artist not in artists: 
        http = httplib2.Http()
        service = discovery.build('customsearch', 'v1',  developerKey='AIzaSyCe7pbOm0sxYXwMWoMJMmWvqBcvaTftRC0', http=http)
        z = service.cse().list(q=artist, searchType='image', imgSize='large', num=10, cx='007924195092800608279:0o2y8a3v-kw').execute() 

        print 'artist=',artist    #################################################
        image_list = []

        for x in z['items']:
            y = {}
            y['image'] = {k:x['image'][k] for k in ['height','width']}
            y['link'] = x['link']
            image_list.append(y)
      
        artists[artist] = image_list

        print "**************Google Custom Search Engine Request for "+artist+"**************"
          
        try:
            with open('artists.json', 'w') as f:
                json.dump(artists, f)
        except IOError:
            print "Could not write 'artists' json file"

    return artists[artist]
    
def get_url(artist, title):
    payload = {'func': 'getSong', 'artist': artist, 'song': title, 'fmt': 'realjson'}
    
    try:
         r = requests.get("http://lyrics.wikia.com/api.php", params=payload)
    except:
        url = None
         
    else:        
        q = r.json()
        
        url = q['url'] if 'url' in q else None
        
        if url and url.find("action=edit") != -1: 
            url = None 
            
    if url is not None:
        return url
            
    try:
        z = musicbrainzngs.search_recordings(artist=artist, recording=title, limit=5, offset=None, strict=False)
    except:
        return None
        
    for d in z['recording-list']:

         if int(d['ext:score'])==100:
             new_artist = d['artist-credit-phrase']
             new_title = d['title']
    
    payload = {'func': 'getSong', 'artist': new_artist, 'song': new_title, 'fmt': 'realjson'}
    
    try:
         r = requests.get("http://lyrics.wikia.com/api.php", params=payload)
    except:
        return None
                
    q = r.json()
        
    url = q['url'] if 'url' in q else None
        
    if url and url.find("action=edit") != -1: 
        url = None 
    else:
        print "got song lyrics by using musicbrainz db to figure out correct artist and title"
        
    return url
    
def get_lyrics(url):

    if not url:
        return "Can't find lyrics - url couldn't be found or had 'edit'  "
    
    try:
        doc = lxml.html.parse(url)
    except IOError:
        return "Can't find lyrics - couldn't parse url - may be a cover"

    try:
        lyricbox = doc.getroot().cssselect(".lyricbox")[0]        
    except IndexError:
        return "Can't find lyrics - couldn't find lyrics in page"

    # look for a sign that it's instrumental
    if len(doc.getroot().cssselect(".lyricbox a[title=\"Instrumental\"]")):
        return "No lyrics - appears to be instrumental"

    # prepare output
    lyrics = []
    if lyricbox.text is not None:
        lyrics.append(lyricbox.text)
    for node in lyricbox:
        if str(node.tag).lower() == "br":
            lyrics.append("\n")
        if node.tail is not None:
            lyrics.append(node.tail)
    return "".join(lyrics).strip()
    
def show_lyrics(lyrics):
    
    screen.fill((0,0,0))
    text = txtlib.Text((320, 240), 'freesans', font_size=10)
    text.text = lyrics
    text.update()
    screen.blit(text.area, (0,0))
    pygame.display.flip()
    
def display_weather():
    
    # Tuesday :  Showers and thunderstorms. Lows overnight in the low 70s.
    # Tuesday Night :  Thunderstorms likely. Low 72F. Winds SSW at 5 to 10 mph. Chance of rain 90%.
    
    r = requests.get("http://api.wunderground.com/api/9862edd5de2d456c/forecast/q/10011.json")
    m1 = r.json()['forecast']['txt_forecast']['forecastday'][0]['title'] + ': ' + r.json()['forecast']['txt_forecast']['forecastday'][0]['fcttext']
    m2 = r.json()['forecast']['txt_forecast']['forecastday'][1]['title'] + ': ' + r.json()['forecast']['txt_forecast']['forecastday'][1]['fcttext']
 
    text = txtlib.Text((320, 240), 'freesans')
    text.text = wrapper.fill(m1)+'\n'+wrapper.fill(m2)
    text.update()
    screen.blit(text.area, (0, 0))
    pygame.display.flip() # Update the full display Surface to the screen


#2 = forward: lcd.RIGHT
#4 = volume lower: lcd.DOWN
#8 = volume higher: lcd.UP
#16 = pause: lcd.LEFT
#1 = change mode: lcd.SELECT
#0 = no button

#btns = {
#           1: ( 'select', 'Change Mode',           lcd.YELLOW,  select,         select),
#           2: ( lcd.RIGHT,    'Next',                         lcd.VIOLET,    next),
#           4: ( lcd.DOWN,    'Decrease\nVolume',    lcd.GREEN,    dec_volume, scroll_down),
#           8: ( lcd.UP,       'Increase\nVolume',        lcd.BLUE,       inc_volume,  scroll_up),
#          16: ( lcd.LEFT,    'Play/Pause',                 lcd.RED,        play_pause,  cancel)
#         } 
    

if __name__ == '__main__':
    
    prev_title = -1 #this is zero so if the inital song title is the empty string, it's not equal
    prev_hour = -1
    #new_song = False
    tt = z = time.time()
       
    while 1:
        
       # pygame.event.get() # necessary to keep pygame window from going to sleep

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    sys.exit()
                elif event.key == pygame.K_p:
                    play_pause()
                elif event.key == pygame.K_k:
                    inc_volume()
                elif event.key == pygame.K_j:
                    dec_volume()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                print "mousedown"
                play_pause()
                    
        if  mode:
                        
            state = master.get_current_transport_info()['current_transport_state']
            
            if state != 'PLAYING':
                
                hour = datetime.datetime.now().hour
                if hour != prev_hour:

                    display_weather()
                    
                    prev_hour = hour
                    prev_title = ''
                
            else:
            
                if time.time() - tt > 2:

                    #get_current_track_info() =  {
                                #u'album': 'We Walked In Song', 
                                #u'artist': 'The Innocence Mission', 
                                #u'title': 'My Sisters Return From Ireland', 
                                #u'uri': 'pndrradio-http://audio-sv5-t3-1.pandora.com/access/5459257820921908950?version=4&lid=86206018&token=...', 
                                #u'playlist_position': '3', 
                                #u'duration': '0:02:45', 
                                #u'position': '0:02:38', 
                                #u'album_art': 'http://cont-ch1-2.pandora.com/images/public/amz/3/2/9/3/655037093923_500W_500H.jpg'}

                    
                    current_track = master.get_current_track_info()
                    title = current_track['title']
                    artist = current_track['artist'] # for lyrics           
                    tt = time.time()
                    
                    print str(tt), "checking to see if track has changed"
                    
                    if prev_title != title:
                        
                        track = dict(current_track)
                        # there will be no date if from one of our compilations
                        if not 'date' in track and track.get('artist') and track.get('title'):
                            track['date'] = get_release_date(track['artist'], track['album'], track['title'])
                        else:
                            track['date'] = ''
                        
                        media_info = master.avTransport.GetMediaInfo([('InstanceID', 0)])
                        #media_uri = media_info['CurrentURI']
                        meta = media_info['CurrentURIMetaData']
                        if meta:
                            root = ET.fromstring(meta)
                            service = root[0][0].text
                            track['service'] = service
                        
                        #track_strings = [DISPLAY[x]+': '+track[x] for x in DISPLAY if x in track] 
                        track_strings = [DISPLAY[x]+': '+track[x] for x in DISPLAY if track.get(x)] 
                        print "track_strings = ",track_strings
                        print "artist = {artist}, album = {album}, title = {title}, release date = {date}".format(**track)
                    
                        z = time.time()
                        
                                          
                        prev_title = title
                        i = 0
                        new_song = True
                        
                        #if there is no artist (for example when Sonos isn't playing anything or for some radio) then show images of sunsets  ;-)
                        artist_image_list = get_images(track['artist'] if track.get('artist') else "sunsets")
                        
                        print "displaying initial image of ", track.get('artist', '')
                        #display_initial_song_info()
                        display_song_info(0)

                    elif not new_song:
                        # show the next track_string if not the image and text from a new song
                            
                        if not track_strings:
                            track_strings.extend([DISPLAY[x]+': '+track[x] for x in DISPLAY if track.get(x)])
                                 
                        line = track_strings.pop(0)

                        font = pygame.font.SysFont('Sans', 14)
                        font.set_bold(True)
                        
                        text = font.render(line, True, (255,0,0))
                        zzz = pygame.Surface((320,20)) 
                        zzz.fill((0,0,0))
                        
                        screen.blit(zzz, (0,224))
                        screen.blit(text, (0,224))
                        pygame.display.flip()
                        
                else:
                
                    if time.time() - z > 10:
                        
                        new_song = False
                        
                        i = i+1 if i < 9 else 0
                        
                        print "displaying a new image of ", track['artist']
                        display_song_info2(i) #################
                        
                        z = time.time()
            
        sleep(0.1)

       


