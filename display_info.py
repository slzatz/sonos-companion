'''
Currently a python 2.7 program but needs to be re-written as python 3 since pygame now runs on 3
This is the current script that runs on a raspberry pi or on Windows to display
pictures from unsplash, artists' images when music is playing and weather, news, twitter, stock prices, etc.
It displays lyrics and artists pictures to accompany what is playing on Sonos
The news, stocks, twitter, etc information being broadcast by esp_tft_mqtt.py currently running on AWS
track_info.py is also broadcasting track and artist
esp_tft_mqtt.py message: {"header": "Weather", "text": ["Thursday Night: Some clouds this evening will give way to mainly clear skies overnight. 
Low 18F. Winds WNW at 10 to 20 mph.", "Friday: Mostly sunny skies. High around 30F. Winds W at 10 to 15 mph."], "pos": 0}
esp_tft_mqtt.py message: {"header": "Top WSJ Article", "text": ["Trump Lashes Out as Senator, Others Recount Court Nominee\u2019s Criticism"], "pos": 1}
esp_tft_mqtt.py message: {"header": "WebMD Stock Quote", "text": ["50.955 +0.582% 176.80M 1.91B"], "pos": 2}
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
from config import google_api_key, unsplash_api_key, aws_mqtt_uri 
import json
import paho.mqtt.client as mqtt
from artist_images_db import *
from apiclient import discovery #google custom search api
import httplib2 #needed by the google custom search engine module apiclient
from datetime import datetime
from itertools import cycle

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--search", help="unsplash search term; if no command line switches defaults to celestial - 543026")
parser.add_argument("-n", "--name", help="unsplash user name; if no command line switches defaults to curated list")
parser.add_argument("-c", "--collection", help="unsplash collection id: celestial=543026, dark=162326 and my nature=525677")
parser.add_argument("-w", "--window", action='store_true', help="use -w if you want a small window instead of full screen")
args = parser.parse_args()

with open('location') as f:
    location = f.read().strip()

sonos_topic = "sonos/{}/current_track".format(location)
info_topic = "esp_tft"
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
NUM_BOXES = 7 #numbered 0 to 6
positions = []
image_subsurfaces = [] # 'global' list to hold the image subsurfaces to "patch" screen
foos = [] #######################################################################################################
sizes = []
colors = [(255,0,0), (0,255,0), (0,255,255), (255,255,0), (255,0,255)] # (255,255,255)] # blue too dark
color = cycle(colors)
MAX_HEIGHT = 375
MAX_WIDTH = 665 # with max char/line =  75 and sans font size of 18 this usually works but lines will be truncated to MAX_WIDTH
MIN_WIDTH = 200

bullet_surface = pygame.Surface((5,5))

#font = pygame.font.SysFont('Sans', 30)
#font.set_bold(True)
#text = font.render("Sonos-Companion", True, (0,0,0))
#screen.fill((255,255,255)) 
#screen.blit(text, (0,0))
#pygame.display.flip()

trackinfo = {"artist":None, "track_title":None}

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
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
        #r = requests.get('{}photos/curated'.format(unsplash_uri), params={'client_id':unsplash_api_key, 'per_page':40})
        r = requests.get('{}collections/{}/photos'.format(unsplash_uri, '543026'), params={'client_id':unsplash_api_key, 'per_page':40})
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

    #screen.blit(blank_surface, (0,0)) #####################################################################################
    screen.blit(img, pos)      
    screen.blit(text, (0,0))

    pygame.display.flip()

    # Blit current image before any text has been written on it into screen_image and
    # then create the subsurfaces that can be used to "patch" the impact of the text boxes
    screen_image.blit(screen, (0,0))

    # when a new background image is displayed then delete the subsurfaces
    #image_subsurfaces.clear() # only 3.3 and above
    del image_subsurfaces[:]
    del positions[:]
    del foos[:]
    del sizes[:]

    for i in range(NUM_BOXES):
        image_subsurfaces.append(pygame.Surface((0,0)))
        positions.append((1920,1080))
        foos.append(pygame.Surface((0,0)))
        sizes.append((0,0))

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

def display_artist_image(x):

    print x.link
    if not x.ok:
         print "The link isn't OK. ",x.link
         return
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

        return
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

            return

    try:
        ww = img.width
        hh = img.height
        sq = ww if ww <= hh else hh
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

        return

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

        return

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
    topic = msg.topic
    body = msg.payload
    print(topic+": "+str(body))

    try:
        z = json.loads(body)
    except Exception as e:
        print "error reading the mqtt message body: ", e
        return

    if topic==info_topic:

        # if there is an active track don't post weather/news/twitter/stock price message boxes
        if trackinfo['artist']:
            return

        col = next(color)

        # create a copy of the current screen that we will be blitting later
        #new_screen = pygame.Surface.copy(screen) ############################################### 
        new_screen = pygame.Surface.copy(screen_image) 
        k = z.get('pos',0)

        # Current code below assumes there was a collision the last time the position was painted, might be possible to check
        # Problems: we could be painting in wrong order and should check if no collision no need to reblit the foos

        for i in range(len(foos)):
            # restore the background image where all the text boxes are, not just the one that is moving and repaint all the old ones below
            #new_screen.blit(image_subsurfaces[i], positions[i])###########################################################
            if i==k:
                continue
            # repainting all the text boxes except the one about to be painted seems the best way to deal with erasing a box
            new_screen.blit(foos[i], positions[i], ((0,0), image_subsurfaces[i].get_rect().size)) 
        
        #foo is the surface that we 'paint' the text and rectangles on
        foo = pygame.Surface((800,800))
        foo.fill((0,0,0))
        foo.set_alpha(175) #125

        font = pygame.font.SysFont('Sans', 18)
        font.set_bold(True)
        text = font.render(z.get('header', 'no source'), True, col)
        foo.blit(text, (5,5)) 
        font.set_bold(False)

        line_widths = []
        n = 20
        for item in z.get('text',''): 
            if n+20 > MAX_HEIGHT:
                break

            pygame.draw.rect(bullet_surface, col, ((0,0), (5,5)))
            foo.blit(bullet_surface, (4,n+13))

            if item[0] == '#':
                item=item[1:]
                font.set_bold(True)
                max_chars_line = 65
            else:
                font.set_bold(False)
                max_chars_line = 75

            #lines = textwrap.wrap(item, 75)
            lines = textwrap.wrap(item, max_chars_line)
            for line in lines:

                if n+20 > MAX_HEIGHT:
                    break

                try:
                    text = font.render(line.strip(), True, (255,255,255)) #col
                except UnicodeError as e:
                    print "UnicodeError in text lines: ", e
                else:
                    foo.blit(text, (14,n+5))
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

        attempts = 0
        while attempts < 20:
            new_pos = (random.randint(50,screen_width-new_size[0]), random.randint(50,screen_height-new_size[1]))
            rect = pygame.Rect((new_pos, new_size))    
            idx = rect.collidelist(zip([positions[j] for j in range(len(positions)) if j!=k], [image_subsurfaces[i].get_rect().size for i in range(len(positions)) if i!=k]))
            if idx == -1:
                print "No collision"
                break
            else:
                print "collision"
                print "idx = ", idx

            attempts+=1

        else:
            print "Couldn't find a clear area for box"
            
        new_screen.blit(foo, new_pos, ((0,0), new_size)) 

        # Below is saving the text box to reblit the screen to deal with collisions
        #cropped_foo = pygame.Surface(new_size)
        #cropped_foo.blit(foo, (0,0)) # unfortunately lose alpha
        #foos[k] = cropped_foo
        foos[k] = foo ##############################
        sizes[k] = new_size ###################################

        blast_y = 0 if new_pos[1]+new_size[1]/2 > screen_height/2 else screen_height
        blast_x = random.randint(0,screen_width)
        blast_point = (blast_x,blast_y)

        pygame.draw.line(screen, col, new_pos, blast_point) 
        pygame.draw.line(screen, col, (new_pos[0],new_pos[1]+new_size[1]), blast_point) 
        pygame.draw.line(screen, col, (new_pos[0]+new_size[0],new_pos[1]), blast_point) 
        pygame.draw.line(screen, col, (new_pos[0]+new_size[0],new_pos[1]+new_size[1]), blast_point) 

        pygame.draw.rect(screen, col, (new_pos, new_size), 3)

        prev_pos = positions[k]
        subsurface = image_subsurfaces[k]

        if subsurface.get_height() > 1:
            screen.blit(subsurface, prev_pos)

            prev_size = subsurface.get_rect().size
            #blast_y = 0 if prev_pos[1]+prev_size[1]/2 > screen_height/2 else screen_height
            #blast_x = random.randint(0,screen_width)
            #blast_point = (blast_x,blast_y)
            col = (125,125,125)

            #pygame.draw.line(screen, col, prev_pos, blast_point) 
            #pygame.draw.line(screen, col, (prev_pos[0],prev_pos[1]+prev_size[1]), blast_point) 
            #pygame.draw.line(screen, col, (prev_pos[0]+prev_size[0],prev_pos[1]), blast_point) 
            #pygame.draw.line(screen, col, (prev_pos[0]+prev_size[0],prev_pos[1]+prev_size[1]), blast_point) 

            pygame.draw.rect(screen, col, (prev_pos, prev_size), 3)

        pygame.display.flip()
        sleep(1) #.5
        screen.blit(new_screen, (0,0)) 
        pygame.display.flip() 
        subsurface = screen_image.subsurface((new_pos, new_size)) 
        image_subsurfaces[k] = subsurface
        positions[k] = new_pos

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
client.connect(aws_mqtt_uri, 1883, 60)
#not calling client.loop_forever() but explicitly calling client.loop() below
    
photos = get_photos()

L = len(photos)
print "Number of photos = {}".format(L)
if not photos:
    sys.exit("No photos")

display_photo(random.choice(photos))

prev_artist_track = None
nn = 0 # measures the number of times in a row we've displayed the same artist so it doesn't go on endlessly

screen.fill((0,0,0)) 
pygame.display.flip()

photo = random.choice(photos)
print "Next photo is:", photo.get('photographer', '').encode('ascii', errors='ignore'), photo.get('text','').encode('ascii', errors='ignore')
display_photo(photo)

num_photos_shown = 1
t1 = t0 = time()
while 1:
    #pygame.event.get() or .poll() -- necessary to keep pygame window from going to sleep
    event = pygame.event.poll()
    
    if event.type == pygame.NOEVENT:
        pass # want pass and not continue because want this to fall through to the non pygame event stuff
        
    elif event.type == pygame.QUIT:
        sys.exit(0)

    client.loop()

    cur_time = time()

    if cur_time - t0 > 300:
        try:
            alive = session.query(session.query(Artist).exists()).all()
        except Exception as e:
             print "Exception checking if db alive: ", e
        else:
            if alive[0][0]:
                print cur_time, "The connection to Artsit db is alive", num_photos_shown
            else:
                print cur_time, "There is a problem with the Artist db connection"

        t0 = time()

    artist = trackinfo['artist']
    track = trackinfo['track_title']

    if not artist:
        if cur_time - t1 > 3600: # picture flips each hour
            photo = random.choice(photos)
            print "Next photo is:", photo.get('photographer', '').encode('ascii', errors='ignore'), photo.get('text','').encode('ascii', errors='ignore')
            display_photo(photo)
            num_photos_shown+=1

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

    if not images:
        continue

    if not images0:
        images0 = images[:]

    x = images0.pop()
    display_artist_image(x)

    nn+=1
    # if sonos no longer playing then artist images would be stuck on last artist without this
    if nn > 25:
        trackinfo['artist'] = None
        prev_artist_track = None
        photo = random.choice(photos)
        print "Next photo is:", photo.get('photographer', '').encode('ascii', errors='ignore'), photo.get('text','').encode('ascii', errors='ignore')
        display_photo(photo)
        num_photos_shown+=1


    t1 = time()
    print t1

    sleep(1)
