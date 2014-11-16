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
from StringIO import StringIO

import wand.image
import config as c
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home,'SoCo')] + sys.path
import soco
from soco import config

import pygbutton_lite as pygbutton

if platform.machine() == 'armv6l':
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

from amazon_music_db import *

parser = argparse.ArgumentParser(description='Command line options ...')

g_api_key = c.google_api_key

# for all of the following: if the command line option is not present then the value is True and startup is normal
parser.add_argument('-d', '--display', action='store_true', help="Use raspberry pi HDMI display and not LCD") #default is opposite of action
args = parser.parse_args()

#if args.display ...

musicbrainzngs.set_useragent("Sonos", "0.1", contact="slzatz")

try:
  with open('artists.json', 'r') as f:
      artists = json.load(f)
except IOError:
      artists = {}

DISPLAY = OrderedDict([('artist','Artist'), ('album','Album'), ('title','Song'), ('date','Date'), ('service','Service'), ('scrobble','Scrobble'), ('uri','Uri')])

#last.fm - using for scrobble information, can also be used for artist bios 
base_url = "http://ws.audioscrobbler.com/2.0/"
api_key = c.last_fm_api_key 

wrapper = textwrap.TextWrapper(width=42, replace_whitespace=False) # may be able to be a little longer than 40

prev_track = ""

if platform.machine() == 'armv6l' and not args.display:
    os.putenv('SDL_VIDEODRIVER', 'fbcon')
    os.putenv('SDL_FBDEV', '/dev/fb1')
    os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')
    os.putenv('SDL_MOUSEDRV', 'TSLIB')
elif platform.system() == 'Windows':
    os.environ['SDL_VIDEODRIVER'] = 'windib'
elif platform.system() == "Linux":
    os.putenv('SDL_VIDEODRIVER', 'x11')
else:
    sys.exit("Currently unsupported hardware/OS")

pygame.init()

if platform.machine() == 'armv6l':
    pygame.mouse.set_visible(False)

w, h = pygame.display.Info().current_w, pygame.display.Info().current_h
if w > 640:
    w,h = 640,640
screen = pygame.display.set_mode((w, h))

screen.fill((0,0,0))

# need a backup image that should be renamed backup
#img = wand.image.Image(filename = "test.bmp") #########
#img.transform(resize = '320x240^')#############
#img.save(filename = "test.bmp")
img = pygame.image.load("test.bmp").convert() ################

text = txtlib.Text((w, h), 'freesans')
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
           
for s in speakers:
    if s.is_coordinator:
        master = s
        print "\nNOTE: found coordinator and master =", master.player_name
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

    if b == 4:
        inc_volume()

    elif b == 3:
        dec_volume()

    elif b == 2:
        play_pause()

    else:
        play_random_amazon()

        #if mode:
        #    url = get_url(artist, title)
        #    lyrics = get_lyrics(url)
        #    show_lyrics(lyrics)
        #    mode = 0
        #else:
        #    mode = 1
        
if platform.machine() == 'armv6l':
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

    #img.transform(resize = '320x240^')
    img.transform(resize = str(h)+'x'+str(w)+'^')
    img = img.convert('bmp')
    img.save(filename = "test1.bmp")
    img = pygame.image.load("test1.bmp").convert()
    img.set_alpha(75) # the lower the number the more faded - 75 seems too faded; try 100

    font = pygame.font.SysFont('Sans', 16)
    font.set_bold(True)
    
    screen.fill((0,0,0))
    screen.blit(img, (0,0))      
    n=0
    for a,b in DISPLAY.items():
        text = font.render(u"{}: {}".format(b, track.get(a)), True, (255, 0, 0))
        screen.blit(text, (5,n))
        n+=18
    pygame.display.flip()

    os.remove("test1.bmp")
 
def display_song_info2(i):

    url = artist_image_list[i]['link']

    try:
        response = requests.get(url)
    except Exception as e:
        print "response = requests.get(url) generated exception: ", e
        img = wand.image.Image(filename = "test.bmp")
    else:

        try:
            img = wand.image.Image(file=StringIO(response.content))
        except Exception as e:
            img = wand.image.Image(filename = "test.bmp")
            print "img = wand.image.Image(file=StringIO(response.content)) generated exception: ", e

    try:
       # img.transform(resize = '320x240^')
        img.transform(resize = str(h)+'x'+str(w)+'^')
        img = img.convert('bmp')
        img.save(filename = "test1.bmp")
        img = pygame.image.load("test1.bmp").convert()
        #img.set_alpha(100) # the lower the number the more faded - 75 seems too faded; now not fading for display_images
        
        screen.fill((0,0,0)) 
        screen.blit(img, (0,0))      

        pygame.display.flip()
        
        os.remove("test1.bmp") 

    except Exception as e:
        print "Problem with img: ", e

def get_scrobble_info(artist, track, username='slzatz', autocorrect=True):
    
    payload = {'method':'track.getinfo', 'artist':artist, 'track':track, 'autocorrect':autocorrect, 'format':'json', 'api_key':api_key, 'username':username}
    
    try:
        r = requests.get(base_url, params=payload)
        
        z = r.json()['track']['userplaycount']
        zz = r.json()['track']['userloved']
        return "playcount: "+z+" loved: "+zz

    except Exception as e:
        print "Exception in get_artist_info: ", e
        return ''

def get_release_date(artist, album, title):

    try:
        #print "artist = {}; album = {} [not used in search], title = {} [in get_release_date]".format(artist, album, title)
        t = "artist = {}; album = {} [not used in search], title = {} [in get_release_date]".format(artist, album, title)
        print t.encode('ascii', 'ignore')
    except UnicodeEncodeError as e: # should just be .encode('ascii', 'ignore')
        print "Unicode Error", e

    ## commented this out because I think in most circumstances where there is a legit album, there is an accompanying date
    ## (like for a ripped CD, a Rhapsody song, Pandora
    ## In addition, this allows you to display the first album where the song appeared 
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
        result = musicbrainzngs.search_recordings(artist=artist, recording=title, limit=40, offset=None, strict=False)
    except:
        return "No date exception (search_recordings)"
    
    recording_list = result.get('recording-list')
    
    if recording_list is None:
        return "No date (search of musicbrainzngs did not produce a recording_list)"
    
    dates = []
    for d in recording_list:
        if int(d['ext:score']) > 98 and 'release-list' in d:
            rel_dict = d['release-list'][0] # it's a list but seems to have one element and that's a dictionary
            date = rel_dict.get('date', '9999')[0:4]
            title = rel_dict.get('title','No title')

            if rel_dict.get('artist-credit-phrase') == 'Various Artists':  #possibly could also use status:promotion
                dates.append((date,title,'z'))
            else:
                dates.append((date,title,'a'))
                
    if dates:
        dates.sort(key=itemgetter(0,2)) # idea is to put albums by the artist ahead of albums by various artists
        return u"{} - {}".format(dates[0][0], dates[0][1])   
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

#def next():
#    master.next()

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
        
def play_random_amazon():
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

def display_action(text):
    
    font = pygame.font.SysFont('Sans', 14)
    zzz = pygame.Surface((w,20)) 
    zzz.fill((0,0,0))
    text = font.render(text, True, (255, 0, 0))
    screen.blit(zzz, (0,h-16))                 
    screen.blit(text, (0,h-16)) 
    pygame.display.flip()

def scroll_up(): # not in use
    
    global station_index
    
    station_index+=1
    station_index = station_index if station_index < 12 else 0
    
    #lcd.clear()
    #lcd.backlight(lcd.YELLOW)
    #lcd.message(stations[station_index][0])

def scroll_down():# not in use
       
    global station_index
    
    station_index-=1
    station_index = station_index if station_index > -1 else 0
    
    #lcd.clear()
    #lcd.backlight(lcd.YELLOW)
    #lcd.message(stations[station_index][0])
    
def select______():# not in use
    
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
        
def list_stations():# not in use
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
        service = discovery.build('customsearch', 'v1',  developerKey=g_api_key, http=http)
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

    if artist is None or title is None:
        return None

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
    
def get_lyrics():

    global mode
    mode = 0
    
    if artist is None or title is None:
         return "No artist or title"

    print artist, title
    
    url = get_url(artist, title)
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

    text = txtlib.Text((w, h), 'freesans', font_size=18)
    text.text = "".join(lyrics).strip()
    text.update()

    screen.fill((0,0,0))
    screen.blit(text.area, (0,0))
    pygame.display.flip()

def show_lyrics(lyrics): #not in use
    
    screen.fill((0,0,0))
    text = txtlib.Text((w, h), 'freesans', font_size=18)
    text.text = lyrics
    text.update()
    screen.blit(text.area, (0,0))
    pygame.display.flip()
    
def display_weather():
    
    # Tuesday :  Showers and thunderstorms. Lows overnight in the low 70s.
    # Tuesday Night :  Thunderstorms likely. Low 72F. Winds SSW at 5 to 10 mph. Chance of rain 90%.
    
    try:
        r = requests.get("http://api.wunderground.com/api/9862edd5de2d456c/forecast/q/10011.json")
        m1 = r.json()['forecast']['txt_forecast']['forecastday'][0]['title'] + ': ' + r.json()['forecast']['txt_forecast']['forecastday'][0]['fcttext']
        m2 = r.json()['forecast']['txt_forecast']['forecastday'][1]['title'] + ': ' + r.json()['forecast']['txt_forecast']['forecastday'][1]['fcttext']
    except requests.exceptions.ConnectionError as e:
        print "ConnectionError in request in display_weather: ", e
    else:
        text = txtlib.Text((320, 240), 'freesans')
        text.text = wrapper.fill(m1)+'\n'+wrapper.fill(m2)
        text.update()
        screen.blit(text.area, (0, 0))
        pygame.display.flip() # Update the full display Surface to the screen

def hide_buttons():
    global mode
    sleep(1)
    mode = 1
    

def select(station=None):
    global mode

    #station = stations[station_index]
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

def show_screen_buttons():
    font = pygame.font.SysFont('Sans', 20)
    font.set_bold(True)
    w1 = (w/2) - 15
    b0 = pygbutton.PygButton((10,10,w1,30), 'Lyrics', action=get_lyrics, redraw=False)
    b1 = pygbutton.PygButton((10,60,w1,30), 'Play-Pause', action=play_pause)
    b2 = pygbutton.PygButton((10,110,w1,30), 'Increase Volume', action=inc_volume)
    b3 = pygbutton.PygButton((10,160,w1,30), 'Decrease Volume', action=dec_volume)
    b4 = pygbutton.PygButton((10,210,w1,30), 'Hide Buttons', action=hide_buttons)
    w2 = (w/2) + 10
    b5 = pygbutton.PygButton((w2,10,w1,30), 'Weather')
    b6 = pygbutton.PygButton((w2,60,w1,30), 'Random Amazon', action=play_random_amazon)
    b7 = pygbutton.PygButton((w2,110,w1,30), 'Patty Griffin Radio', action=partial(select, station=stations[6]))
    b8 = pygbutton.PygButton((w2,160,w1,30), 'Decrease Volume')
    b9 = pygbutton.PygButton((w2,210,w1,30), 'Hide Buttons')
    screen.fill((100,100,100))
    buttons = (b0, b1, b2, b3, b4, b5, b6, b7, b8, b9) 
    for b in buttons:
        b.draw(screen)

    pygame.display.flip() 
    
    return buttons

if __name__ == '__main__':
    
    prev_title = None  #this is None so if the song title is the empty string, it's not equal
    prev_hour = -1
    ttt = tt = z = time.time()
    new_song = True
    i = 0
    artist = None

    KEYS = {pygame.K_p:play_pause, pygame.K_k:inc_volume, pygame.K_j:dec_volume, pygame.K_a:play_random_amazon}

    while 1:
        
       # pygame.event.get() or .poll() -- necessary to keep pygame window from going to sleep

        event = pygame.event.poll()
        
        if event.type == pygame.NOEVENT:
            pass # want pass and not continue because want this to fall through to the non pygame event stuff
            
        elif event.type == pygame.MOUSEBUTTONDOWN: #=5 - MOUSEMOTION ==4

            if mode==1:
                #pos = pygame.mouse.get_pos()
                buttons = show_screen_buttons()
                mode = 2 # mode = 2 is when the buttons are shown
                #print "mouse position=",pos
                sleep(1)
                
            elif mode==0:
                prev_title = None
                mode = 1 # when mode = 1 images are being flipped

            else:  # mode 2 = the buttons are showing 

                button = next((b for b in buttons if b.pressed(event)),buttons[4])
                button.draw_down(screen)
                button.action()
                button.re_draw(screen)

                #if b1.pressed(event):
                #    b1.draw_down(screen)
                #    if artist:
                #        print "must have tried to change mode"
                #        url = get_url(artist, title)
                #        lyrics = get_lyrics(url)
                #        show_lyrics(lyrics)
                #        mode = 0 # mode = 0 is when lyrics are showing
                #elif b2.pressed(event): 
                #    b2.draw_down(screen)
                #    play_pause()
                #    b2.draw_normal(screen)
                #elif b3.pressed(event): 
                #    b3.draw_down(screen)
                #    inc_volume()
                #    b3.draw_normal(screen)
                #    pygame.display.update(b3.rect)
                #elif b4.pressed(event): 
                #    b4.draw_down(screen)
                #    dec_volume()
                #    b4.draw_normal(screen)
                #else:
                #    b5.pressed(event) # makes sure button is drawn in depressed view if it is pushed
                #    b5.draw_down(screen)
                #    mode = 1
                #    z = 0
                #    tt = time.time() + 2     
                    
            pygame.event.clear()  #trying not to catch stray mousedown events since a little unclear how touch screen generates them
                
        elif event.type == pygame.QUIT:
            sys.exit()
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                GPIO.cleanup()
                sys.exit()

            KEYS.get(event.key, lambda:None)()

        # end of processing pygame events
             
        if  mode!=1:
            if time.time() - ttt > 2:
                print time.time(),"mode=",mode
                ttt = time.time()
            continue

        try:
            state = master.get_current_transport_info()['current_transport_state']
        except (requests.exceptions.ConnectionError, soco.exceptions.SoCoUPnPException) as e:
            state = 'ERROR'
            print "Encountered error in state = master.get_current transport_info(): ", e

        if state != 'PLAYING':
            
            hour = datetime.datetime.now().hour
            if hour != prev_hour:

                display_weather()
                
                prev_hour = hour
                prev_title = ''

            continue
                
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
                
                if not 'scrobble' in track and track.get('artist') and track.get('title'):
                    track['scrobble'] = get_scrobble_info(track['artist'], track['title'])
                else:
                    track['scrobble'] = ''

                try:
                    media_info = master.avTransport.GetMediaInfo([('InstanceID', 0)])
                    #media_uri = media_info['CurrentURI']
                    meta = media_info['CurrentURIMetaData']
                    if meta:
                        root = ET.fromstring(meta)
                        service = root[0][0].text
                        track['service'] = service
                except requests.exceptions.ConnectionError as e:
                    print "Error in media_info: ",e

                track_strings = [DISPLAY[x]+': '+track[x] for x in DISPLAY if track.get(x)] 
            
                z = time.time()
                                  
                prev_title = title
                i = 0
                new_song = True
                
                #if there is no artist (for example when Sonos isn't playing anything or for some radio) then show images of sunsets  ;-)
                artist_image_list = get_images(track['artist'] if track.get('artist') else "sunsets")
                
                print "displaying initial image of ", track.get('artist', '')
                display_song_info(0)
                
            elif not new_song:
                # show the next track_string if not the image and text from a new song
                    
                if not track_strings:
                    track_strings.extend([DISPLAY[x]+': '+track[x] for x in DISPLAY if track.get(x)])
                         
                line = track_strings.pop(0)

                font = pygame.font.SysFont('Sans', 14)
                font.set_bold(True)
                
                text = font.render(line, True, (255,0,0))
                zzz = pygame.Surface((w,20)) 
                zzz.fill((0,0,0))
                 
                screen.blit(zzz, (0,h-16))
                screen.blit(text, (0,h-16))
                pygame.display.flip()
                
        
        if time.time() - z > 10:
            
            new_song = False
            
            i = i+1 if i < 9 else 0
            try:
               #track 
                print "displaying a new image of ", track['artist']
                display_song_info2(i) 
            except NameError as e:
               print "NameError:", e
            #else:
                #print "displaying a new image of ", track['artist']
                #display_song_info2(i) 
            
            z = time.time()
        
        sleep(0.1)

