'''
Currently a python 2.7 program but needs to be re-written as python 3 since pygame now runs on 3
This is the current script that runs on a raspberry pi or on Windows that displays
rotating background images from unsplash, info boxes that can display weather, news, twitter, stock prices,, outlook schedule, sales force numbers etc.
When sonos is playing, it displays lyrics and artists pictures - now in a 400 x 400 box and not broadcasting lyrics at the moment but will
The news, stocks, twitter, etc information being broadcast by:
esp_tft_mqtt.py, esp_tft_mqtt_sf.py and esp_tft_mqtt_outlook.py, esp_tft_mqtt_photos currently running on AWS.
The odd "esp_tft..." name comes from the fact that these mqtt broadcasts were originally designed to go to an esp8266 and some still do.
Sonos track artist, track and lyrics are being broadcast by sonos_track_info.py.
esp_tft_mqtt.py message: {"header": "Weather", "text": ["Thursday Night: Some clouds this evening will give way to mainly clear skies overnight. 
Low 18F. Winds WNW at 10 to 20 mph.", "Friday: Mostly sunny skies. High around 30F. Winds W at 10 to 15 mph."], "pos": 0}
esp_tft_mqtt.py message: {"header": "Top WSJ Article", "text": ["Trump Lashes Out as Senator, Others Recount Court Nominee\u2019s Criticism"], "pos": 1}
esp_tft_mqtt.py message: {"header": "WebMD Stock Quote", "text": ["50.955 +0.582% 176.80M 1.91B"], "pos": 2}
esp_tft_mqtt_photos.py message: {"pos":7, "uri":"https://s-media-cache-ak0.pinimg.com/originals/cb/e8/9d/cbe89da159842dd218ec722082ab50c5.jpg", "header":"Neil Young"}
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
from config import unsplash_api_key, aws_mqtt_uri 
import json
import paho.mqtt.client as mqtt
from artist_images_db import *
from datetime import datetime
from itertools import cycle

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--search", help="unsplash search term; if no command line switches defaults to celestial - 543026")
parser.add_argument("-n", "--name", help="unsplash user name; if no command line switches defaults to curated list")
parser.add_argument("-c", "--collection", help="unsplash collection id: celestial=543026, dark=162326 and my nature=525677")
parser.add_argument("-w", "--window", action='store_true', help="use -w if you want a small window instead of full screen")
args = parser.parse_args()

info_topic = "esp_tft" # should be changed to "info"
image_topic = "images"
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
# screen_image will hold the "pure" image before text boxes are drawn on it
screen_image = pygame.Surface((screen_width, screen_height))

#Globals
NUM_BOXES = 11 #numbered 0 to 6 7=artist image, 8=lyrics 9=track_info
positions = []
foos = [] 
sizes = []
timing = []
colors = [(255,0,0), (0,255,0), (0,255,255), (255,255,0), (255,0,255)] # (255,255,255)] # blue too dark
color = cycle(colors)
MAX_HEIGHT = 400
MAX_WIDTH = 665 # with max char/line =  75 and sans font size of 18 this usually works but lines will be truncated to MAX_WIDTH
MIN_WIDTH = 275

star = pygame.image.load('star.png').convert()

bullet_surface = pygame.Surface((5,5))
pygame.draw.rect(bullet_surface, (200,200,200), ((0,0), (5,5))) #col

def on_connect(client, userdata, flags, rc):
    print "(Re)Connected with result code "+str(rc) 

    # Subscribing in on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    client.subscribe([(info_topic, 0), (image_topic, 0)])

def on_disconnect():
    print "Disconnected from mqtt broker"

print "\n"

print "program running ..."

def get_unsplash_images():

    if args.search:
        r = requests.get('{}search/photos'.format(unsplash_uri), params={'client_id':unsplash_api_key, 'per_page':40, 'query':args.search}, timeout=1.0)
        z = r.json()['results']
    elif args.name:
        r = requests.get('{}users/{}/photos'.format(unsplash_uri, args.name), params={'client_id':unsplash_api_key, 'per_page':40}, timeout=1.0)
        z = r.json()
    elif args.collection:
        r = requests.get('{}collections/{}/photos'.format(unsplash_uri, args.collection), params={'client_id':unsplash_api_key, 'per_page':40}, timeout=1.0)
        z = r.json()
    else:
        #r = requests.get('{}photos/curated'.format(unsplash_uri), params={'client_id':unsplash_api_key, 'per_page':40})
        r = requests.get('{}collections/{}/photos'.format(unsplash_uri, '543026'), params={'client_id':unsplash_api_key, 'per_page':40}, timeout=1.0)
        z = r.json()

    return [{'url':x['links']['download'], 'photographer':x['user']['name']} for x in z]

def display_background_image(photo):

    try:
        response = requests.get(photo['url'], timeout=1.0)
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

    img.transform(resize="{}x{}^".format(screen_width, screen_height)) #fits whether original smaller or bigger; ? can accept gravity='center'
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

    font = pygame.font.SysFont('Sans', 24)
    font.set_bold(True)

    text = font.render(photo.get('photographer', 'unknown'), True, (255, 0, 0))

    screen.blit(img, pos)      
    screen.blit(text, (0,0))

    pygame.display.flip()

    # create background image surface without any boxes drawn on it
    screen_image.blit(screen, (0,0))

    del positions[:]
    del foos[:]
    del sizes[:]
    del timing[:]

    for i in range(NUM_BOXES):
        positions.append((1920,1080))
        foos.append(pygame.Surface((0,0)))
        sizes.append((0,0))
        timing.append(0)

def display_artist_image(x):

    print x
    try:
        response = requests.get(x, timeout=1.0)
    except Exception as e:
        print "response = requests.get(url) generated exception: ", e
        # in some future better world may indicate that the image was bad

        return
    else:     
        try:
            img = wand.image.Image(file=StringIO(response.content))
        except Exception as e:
            print "img = wand.image.Image(file=StringIO(response.content)) generated exception from url:", x, "Exception:", e
            # in some future better world may indicate that the image was bad

            return

    try:
        ww = img.width
        hh = img.height
        sq = ww if ww <= hh else hh
        t = ((ww-sq)/2,(hh-sq)/2,(ww+sq)/2,(hh+sq)/2) 
        img.crop(*t)
        # resize should take the image and enlarge it without cropping so will fill vertical but leave space for lyrics
        img.resize(screen_height,screen_height)
        img.resize(400,400)
        conv_img = img.convert('bmp')
        img.close()
    except Exception as e:
        print "img.transfrom or img.convert error:", e
        # in some future better world may indicate that the image was bad

        return

    f = StringIO()
    try:
        conv_img.save(f)
        conv_img.close()
    except wand.exceptions.OptionError as e:
        print "Problem saving image:",e
        # in some future better world may indicate that the image was bad

        return

    f.seek(0)
    img = pygame.image.load(f, 'bmp').convert()
    f.close()
    img_rect = img.get_rect()

    print "img_rect =", img_rect
    # 430 seems to give enough room for lyrics on a standard monintor - used 300 when doing 1000 x 700 in a  window on Windows
    pos = (430,0)
    print "pos =", pos

    foo = pygame.Surface((800,800))
    foo.fill((0,0,0))
    foo.set_alpha(175) #125
    
    foo.blit(img, (0,0))      

    return foo

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

def on_message(client, userdata, msg):
    # {"pos":7, "uri":"https://s-media-cache-ak0.pinimg.com/originals/cb/e8/9d/cbe89da159842dd218ec722082ab50c5.jpg", "header":"Neil Young"}
    # {"pos":4, "header":"Wall Street Journal", "text":"["The rain in spain falls mainly on the plain", "I am a yankee doodle dandy"]}
    topic = msg.topic
    body = msg.payload
    print(topic+": "+str(body))

    try:
        z = json.loads(body)
    except Exception as e:
        print "error reading the mqtt message body: ", e
        return

    if topic in (info_topic, image_topic):

        col = next(color)

        new_screen = pygame.Surface.copy(screen_image) 
        k = z.get('pos',0)
        # Current code below assumes there was a collision the last time the position was painted, might be possible to check
        # Need to repaint in the right order
        for i in sorted(range(len(timing)), key=lambda t:timing[t]):
            # paint a copy of the current screen except for the box that is moving/being updated
            if i==k:
                continue

            new_screen.blit(foos[i], positions[i], ((0,0), sizes[i])) 

        if topic==info_topic:
            #foo is the surface that we 'paint' the text and rectangles on
            foo = pygame.Surface((800,800))
            foo.fill((0,0,0))
            foo.set_alpha(175) #125
            font = pygame.font.SysFont('Sans', 18)
            font.set_bold(True)
            header = "{} [{}]".format(z.get('header', 'no source'), k)
            text = font.render(header, True, col)
            foo.blit(text, (5,5)) 
            font.set_bold(False)

            line_widths = [0] # for situation when text = [''] otherwise line_widths = [] would be fine; happens when no lyrics
            n = 20
            for item in z.get('text',[' ']): 
                item = item if item !='' else ' '
                font.set_bold(False)
                max_chars_line = 66        

                n+=4

                if n+20 > MAX_HEIGHT:
                    break

                if item[0] == '*': 
                    foo.blit(star, (2,n+7))
                    item=item[1:]
                else:
                    foo.blit(bullet_surface, (7,n+13)) #(4,n+13)
                    if item[0] == '#':
                        item=item[1:]
                        font.set_bold(True)
                        max_chars_line = 60

                lines = textwrap.wrap(item, max_chars_line)
                for line in lines:

                    if n+20 > MAX_HEIGHT:
                        break

                    try:
                        text = font.render(line.strip(), True, (255,255,255)) #col
                    except UnicodeError as e:
                        print "UnicodeError in text lines: ", e
                    else:
                        foo.blit(text, (17,n+5)) 
                        line_widths.append(text.get_rect().width)
                        n+=20

            # determine the size of the rectangle for foo and its line border
            max_line = max(line_widths)
            if max_line > MAX_WIDTH:
                max_line = MAX_WIDTH
            elif max_line < MIN_WIDTH:
                max_line = MIN_WIDTH

            new_size = (max_line+18,n+12)
            pygame.draw.rect(foo, col, ((0,0), new_size), 3)

            # put time in upper right of box
            t = datetime.now().strftime("%I:%M %p") #%I:%M:%S %p
            t = t[1:] if t[0] == '0' else t
            t = t[:-2] + t[-2:].lower()
            text = font.render(t, True, col)
            foo.blit(text, (new_size[0]-text.get_rect().width-5,5)) 

        elif topic==image_topic: 

            if z.get('erase'):
                positions[k] = (1920,1080)
                foos[k] = pygame.Surface((0,0)) 
                sizes[k] = (0,0)
                timing[k] = 0
                screen.blit(new_screen, (0,0)) 
                pygame.display.flip() 
                return
                
            uri = z.get('uri')
            if not uri:
                return
            foo = display_artist_image(uri)
            if not foo:
                return
            new_size = (400,400)
            font = pygame.font.SysFont('Sans', 18)
            font.set_bold(True)
            try:
                header = "{} [{}]".format(z.get('header', 'no artist'), k)
            except UnicodeEncodeError:
                header = "{} [{}]".format("Unicode Error", k)
            text = font.render(header, True, col)
            foo.blit(text, (5,5)) 
            font.set_bold(False)
            pygame.draw.rect(foo, col, ((0,0), new_size), 3)
            # for image could just say that new_pos = old_pos (if time is less than some value or something)

        if z.get('move', True):
            attempts = 0
            while attempts < 20:
                new_pos = (random.randint(50,screen_width-new_size[0]), random.randint(50,screen_height-new_size[1]))
                rect = pygame.Rect((new_pos, new_size))    
                idx = rect.collidelist(zip([positions[j] for j in range(len(positions)) if j!=k], [sizes[i] for i in range(len(positions)) if i!=k]))
                if idx == -1:
                    print "No collision"
                    break
                else:
                    print "collision"
                    print "idx = ", idx

                attempts+=1

            else:
                print "Couldn't find a clear area for box"
            

            #new_screen.blit(foo, new_pos, ((0,0), new_size)) 

            blast_y = 0 if new_pos[1]+new_size[1]/2 > screen_height/2 else screen_height
            blast_x = random.randint(0,screen_width)
            blast_point = (blast_x,blast_y)

            pygame.draw.line(screen, col, new_pos, blast_point) 
            pygame.draw.line(screen, col, (new_pos[0],new_pos[1]+new_size[1]), blast_point) 
            pygame.draw.line(screen, col, (new_pos[0]+new_size[0],new_pos[1]), blast_point) 
            pygame.draw.line(screen, col, (new_pos[0]+new_size[0],new_pos[1]+new_size[1]), blast_point) 
            pygame.draw.rect(screen, col, (new_pos, new_size), 3)

            pygame.display.flip()
            sleep(1) #.5

        else:
            new_pos = positions[k]

        new_screen.blit(foo, new_pos, ((0,0), new_size)) 
        screen.blit(new_screen, (0,0)) 
        pygame.display.flip() 

        positions[k] = new_pos
        foos[k] = foo 
        sizes[k] = new_size 
        timing[k] = time()

        return


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(aws_mqtt_uri, 1883, 60)
#not calling client.loop_forever() but explicitly calling client.loop() below
    
photos = get_unsplash_images()

L = len(photos)
print "Number of photos = {}".format(L)
if not photos:
    sys.exit("No photos")

prev_artist_track = None
nn = 0 # measures the number of times in a row we've displayed the same artist so it doesn't go on endlessly

screen.fill((0,0,0)) 
pygame.display.flip()

photo = random.choice(photos)
print "Next photo is:", photo.get('photographer', '').encode('ascii', errors='ignore'), photo.get('text','').encode('ascii', errors='ignore')
display_background_image(photo)

num_photos_shown = 1
t1 = time()
while 1:
    #pygame.event.get() or .poll() -- necessary to keep pygame window from going to sleep
    event = pygame.event.poll()
    
    if event.type == pygame.NOEVENT:
        pass # want pass and not continue because want this to fall through to the non pygame event stuff
        
    elif event.type == pygame.QUIT:
        sys.exit(0)

    client.loop(timeout = 1.0)

    if time() - t1 > 3600: # picture flips each hour
        photo = random.choice(photos)
        print "Next photo is:", photo.get('photographer', '').encode('ascii', errors='ignore'), photo.get('text','').encode('ascii', errors='ignore')
        display_background_image(photo)
        num_photos_shown+=1
        # shouldn't have to do this but I seem to be losing connection to mqtt broker
        # and this seems to be working
        client.disconnect()
        client.reconnect()

        t1 = time()

    sleep(1)
