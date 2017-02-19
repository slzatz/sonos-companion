'''
This is the current script that runs on a raspberry pi or on Windows to display
lyrics and artists pictures to accompany what is playing on Sonos
This script could also be the basis for using a large screen to display
The information being broadcast by esp_tft_mqtt.py
Next photo is: Michael Hacker
1486671741.8 database connection alive 2
esp_tft {"header": "Weather", "text": ["Thursday Night: Some clouds this evening will give way to mainly clear skies overnight. Low 18F. Winds WNW at 10 to 20 mph.", "Friday: Mostly
sunny skies. High around 30F. Winds W at 10 to 15 mph."], "pos": 0}
mqtt messge body = {"header": "Weather", "text": ["Thursday Night: Some clouds this evening will give way to mainly clear skies overnight. Low 18F. Winds WNW at 10 to 20 mph.", "Frid
ay: Mostly sunny skies. High around 30F. Winds W at 10 to 15 mph."], "pos": 0}
esp_tft {"header": "Top WSJ Article", "text": ["Trump Lashes Out as Senator, Others Recount Court Nominee\u2019s Criticism"], "pos": 1}
mqtt messge body = {"header": "Top WSJ Article", "text": ["Trump Lashes Out as Senator, Others Recount Court Nominee\u2019s Criticism"], "pos": 1}
esp_tft {"header": "WebMD Stock Quote", "text": ["50.955 +0.582% 176.80M 1.91B"], "pos": 2}
mqtt messge body = {"header": "WebMD Stock Quote", "text": ["50.955 +0.582% 176.80M 1.91B"], "pos": 2}
'''
import platform
import os
import argparse
import pygame
from time import time, sleep
import random
import requests
import textwrap
import sys
from cStringIO import StringIO
import wand.image
from config import mqtt_uris, google_api_key, unsplash_api_key, aws_mqtt_uri 
import json
import paho.mqtt.client as mqtt
from artist_images_db import *
from apiclient import discovery #google custom search api
import httplib2 #needed by the google custom search engine module apiclient

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--search", help="unsplash search term; if no command line switches defaults to curated list")
parser.add_argument("-n", "--name", help="unsplash user name; if no command line switches defaults to curated list")
parser.add_argument("-c", "--collection", help="unsplash collection id: celestial=543026, dark=162326 and my nature=525677")
parser.add_argument("-w", "--window", action='store_true', help="use -w if you want a small window instead of full screen")
args = parser.parse_args()

with open('location') as f:
    location = f.read().strip()

sonos_topic = "sonos/{}/current_track".format(location)
info_topic = "esp_tft"
#mqtt_uri = mqtt_uris[location]
mqtt_uri = aws_mqtt_uri
print "mqtt_uri =",mqtt_uri

unsplash_uri = 'https://api.unsplash.com/'

# Environment varialbes for pygame
if platform.system() == 'Windows':
    os.environ['SDL_VIDEODRIVER'] = 'windib'
elif platform.system() == "Linux":
    os.environ['SDL_VIDEODRIVER'] = 'x11' 
    os.environ['SDL_VIDEO_CENTERED'] = '1'
else:
    sys.exit("Currently unsupported hardware/OS")

# Should be (6,0) if pygame inits correctly
#r = pygame.init()
#print "pygame init",r
#below just initiating the modules that are needed instead of all with pygame.init()
pygame.font.init()
pygame.display.init()

if platform.machine()[:3] == 'arm': 
    pygame.mouse.set_visible(False)

#if platform.system() == 'Windows':
if args.window:
    screen_width, screen_height = 1000,700
else:
    screen_width, screen_height = pygame.display.Info().current_w, pygame.display.Info().current_h

print "screen width =", screen_width, "; screen height =", screen_height
print "Can't execute line below without a control-c"
# Note suggestion from https://www.raspberrypi.org/forums/viewtopic.php?f=32&t=22306 is sys.exit(0)
# might be necessary and I would put a try except around the while loop but haven't done that
screen = pygame.display.set_mode((screen_width, screen_height))
screen.fill((0,0,0))
erase_rect = pygame.Surface((screen_width,screen_height-70))
erase_rect.fill((0,0,0))
#text_rect = pygame.Surface((screen_width,70))
#text_rect = pygame.Surface((625,70))
#text_rect.fill((0,0,0))
font = pygame.font.SysFont('Sans', 30)
font.set_bold(True)
text = font.render("Sonos-Companion", True, (0,0,0))
screen.fill((255,255,255)) 
screen.blit(text, (0,0))
pygame.display.flip()

trackinfo = {"artist":None, "track_title":None}

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    #client.subscribe(topic)
    client.subscribe([(sonos_topic, 0), (info_topic, 0)])

print "\n"

print "program running ..."

def get_photos():
    if args.search:
        r = requests.get('{}search/photos'.format(unsplash_uri), params={'client_id':unsplash_api_key, 'per_page':40, 'query':args.search})
        z = r.json()['results']
    elif args.name:
        r = requests.get('{}users/{}/photos'.format(unsplash_uri, args.name), params={'client_id':unsplash_api_key, 'per_page':40})
        z = r.json()
    elif args.collection:
        r = requests.get('{}collections/{}/photos'.format(unsplash_uri, args.collection), params={'client_id':unsplash_api_key, 'per_page':40})
        z = r.json()
    else:
        r = requests.get('{}photos/curated'.format(unsplash_uri), params={'client_id':unsplash_api_key, 'per_page':40})
        z = r.json()
    return [{'url':x['links']['download'], 'photographer':x['user']['name']} for x in z]

def display_photo(photo):

    try:
        response = requests.get(photo['url'])
    except Exception as e:
        print "response = requests.get(url) generated exception:", e
        return

    try:
        img = wand.image.Image(file=StringIO(response.content))
    except Exception as e:
        print "img = wand.image.Image(file=StringIO(response.content)) generated exception:", e
        if "Insufficient memory" in repr(e):
            sys.exit("Insufficient memory -- line 104")
        else:
            return

    img.transform(resize="{}x{}>".format(screen_width, screen_height-70))
    conv_img = img.convert('bmp')
    # need to close image or there is a memory leak
    # could do: with img.convert('bmp') as converted; converted.save(f)
    img.close()

    f = StringIO()
    try:
        conv_img.save(f)
    except Exception as e:
        print "image.save(f) with error:", e
        return

    # need to close image or there is a memory leak - could do with ... (see above)
    conv_img.close()

    f.seek(0)

    try:
        img = pygame.image.load(f).convert()
    except pygame.error as e:
        print e
        return

    f.close()
    img_rect = img.get_rect()
    pos = ((screen_width-img_rect.width)/2, 0)

    font = pygame.font.SysFont('Sans', 28)
    font.set_bold(True)

    text = font.render(photo.get('photographer', 'unknown'), True, (255, 0, 0))

    screen.blit(erase_rect, (0,0))
    #screen.fill((0,0,0)) 
    screen.blit(img, pos)      
    screen.blit(text, (0,0))

    img = None ##########################################
    
    txt = photo.get('text', '')
    lines = textwrap.wrap(txt, 60)
    font = pygame.font.SysFont('Sans', 16)
    n = 36
    for line in lines:
        try:
            text = font.render(line, True, (255, 0, 0))
        except UnicodeError as e:
            print "UnicodeError in text lines: ", e
        else:
            screen.blit(text, (0,n))
            n+=24

    pygame.display.flip()

def get_artist_images(name):

    print "**************Google Custom Search Engine Request for "+name+"**************"
    http = httplib2.Http()
    service = discovery.build('customsearch', 'v1',  developerKey=google_api_key, http=http)
    z = service.cse().list(q=name, searchType='image', imgType='face', imgSize='xlarge', num=10, cx='007924195092800608279:0o2y8a3v-kw').execute() 

    try:
        a = session.query(Artist).filter(func.lower(Artist.name)==name.lower()).one()
    except NoResultFound:
        print "Don't have that name in db so created it"
        a = Artist()
        a.name = name
        session.add(a)
        session.commit()
    except Exception as e:
        print "a = session.query(Artist).filter(func.lower.. error:", e 
        return []

    # must delete images before you can add new whole new set of images
    session.query(Image).filter_by(artist_id=a.id).delete()
    session.commit()

    images = []

    for data in z['items']:
        image=Image()
        image.link = data['link']
        image.width = data['image']['width']
        image.height = data['image']['height']
        image.ok = True
        images.append(image)

    a.images = images
    session.commit()
            
    print "images = ", images
    return images 
positions = [(50,50), (300,300), (500,900), (700,700)]
erase = [80,250,20]
def on_message(client, userdata, msg):
    topic = msg.topic
    body = msg.payload
    print(topic+": "+str(body))

    try:
        z = json.loads(body)
    except Exception as e:
        print "error reading the mqtt message body: ", e
        return

    if topic==info_topic:
        pos = z.get('pos',0)
        #screen.blit(text_rect, (0,screen_height-70))
        #screen.blit(text_rect, (5+pos*625,screen_height-70))
        text_rect = pygame.Surface((625,erase[pos]))
        text_rect.fill((0,0,0))
        screen.blit(text_rect, positions[pos])
        font = pygame.font.SysFont('Sans', 18)
        #n = screen_height - 70
        text = font.render(z.get('header', 'no source'), True, (255, 0, 0))
        screen.blit(text, (positions[pos][0],positions[pos][1]))
        n = 20
        for text in z.get('text',''): 
            lines = textwrap.wrap(text, 75)
            for line in lines:
                try:
                    text = font.render(line.strip(), True, (255, 0, 0))
                except UnicodeError as e:
                    print "UnicodeError in text lines: ", e
                else:
                    screen.blit(text, (positions[pos][0],positions[pos][1]+n))
                    n+=20

        pygame.display.flip()
        return

    print "The python object from mqtt is:",z
    artist = z.get("artist")
    track_title = z.get("title", "")
    lyrics = z.get("lyrics", "")

    print "on_message:artist =",artist
    print "on_message:track_title =",track_title
    trackinfo.update({"artist":artist, "track_title":track_title, "lyrics":lyrics})

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(mqtt_uri, 1883, 60)
#not calling client.loop_forever() but explicitly calling client.loop() below
    
photos = get_photos()

L = len(photos)
print "Number of photos = {}".format(L)
if photos:
    display_photo(random.choice(photos))

prev_artist_track = None
t1 = time()
nn = 0 # measures the number of times in a row we've displayed the same artist so it doesn't go on endlessly

def draw_lyrics(lyrics, x_coord):
    print "drawing lyrics"
    font = pygame.font.SysFont('Sans', 16)
    n = 10
    for lyric in lyrics:
        lines = textwrap.wrap(lyric, 60)
        for line in lines:
            try:
                text = font.render(line.strip(), True, (255, 0, 0))
            except UnicodeError as e:
                print "UnicodeError in text lines: ", e
            else:
                screen.blit(text, (x_coord,n))
                n+=20

num_photos_shown = 0
screen.fill((0,0,0)) 
pygame.display.flip()
while 1:
    #pygame.event.get() or .poll() -- necessary to keep pygame window from going to sleep
    event = pygame.event.poll()
    
    if event.type == pygame.NOEVENT:
        pass # want pass and not continue because want this to fall through to the non pygame event stuff
        
    elif event.type == pygame.QUIT:
        sys.exit(0)

    client.loop()

    cur_time = time()

    artist = trackinfo['artist']
    track = trackinfo['track_title']

    if not artist:
        if photos:
            if cur_time - t1 > 15:
                if num_photos_shown > 0:
                    continue
                photo = random.choice(photos)
                print "Next photo is:", photo.get('photographer', '').encode('ascii', errors='ignore'), photo.get('text','').encode('ascii', errors='ignore')
                display_photo(photo)
                num_photos_shown+=1

                alive = session.query(session.query(Artist).exists()).all()
                if alive[0][0]:
                    print cur_time, "database connection alive", num_photos_shown

                t1 = time()
        sleep(1)
        continue

    artist_track = "{} - {}".format(artist,track)

    if prev_artist_track != artist_track:

        prev_artist_track = artist_track
        nn = 0

        print "about to query image database for artist", artist

        try:
            a = session.query(Artist).filter(func.lower(Artist.name)==artist.lower()).one()
        except NoResultFound:
            images = get_artist_images(artist)
            if not images:
                print "Could not find images for {}".format(artist)
                continue
        except Exception as e:
            print "error trying to find artist:", e
            continue
        else:
            images = a.images

        if len([i for i in images if i.ok]) < 8:
            print "fewer than 8 images so getting new set of images for artist"
            images = get_artist_images(artist)
            if not images:
                print "Could not find images for {}".format(artist)
                continue

        #random.shuffle(images) - messes up things if you have to update an image with image.ok = False
        images0 = images[:]       

        #line = "{} - {}".format(artist,track)

        font = pygame.font.SysFont('Sans', 14)
        font.set_bold(True)
        text = font.render(artist_track, True, (255,0,0))

        screen.fill((0,0,0))

        screen.blit(text, (0,screen_height-16))

        draw_lyrics(trackinfo['lyrics'][:47],0)
        draw_lyrics(trackinfo['lyrics'][47:],1450)

        pygame.display.flip()
            
        t1 = 0

    if cur_time - t1 < 15:
        continue

    # note that alive below is just pinging the database -- could also try
    #conn = engine.connect() # presumably this could be done once at the start of the script
    #z = conn.execute("SELECT 1")
    #z.fetchall()
    #[(1,)]
    alive = session.query(session.query(Artist).exists()).all()
    if alive[0][0]:
        print "database connection alive"

    if not images:
        continue

    if not images0:
        images0 = images[:]
    x = images0.pop()

    nn+=1
    # if sonos no longer playing then artist images would be stuck on last artist without this
    if nn > 25:
        trackinfo['artist'] = None
        prev_artist_track = None

    print x.link
    if not x.ok:
         print "The link isn't OK. ",x.link
         continue
    try:
        response = requests.get(x.link)
    except Exception as e:
        print "response = requests.get(url) generated exception: ", e
        try:
            x.ok = False
            session.commit()
            print "ok was set to False for", x.link
        except Exception as e:
            print "x.ok = False - error:", e

        continue
    else:     
        try:
            img = wand.image.Image(file=StringIO(response.content))
        except Exception as e:
            print "img = wand.image.Image(file=StringIO(response.content)) generated exception from url:", x.link, "Exception:", e

            try:
                x.ok = False
                session.commit()
                print "ok was set to False for", x.link
            except Exception as e:
                print "x.ok set to false error:", e

            continue

    try:
        ww = img.width
        hh = img.height
        sq = ww if ww <= hh else hh
        #crop(left, top, right, bottom)
        t = ((ww-sq)/2,(hh-sq)/2,(ww+sq)/2,(hh+sq)/2) 
        img.crop(*t)
        # resize should take the image and enlarge it without cropping so will fill vertical but leave space for lyrics
        img.resize(screen_height,screen_height)
        conv_img = img.convert('bmp')
        img.close()
    except Exception as e:
        print "img.transfrom or img.convert error:", e

        try:
            x.ok = False
            session.commit()
            print "ok was set to False for", x.link
        except Exception as e:
            print "x.ok set to false error:", e

        continue

    t1 = time()
    print t1

    f = StringIO()
    try:
        conv_img.save(f)
        conv_img.close()
    except wand.exceptions.OptionError as e:
        print "Problem saving image:",e

        try:
            x.ok = False
            session.commit()
            print "ok was set to False for", x.link
        except Exception as e:
            print "x.ok set to false error:", e

        continue

    f.seek(0)
    img = pygame.image.load(f, 'bmp').convert()
    f.close()
    img_rect = img.get_rect()

    print "img_rect =", img_rect
    # 430 seems to give enough room for lyrics on a standard monintor - used 300 when doing 1000 x 700 in a  window on Windows
    pos = (430,0)
    print "pos =", pos
    
    screen.blit(img, pos)      
    pygame.display.flip()

    sleep(1)
