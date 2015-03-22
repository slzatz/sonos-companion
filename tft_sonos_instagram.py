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
from cStringIO import StringIO
import dropbox
import wand.image
import config as c
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'Soco')] + [os.path.join(home, 'pydub')] + [os.path.join(home, 'twitter')] + sys.path
import soco
from soco import config
from pydub import AudioSegment
from twitter import *
from twitter.api import TwitterHTTPError
import pygbutton_lite as pygbutton

import boto.sqs
from boto.sqs.message import Message


#################instagram
instagram_base_url = "https://api.instagram.com/v1/users/{}/media/recent/"
client_id = "8372f43ffb4b4bbbbd054871d6561668"

#https://api.instagram.com/v1/users/search?q=brahmino&access_token=278917377.8372f43.33d3f65330834b9fa6126d30283b660e
#ids = 4616106 Jason Peterson; 17789355 JR; 986542 Tyson Wheatley; 230625139 Nick Schade; 3399664 Zak Shelhamer; 6156112 Scott Rankin; 1607304 Laura Pritchet; janske 24078; 277810 Richard Koci Hernandez; 1918184 Simone Bramante; 197656340 Michael Christoper Brown; 200147864 David Maialetti; 4769265 eelco roos 

ids = [4616106, 17789355, 986542, 230625139, 3399664, 6156112, 1607304, 24078, 277810, 1918184, 197656340, 200147864, 4769265] 
#################instagram


conn = boto.sqs.connect_to_region(
    "us-east-1",
    aws_access_key_id=c.aws_access_key_id,
    aws_secret_access_key=c.aws_secret_access_key)

sqs_track_queue = conn.get_all_queues()[0]

if platform.machine() == 'armv6l':
    import RPi.GPIO as GPIO
    PINS = [23,22,27,18] #pins 1 through 4
    GPIO.setmode(GPIO.BCM)
    for pin in PINS:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
else:
    GPIO = None

#google custom search api
from apiclient import discovery

# needed by the google custom search engine module apiclient
import httplib2

#using the musicbrainz db to find the release date and album (if a compilation)
import musicbrainzngs

from amazon_music_db import *
#from create_image_db import *

client = dropbox.client.DropboxClient(c.dropbox_code)

parser = argparse.ArgumentParser(description='Command line options ...')

g_api_key = c.google_api_key

# twitter
oauth_token = c.twitter_oauth_token 
oauth_token_secret = c.twitter_oauth_token_secret
CONSUMER_KEY = c.twitter_CONSUMER_KEY
CONSUMER_SECRET = c.twitter_CONSUMER_SECRET
tw = Twitter(auth=OAuth(oauth_token, oauth_token_secret, CONSUMER_KEY, CONSUMER_SECRET))
# for all of the following: if the command line option is not present then the value is True and startup is normal
parser.add_argument('-d', '--display', action='store_true', help="Use raspberry pi HDMI display and not LCD") #default is opposite of action
args = parser.parse_args()

#if args.display ...

musicbrainzngs.set_useragent("Sonos", "0.1", contact="slzatz")

#try:
#  with open('artists.json', 'r') as f:
#      artists = json.load(f)
#except IOError:
#      artists = {}

DISPLAY = OrderedDict([('artist','Artist'), ('album','Album'), ('title','Song'), ('date','Date'), ('service','Service'), ('scrobble','Scrobble'), ('uri','Uri')])
MINI_DISPLAY = OrderedDict([('artist','Artist'), ('album','Album'), ('title','Song')])
#last.fm - using for scrobble information, can also be used for artist bios 
base_url = "http://ws.audioscrobbler.com/2.0/"
api_key = c.last_fm_api_key 

wrapper = textwrap.TextWrapper(width=42, replace_whitespace=False) # may be able to be a little longer than 40
wrapper = textwrap.TextWrapper(width=72, replace_whitespace=False)  #instagram

prev_track = ""

if platform.machine() == 'armv6l' and not args.display:
    os.putenv('SDL_VIDEODRIVER', 'fbcon')
    os.putenv('SDL_FBDEV', '/dev/fb1')
    os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')
    os.putenv('SDL_MOUSEDRV', 'TSLIB')
elif platform.system() == 'Windows':
    os.environ['SDL_VIDEODRIVER'] = 'windib'
elif platform.system() == "Linux":
    os.environ['SDL_VIDEODRIVER'] = 'x11' #note: this works if you launch x (startx) and run terminal requires keyboard/mouse
else:
    sys.exit("Currently unsupported hardware/OS")

r = pygame.init()
print r

if platform.machine() == 'armv6l' and not args.display:
    pygame.mouse.set_visible(False)

w, h = pygame.display.Info().current_w, pygame.display.Info().current_h
if w > 1000:
    w = 1000
if h > 700:
    h = h - 100
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
('WNYC-FM', 'x-sonosapi-stream:s21606?sid=254&flags=32', 'SA_RINCON65031_'), 
('WSHU-FM', 'x-sonosapi-stream:s22803?sid=254&flags=32', 'SA_RINCON65031_'),
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

meta_format_radio = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="-1" parentID="-1" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItem.audioBroadcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

didl_amazon = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="00030020{id_}" parentID="" restricted="true"><dc:title></dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON6663_X_#Svc6663-0-Token</desc></item></DIDL-Lite>'''

def button_press(pin, b=0):
    #global mode
    #print "mode = ",mode
    print "Pressed GPIO: "+str(pin)+" = button: "+str(b)

    if b == 4:
        inc_volume()

    elif b == 3:
        dec_volume()

    elif b == 2:
        play_pause()

    else:
        # this could be anything but right now playing random amazon
        play_random_amazon()

if platform.machine() == 'armv6l':
    GPIO.add_event_detect(18, GPIO.FALLING, callback=partial(button_press, b=4), bouncetime=300) 
    GPIO.add_event_detect(27, GPIO.FALLING, callback=partial(button_press, b=3), bouncetime=300) 
    GPIO.add_event_detect(22, GPIO.FALLING, callback=partial(button_press, b=2), bouncetime=300) 
    GPIO.add_event_detect(23, GPIO.FALLING, callback=partial(button_press, b=1), bouncetime=300)

def display_artist_info(artist):

    artist_image_list = get_images(artist)
    r = random.randint(0,9)
    url = artist_image_list[r].link

    try:
        response = requests.get(url)
    except Exception as e:
        print "response = requests.get(url) generated exception:", e
        img = wand.image.Image(filename = "test.bmp")
        artist_image_list[r].ok = False
        session.commit()
    else:
        try:
            img = wand.image.Image(file=StringIO(response.content))
        except Exception as e:
            print "img = wand.image.Image(file=StringIO(response.content)) generated exception:", e
            img = wand.image.Image(filename = "test.bmp")
            artist_image_list[r].ok = False
            session.commit()

    #img.transform(resize = '320x240^')
    img.transform(resize = str(h)+'x'+str(w)+'^')
    img = img.convert('bmp')
    f = StringIO()
    img.save(f)
    f.seek(0)
    img = pygame.image.load(f, 'bmp').convert()
    f.close()
    img.set_alpha(75) # the lower the number the more faded - 75 seems too faded; try 100

    font = pygame.font.SysFont('Sans', 28)
    font.set_bold(True)
    
    screen.fill((0,0,0))
    screen.blit(img, (0,0))      

    text = font.render(u"{}".format(artist), True, (255, 0, 0))
    screen.blit(text, (5,5))

    bio = get_artist_info(artist, autocorrect=0)
    bio = textwrap.wrap(bio, 70)
    font = pygame.font.SysFont('Sans', 18)
    font.set_bold(False)
    n=40
    for line in bio:
        text = font.render(u"{}".format(line), True, (255, 0, 0))
        screen.blit(text, (5,n))
        n+=18

    pygame.display.flip()

def display_song_info(i):

    url = artist_image_list[i].link

    try:
        response = requests.get(url)
    except Exception as e:
        print "response = requests.get(url) generated exception: ", e
        img = wand.image.Image(filename = "test.bmp")
        artist_image_list[i].ok = False
        session.commit()
    else:     
        try:
            img = wand.image.Image(file=StringIO(response.content))
        except Exception as e:
            img = wand.image.Image(filename = "test.bmp")
            print "img = wand.image.Image(file=StringIO(response.content)) generated exception:", e 
            artist_image_list[i].ok = False
            session.commit()

    #img.transform(resize = '320x240^')
    img.transform(resize = str(h)+'x'+str(w)+'^')
    img = img.convert('bmp')
    f = StringIO()
    img.save(f)
    f.seek(0)
    img = pygame.image.load(f, 'bmp').convert()
    f.close()
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

def display_song_info2(i):

    url = artist_image_list[i].link

    try:
        response = requests.get(url)
    except Exception as e:
        print "response = requests.get(url) generated exception: ", e
        img = wand.image.Image(filename = "test.bmp")
        artist_image_list[i].ok = False
        session.commit()
    else:
        try:
            img = wand.image.Image(file=StringIO(response.content))
        except Exception as e:
            img = wand.image.Image(filename = "test.bmp")
            print "img = wand.image.Image(file=StringIO(response.content)) generated exception: ", e
            artist_image_list[i].ok = False
            session.commit()

    try:
       # img.transform(resize = '320x240^')
        img.transform(resize = str(h)+'x'+str(w)+'^')
        img = img.convert('bmp')
        f = StringIO()
        img.save(f)
        f.seek(0)
        img = pygame.image.load(f, 'bmp').convert()
        f.close()
        #img.set_alpha(100) # the lower the number the more faded - 75 seems too faded; now not fading for display_images
        
        screen.fill((0,0,0)) 
        screen.blit(img, (0,0))      

        pygame.display.flip()
        
    except Exception as e:
        print "Problem with img: ", e

def get_scrobble_info(artist, track, username='slzatz', autocorrect=True):
    
    payload = {'method':'track.getinfo', 'artist':artist, 'track':track, 'autocorrect':autocorrect, 'format':'json', 'api_key':api_key, 'username':username}
    
    try:
        r = requests.get(base_url, params=payload)
        
        z = r.json()['track']['userplaycount']
        zz = r.json()['track']['userloved']
        #return "playcount: "+z+" loved: "+zz
        return z # will need to be converted to integer when sent to SQS
    except Exception as e:
        print "Exception in get_scrobble_info: ", e
        return '-1' # will need to be converted to integer when sent to SQS


def get_artist_info(artist, autocorrect=0):
    
    payload = {'method':'artist.getinfo', 'artist':artist, 'autocorrect':autocorrect, 'format':'json', 'api_key':api_key}
    
    try:
        r = requests.get(base_url, params=payload)
        bio = r.json()['artist']['bio']['summary']
        text = lxml.html.fromstring(bio).text_content()
        idx = text.find("Read more")
        if idx != -1:
            text = text[:idx]
        
        return text
        
    except:
        return ''

def get_release_date(artist, album, title):

    t = "artist = {}; album = {} [used in search], title = {} [in get_release_date]".format(artist, album, title)
    print t.encode('ascii', 'ignore')

    # commented this out because I think in most circumstances where there is a legit album, there is an accompanying date
    # (like for a ripped CD, a Rhapsody song, Pandora
    # In addition, this allows you to display the first album where the song appeared 
    try:
        result = musicbrainzngs.search_releases(artist=artist, release=album, limit=20, strict=True)
    except:
        return "No date exception (search_releases)"
    
    release_list = result['release-list'] # can be missing
    
    if 'release-list' in result:
        release_list = result['release-list'] # can be missing
        dates = [d['date'][0:4] for d in release_list if 'date' in d and int(d['ext:score']) > 90] 
    
        if dates:
            dates.sort()
            return "{}".format(dates[0])  

    return ''
       
    ## Generally if there was no date provided it's because there is also a bogus album (because it's a collection
    ## and so decided to comment out the above.  We'll see how that works over time.

def get_recording_date(artist, album, title):

    t = "artist = {}; album = {} [not used in search], title = {} [in get_recording_date]".format(artist, album, title)
    print t.encode('ascii', 'ignore')
    
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
        return '' 
    
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

def scroll_up():
    global station_index
    max = len(stations) 
    station_index+=1
    station_index = station_index if station_index < max else 0
    artist = stations[station_index][0]
    idx = artist.find('Radio')
    if idx != -1:
        artist = artist[:idx-1]
    display_artist_info(artist)

def scroll_down():
    global station_index
    
    station_index-=1
    station_index = station_index if station_index > -1 else 0
    artist = stations[station_index][0]
    idx = artist.find('Radio')
    if idx != -1:
        artist = artist[:idx-1]
    display_artist_info(artist)

#def next():
#    master.next()

def previous():# not in use
    global mode 
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
        r = random.randrange(1,rows-1)
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

def get_images(name):
    '''
    10 is the max you can bring back on any individual search
    I think you  separate the orterms by a space
    orTerms='picture photo image'
    imgSize = 'large'
    start=1 or 11
    using link, height, width
    '''
    try:
        artist = session.query(Artist).filter(Artist.name==name).one()
    except NoResultFound:
        #artist = None
        artist = Artist(name=name)
        session.add(artist)
        session.commit()
    
    #if artist not in artists: 
        http = httplib2.Http()
        service = discovery.build('customsearch', 'v1',  developerKey=g_api_key, http=http)
        z = service.cse().list(q=artist, searchType='image', imgSize='large', num=10, cx='007924195092800608279:0o2y8a3v-kw').execute() 

        #print 'artist=',artist    #################################################
        #iimage_list = []

        images = []
        for i in z['items']:
            image = Image(link=i['link'], width=i['image']['width'],height=i['image']['height'])
            images.append(image)
            
        artist.images = images
        session.commit()
     #   for x in z['items']:
     #       y = {}
     #       y['image'] = {k:x['image'][k] for k in ['height','width']}
     #       y['link'] = x['link']
     #       image_list.append(y)
     # 
     #   artists[artist] = image_list

     #   print "**************Google Custom Search Engine Request for "+artist+"**************"
     #     
     #   try:
     #       with open('artists.json', 'w') as f:
     #           json.dump(artists, f)
     #   except IOError:
     #       print "Could not write 'artists' json file"

    #return artists[artist]
    return artist.images 
    
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

    mode = 0 # switch to this mode since there appear to actually be lyrics

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

def display_twitter_feed():
    feed = tw.statuses.home_timeline()[:8] # list of dictionaries for each tweet
    n = 0
    font = pygame.font.SysFont('Sans', h/28 )
    font.set_bold(False)
    surface = pygame.Surface((w,int(.90*h)))
    surface.fill((0,0,0))
    #screen.fill((0,0,0))
    for tweet in feed:
        #print "LINE = ",line
        txt = tweet['text']
        txt = txt[:txt.find('http')] 
        lines = textwrap.wrap(txt, 70)
        lines.insert(0, tweet['user']['screen_name']) 
        n+=24
        m = 0
        nn = n
        for line in lines:
            txt = font.render(u"{}".format(line), True, (255, 0, 0))
            surface.blit(txt, (5,nn+m))
            screen.blit(surface, (0,int(.10*h)))
            m+=24
            n+=24

        pygame.display.flip()

def display_weather():
    
    # Tuesday :  Showers and thunderstorms. Lows overnight in the low 70s.
    # Tuesday Night :  Thunderstorms likely. Low 72F. Winds SSW at 5 to 10 mph. Chance of rain 90%.
    
    try:
        r = requests.get("http://api.wunderground.com/api/9862edd5de2d456c/forecast/q/06880.json")
        m1 = r.json()['forecast']['txt_forecast']['forecastday'][0]['title'] + ': ' + r.json()['forecast']['txt_forecast']['forecastday'][0]['fcttext']
        m2 = r.json()['forecast']['txt_forecast']['forecastday'][1]['title'] + ': ' + r.json()['forecast']['txt_forecast']['forecastday'][1]['fcttext']
    except requests.exceptions.ConnectionError as e:
        print "ConnectionError in request in display_weather: ", e
    else:
        font = pygame.font.SysFont('Sans', h/28 )
        font.set_bold(False)
        screen.fill((0,0,0))
        lines = textwrap.wrap(m1+m2, 70)
        n = 5
        for line in lines:
            txt = font.render(u"{}".format(line), True, (255, 0, 0))
            screen.blit(txt, (5,n))
            n+=24
        pygame.display.flip() 

def weather_tts():
    try:
        r = requests.get("http://api.wunderground.com/api/9862edd5de2d456c/forecast/q/10011.json")
        m1 = r.json()['forecast']['txt_forecast']['forecastday'][0]['title'] + ': ' + r.json()['forecast']['txt_forecast']['forecastday'][0]['fcttext']
        m2 = r.json()['forecast']['txt_forecast']['forecastday'][1]['title'] + ': ' + r.json()['forecast']['txt_forecast']['forecastday'][1]['fcttext']
    except requests.exceptions.ConnectionError as e:
        print "ConnectionError in request in display_weather: ", e
        weather = "Sorry, Steve, could not get the weather"
    else:
        weather = textwrap.wrap(m1+m2,99)

    meta = meta_format_radio.format(title='google', service='SA_RINCON65031_')

    s0 = text2mp3(["Good Morning, Steve"], 'good_morning.mp3')
    #weather = display_weather()
    #print weather
    s1 = text2mp3(weather, 'weather.mp3')
    s2 = s0 + s1
    # there appears to be a problem saving as an mp3 on raspi pi
    s2.export('greeting.wav', format='wav')

    #this is the absolute key and involves taking the file created on the local machine and writing it to dropbox
    f = open('greeting.wav', 'rb')
    response = client.put_file('/Public/greeting.wav', f, overwrite=True) # the problem may be FFmpeg or avconv -- pydub can use either
    #print 'uploaded: ', response

    z = client.media("/Public/greeting.wav")
    public_streaming_url = z['url']
    print "public_streaming_url =", public_streaming_url
    master.play_uri(public_streaming_url,'')

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

def hide_buttons():
    global mode
    sleep(1)
    mode = 1

def show_or_select_station():
    global mode
    global station_index
    #if mode == 1:
    if mode !=0:
        station_index=0
        artist = stations[0][0]
        idx = artist.find('Radio')
        if idx != -1:
            artist = artist[:idx-1]
        display_artist_info(artist)
        mode = 0 #2 both station select and lyrics are mode 0 
    else:
        select()

def select(station=None):
    global mode

    if station is None:
        station = stations[station_index]

    uri = station[1]
    print "uri=",uri
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

def cancel():
    global mode
    mode = 1

def end():
    if GPIO:
        GPIO.cleanup()
    sys.exit()

def create_preset_buttons():
    font = pygame.font.SysFont('Sans', 18)
    font.set_bold(False)

    h1 = h/6
    w1 = (w/2) - 15
    presets = []

    for i,s in enumerate(stations[0:6]):
        p = pygbutton.PygButton((10,5+i*h1,w1,h1-5), "{}: {}".format(str(i),s[0]), action=partial(select, station=stations[i]), redraw=False, font=font)
        presets.append(p)
    
    w2 = (w/2) + 10

    for i,s in enumerate(stations[6:13]):
        p = pygbutton.PygButton((w2,5+i*h1,w1,h1-5), "{}: {}".format(str(i+6),s[0]), action=partial(select, station=stations[i+6]), redraw=False, font=font)
        presets.append(p)

    return presets

presets = create_preset_buttons()

def show_preset_buttons():

    global mode
    mode = 3
    screen.fill((100,100,100))

    for p in presets:
        p.draw(screen)

    pygame.display.flip() 

def create_screen_buttons():
    font = pygame.font.SysFont('Sans', 20)
    font.set_bold(True)

    h1 = h/5

    w1 = (w/2) - 15
    b0 = pygbutton.PygButton((10,5,w1,h1-5), 'Lyrics', action=get_lyrics, font=font, redraw=False)
    b1 = pygbutton.PygButton((10,5+h1,w1,h1-5), 'Play-Pause', action=play_pause, font=font)
    b2 = pygbutton.PygButton((10,5+2*h1,w1,h1-5), 'Increase Volume', action=inc_volume, font=font)
    b3 = pygbutton.PygButton((10,5+3*h1,w1,h1-5), 'Decrease Volume', action=dec_volume, font=font)
    b4 = pygbutton.PygButton((10,5+4*h1,w1,h1-5), 'Hide Buttons', action=hide_buttons, font=font)
    
    w2 = (w/2) + 10
    b5 = pygbutton.PygButton((w2,5,w1,h1-5), 'Speak Weather', action=weather_tts, font=font)
    b6 = pygbutton.PygButton((w2,5+h1,w1,h1-5), 'Random Amazon', action=play_random_amazon, font=font)
    b7 = pygbutton.PygButton((w2,5+2*h1,w1,h1-5), 'Show All Presets', action=show_preset_buttons, font=font, redraw=False)
    b8 = pygbutton.PygButton((w2,5+3*h1,w1,h1-5), 'WNYC', action=partial(select, station=stations[0]), font=font)
    b9 = pygbutton.PygButton((w2,5+4*h1,w1,h1-5), 'Show Presets', action=show_or_select_station, font=font, redraw=False)

    buttons = (b0, b1, b2, b3, b4, b5, b6, b7, b8, b9) 
    return buttons

buttons = create_screen_buttons()

def show_screen_buttons():

    screen.fill((100,100,100))

    for b in buttons:
        b.draw(screen)

    pygame.display.flip() 
    
def get_photos(ids=None):
    
    payload = {'client_id':client_id}
    images = []
    for _id in ids:
        try:
            r = requests.get(instagram_base_url.format(_id), params=payload)
            z = r.json()['data'] 
        except Exception as e:
            print "Exception in get_photos - request: {} related to id: {} ".format(e, _id)
        else:
            for d in z: 
                try:
                    if d['type']=='image': #note they have a caption and the caption has text
                        dd = {}
                        dd['url'] = d['images']['standard_resolution']['url']
                        dd['text'] = d['caption']['text']
                        dd['photographer'] = d['caption']['from']['full_name']
                except Exception as e:
                    print "Exception in get_photos - adding indiviual photo {} related to id: {} ".format(e, _id)
                else:
                    images.append(dd)

    return images

def display_image(image):

    try:
        response = requests.get(image['url'])
    except Exception as detail:
        print "response = requests.get(url) generated exception:", detail
        print "changed image status to False"
        img = wand.image.Image(filename = "test.bmp")
    else:

        try:
            img = wand.image.Image(file=StringIO(response.content))
        except Exception as detail:
            img = wand.image.Image(filename = "test.bmp")
            print ("img = wand.image.Image(file=StringIO(response.content)) generated exception:", detail)

    #size = str(DISPLAY[0])+'x'+str(DISPLAY[1])+'^'
    size = str(w)+'x'+str(h)+'^'
    img.transform(resize = size)
    img = img.convert('bmp')
    f = StringIO()
    img.save(f)
    f.seek(0)
    img = pygame.image.load(f).convert()
    f.close()
    img.set_alpha(75) # the lower the number the more faded - 75 seems too faded; try 100

    font = pygame.font.SysFont('Sans', 28)
    font.set_bold(True)

    text = font.render("Photographer: "+image.get('photographer', 'No photographer'), True, (255, 0, 0))

    screen.fill((0,0,0)) 
    screen.blit(img, (0,0))      
    screen.blit(text, (0,0))
    
    txt = image.get('text', 'No title')
    txt = wrapper.fill(txt)
    lines = txt.split('\n')
    font = pygame.font.SysFont('Sans', 16)
    z = 36
    for line in lines:
        try:
            text = font.render(line, True, (255, 0, 0))
        except UnicodeError as e:
            print "UnicodeError in text lines: ", e
        else:
            screen.blit(text, (0,z))
            z+=24

    pygame.display.flip()

    sleep(3)
    screen.fill((0,0,0)) 
    img.set_alpha(255)
    screen.blit(img, (0,0))      
    pygame.display.flip()

def display_image_and_info(image):

    try:
        response = requests.get(image['url'])
    except Exception as detail:
        print "response = requests.get(url) generated exception:", detail
        image.status = False
        print "changed image status to False"
        session.commit()
        img = wand.image.Image(filename = "test.bmp")
    else:

        try:
            img = wand.image.Image(file=StringIO(response.content))
        except Exception as detail:
            img = wand.image.Image(filename = "test.bmp")
            print ("img = wand.image.Image(file=StringIO(response.content)) generated exception:", detail)

    size = str(w)+'x'+str(h)+'^'
    img.transform(resize = size)
    img = img.convert('bmp')
    f = StringIO()
    img.save(f)
    f.seek(0)
    img = pygame.image.load(f, 'bmp').convert()
    f.close()
    img.set_alpha(75) # the lower the number the more faded - 75 seems too faded; try 100

    font = pygame.font.SysFont('Sans', 28)
    font.set_bold(True)

    text = font.render("Photographer: "+image['photographer'], True, (255, 0, 0))

    screen.fill((0,0,0)) 
    screen.blit(img, (0,0))      
    screen.blit(text, (0,0))
    
    txt = image.get('text', 'No title')
    txt = wrapper.fill(txt)
    lines = txt.split('\n')
    font = pygame.font.SysFont('Sans', 16)
    z = 36
    for line in lines:
        try:
            text = font.render(line, True, (255, 0, 0))
        except UnicodeError as e:
            print "UnicodeError in text lines: ", e
        else:
            screen.blit(text, (0,z))
            z+=24

    pygame.display.flip()

if __name__ == '__main__':
    
    images = get_photos(ids)
    L = len(images)
    print "Number of images = {}".format(L)

    prev_title = None  #this is None so if the song title is the empty string, it's not equal
    prev_minute = -1
    ttt = tt = z = time.time()
    new_song = True
    i = 0
    artist = None
    track_strings = []
    track = {}
    KEYS = {pygame.K_p:play_pause, pygame.K_i:inc_volume, pygame.K_d:dec_volume, pygame.K_s:show_or_select_station, pygame.K_j:scroll_down, pygame.K_k:scroll_up, pygame.K_BACKSPACE:cancel, pygame.K_ESCAPE:end, pygame.K_b:cancel, pygame.K_6:partial(select, station=stations[6])} #play_random_amazon}

    while 1:
        
       # pygame.event.get() or .poll() -- necessary to keep pygame window from going to sleep

        event = pygame.event.poll()
        
        if event.type == pygame.NOEVENT:
            pass # want pass and not continue because want this to fall through to the non pygame event stuff
            
        elif event.type == pygame.MOUSEBUTTONDOWN: #=5 - MOUSEMOTION ==4

            if mode==1:
                #pos = pygame.mouse.get_pos()
                #buttons = show_screen_buttons()
                show_screen_buttons()
                mode = 2 # mode = 2 is when the buttons are shown
                #print "mouse position=",pos
                sleep(1)
                
            elif mode==0:
                prev_title = None
                mode = 1 # when mode = 1 images are being flipped

            elif mode==2: #else:  # mode 2 = the buttons are showing 

                button = next((b for b in buttons if b.pressed(event)),buttons[4])
                button.draw_down(screen)
                button.action()
                button.re_draw(screen)

            elif mode==3: #else:  # mode 3 = the presets are showing 

                preset = next((p for p in presets if p.pressed(event)),buttons[4])
                preset.draw_down(screen)
                preset.action()
                #preset.re_draw(screen)
                mode = 1
                    
            pygame.event.clear()  #trying not to catch stray mousedown events since a little unclear how touch screen generates them
                
        elif event.type == pygame.QUIT:
            end()
            
        elif event.type == pygame.KEYDOWN:
            KEYS.get(event.key, lambda:None)()
            #print "event.key=",event.key, type(event.key)
            if 47 < event.key < 58:
                print "Key between 48 and 57", event.key
                partial(select, station=stations[event.key-48])()

        # end of processing pygame events
        # two purposes for next few lines -- return to mode 1 if someone shoes lyrics or shows presets and does nothing and just to see what mode for debugging     
        if time.time() - ttt > 10:
            print time.time(),"mode=",mode
            ttt = time.time()

        if  mode!=1:
            continue

        #if  mode!=1:
        #    if time.time() - ttt > 2:
        #        print time.time(),"mode=",mode
        #        ttt = time.time()
        #    continue

        ## mode = 1 --> flipping pictures or showing weather
        try:
            state = master.get_current_transport_info()['current_transport_state']
        except (requests.exceptions.ConnectionError, soco.exceptions.SoCoUPnPException) as e:
            state = 'ERROR'
            print "Encountered error in state = master.get_current transport_info(): ", e

        # check if sonos is playing anything and, if not, display weather - could be weather and tweets
        if state != 'PLAYING':
            
            minute = datetime.datetime.now().minute
            if minute > prev_minute:

                image = images[random.randrange(0,L-1)]
                display_image(image)
                prev_minute = minute
                prev_title = ''

            continue
                
        # check every two seconds if the track has changed - can you just subscribe to something?
        #try: 
        #event = sub.events.get(timeout=0.5)
        #except Empty:
            #pass
        #else
            #current_track =
            
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
                if not 'date' in track and track.get('artist') and track.get('title') and track.get('album'):
                    if track['album'].find('(c)') == -1:
                        track['date'] = get_release_date(track['artist'], track['album'], track['title'])
                    else:
                        track['date'] = get_recording_date(track['artist'], track['album'], track['title'])
                         
                else:
                    track['date'] = ''
                
                if not 'scrobble' in track and track.get('artist') and track.get('title'):
                    track['scrobble'] = get_scrobble_info(track['artist'], track['title'])
                else:
                    track['scrobble'] = '-100'

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

                track_strings = [DISPLAY[x]+': '+track[x].encode('ascii', 'ignore') for x in DISPLAY if track.get(x)] # str is for scrobble integer 
            
                #if there is no artist (for example when Sonos isn't playing anything or for some radio) then show images of sunsets  ;-)
                artist_image_list = get_images(track['artist'] if track.get('artist') else "sunsets")
                
                print "displaying initial image of ", track.get('artist', '')
                display_song_info(0)
                z = time.time()
                                  
                prev_title = title
                i = 0
                new_song = True

                # this is for AWS SQS
                msg = '--'.join([MINI_DISPLAY[x]+': '+track[x].encode('ascii', 'ignore') for x in MINI_DISPLAY if track.get(x)])
                if msg:
                    m = Message()
                    m.message_attributes = {
                         "artist": {
                             "data_type": "String",
                             "string_value": track.get('artist') if track.get('artist') else 'None' # need something other than ''
                                   },
                         "song": {
                             "data_type": "String",
                             "string_value": track.get('title') if track.get('title') else 'None'
                                 },
                         "album": {
                             "data_type": "String",
                             "string_value": track.get('album') if track.get('album') else 'None'
                                 },
                         "date": {
                             "data_type": "String",
                             "string_value": track.get('date') if track.get('date') else '0' 
                                 },
                         "scrobble": {
                             "data_type": "Number",
                             "string_value": int(track.get('scrobble', -1))
                                 }
                                 }
                    m.set_body(msg)
                    sqs_track_queue.write(m)

                    #this works but not sure there is any reason to tweet each song
                    #try:
                    #    tw.direct_messages.new(user='slzatz', text=msg)
                    #except TwitterHTTPError:
                    #    print "twitter issue"   

                
            elif not new_song:
                # show the next track_string if not the image and text from a new song
                    
                if not track_strings:
                    track_strings.extend([DISPLAY[x]+': '+track[x].encode('ascii', 'ignore') for x in DISPLAY if track.get(x)])
                         
                line = track_strings.pop(0) if track_strings else "No info found"

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
                print time.time(),"displaying a new image of ", track['artist']
                display_song_info2(i) 
            except Exception as e:
               print "Exception:", e
            #else:
                #print "displaying a new image of ", track['artist']
                #display_song_info2(i) 
            
            z = time.time()
        
        sleep(0.1)

