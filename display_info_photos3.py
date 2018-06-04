'''
Currently a python 2.7 program but needs to be re-written as python 3 since pygame now runs on 3
This is the current script that runs on a raspberry pi or on Windows that displays
rotating background images from unsplash, info boxes that can display weather, news, twitter, stock prices,, outlook schedule, sales force numbers etc.
When sonos is playing, it displays lyrics and artists pictures - now in a 400 x 400 box 
The news, stocks, twitter, etc information being broadcast by:
esp_tft_mqtt.py, esp_tft_mqtt_sf.py and esp_tft_mqtt_outlook.py, esp_tft_mqtt_photos currently running on AWS.
The odd "esp_tft..." name comes from the fact that these mqtt broadcasts were originally designed to go to an esp8266 and some still do.
Sonos track artist, track and lyrics are being broadcast by sonos_track_info.py.
esp_tft_mqtt.py message: {"header": "Weather", "text": ["Thursday Night: Some clouds this evening will give way to mainly clear skies overnight. 
Low 18F. Winds WNW at 10 to 20 mph.", "Friday: Mostly sunny skies. High around 30F. Winds W at 10 to 15 mph."], "pos": 0}
esp_tft_mqtt.py message: {"header": "Top WSJ Article", "text": ["Trump Lashes Out as Senator, Others Recount Court Nominee\u2019s Criticism"], "pos": 1}
esp_tft_mqtt.py message: {"header": "WebMD Stock Quote", "text": ["50.955 +0.582% 176.80M 1.91B"], "pos": 2}
esp_tft_mqtt_photos.py message: {"pos":7, "uri":"https://s-media-cache-ak0.pinimg.com/originals/cb/e8/9d/cbe89da159842dd218ec722082ab50c5.jpg", "header":"Neil Young"}

0=temp sensors (CT, NYC)
1=news feeds (WSJ, NYT, ArsTechnica, Reddit All, Twitter)
2=stock quote
3=ToDos
4=sonos status (PLAYING, TRANSITIONING, STOPPED) broadcast by sonos_track_info on topic esp_tft and also on sonos/{loc}/status for esp_tft_mqtt_photos(and lyrics) 
5=sales forecast
6=outlook_schedule
7=artist image
8=lyrics
9=track_info broadcast by sonos_track_info.py
10=sonos status (PLAYING, TRANSITIONING, STOPPED
11=sales top opportunities
12=Reminders (alarms) 
13=Ticklers
14=Facts
15=weather/tides
16=Industry
17=temp sensor
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
from io import BytesIO
import wand.image
from config import unsplash_api_key, aws_mqtt_uri 
import json
import paho.mqtt.client as mqtt
from datetime import datetime
from itertools import cycle
import re

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
    os.environ['SDL_VIDEO_WINDOW_POS'] = '-150, -1400'
elif platform.system() == "Linux":
    os.environ['SDL_VIDEODRIVER'] = 'x11' 
    if args.window:
        os.environ['SDL_VIDEO_WINDOW_POS'] = '-150, -1400' #do not want this line if there is no external monitor
    #os.environ['SDL_VIDEO_CENTERED'] = '1' # used this for raspy pi
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
    screen_width, screen_height = 2560,1440
else:
    screen_width, screen_height = pygame.display.Info().current_w, pygame.display.Info().current_h

print("screen width =", screen_width, "; screen height =", screen_height)
print("Can't execute line below without a control-c")
# Note suggestion from https://www.raspberrypi.org/forums/viewtopic.php?f=32&t=22306 is sys.exit(0)
# might be necessary and I would put a try except around the while loop but haven't done that
screen = pygame.display.set_mode((screen_width, screen_height), pygame.NOFRAME)
screen.fill((0,0,0))
# screen_image will hold the "pure" image before text boxes are drawn on it
screen_image = pygame.Surface((screen_width, screen_height))

#Globals
LAYOUT = {
0:{'height':200, 'location':None}, #temp sensors (CT, NYC)
1:{'height':400, 'location':None}, #news feeds (WSJ, NYT, ArsTechnica, Reddit All, Twitter)
2:{'height':300, 'location':None}, #stock quote
3:{'height':500, 'location':None}, #ToDos
4:{'height':600, 'location':(-600,400)}, #gmail and google calendar
5:{'height':250, 'location':None}, #sales forecast
6:{'height':500, 'location':(-600,-550)}, #outlook_schedule
7:{'height':400, 'location':None}, #artist image
8:{'height':700, 'location':None}, #lyrics
9:{'height':200, 'location':None}, #track_info broadcast by sonos_track_info.py
10:{'height':200, 'location':None},#sonos status (PLAYING, TRANSITIONING, STOPPED
11:{'height':500, 'location':None},#sales top opportunities
12:{'height':300, 'location':None},#Reminders (alarms)
13:{'height':500, 'location':None},#Poems
14:{'height':150, 'location':None},#Facts
15:{'height':300, 'location':None},#weather/tides
16:{'height':600, 'location':None},#Industry
17:{'height':200, 'location':None} #temp sensor
}
NUM_BOXES = 18 
positions = []
foos = [] 
sizes = []
timing = []
colors = [(0,255,0), (0,255,255), (255,255,0), (255,0,255), (127,127,127)] # (255,255,255)] # blue too dark and red for alerts
color = cycle(colors)
#MAX_HEIGHT = screen_height - 50 #875
MAX_WIDTH = 665 # with max char/line =  75 and sans font size of 18 this usually works but lines will be truncated to MAX_WIDTH
MIN_WIDTH = 275
on_top = [7, 8, 12]

color_map = {'{blue}':(0,0,255), '{red}':(255,0,0), '{green}':(0,255,0), '{grey}':(127,127,127), '{gray}':(127,127,127), '{}':(255,255,255), '{white}':(255,255,255), 'black':(0,0,0)}
star = pygame.image.load('star.png').convert()

bullet_surface = pygame.Surface((5,5))
pygame.draw.rect(bullet_surface, (200,200,200), ((0,0), (5,5))) #col

def on_connect(client, userdata, flags, rc):
    print("(Re)Connected with result code "+str(rc)) 

    # Subscribing in on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    client.subscribe([(info_topic, 0), (image_topic, 0)])

def on_disconnect():
    print("Disconnected from mqtt broker")

print("\n")

print("program running ...")

def get_unsplash_images():
    # probably need try/except since have seen it time out
    if args.search:
        r = requests.get('{}search/photos'.format(unsplash_uri), params={'client_id':unsplash_api_key, 'per_page':40, 'query':args.search}, timeout=5.0)
        z = r.json()['results']
    elif args.name:
        r = requests.get('{}users/{}/photos'.format(unsplash_uri, args.name), params={'client_id':unsplash_api_key, 'per_page':40}, timeout=5.0)
        z = r.json()
    elif args.collection:
        r = requests.get('{}collections/{}/photos'.format(unsplash_uri, args.collection), params={'client_id':unsplash_api_key, 'per_page':40}, timeout=5.0)
        z = r.json()
    else:
        #r = requests.get('{}photos/curated'.format(unsplash_uri), params={'client_id':unsplash_api_key, 'per_page':40})
        r = requests.get('{}collections/{}/photos'.format(unsplash_uri, '543026'), params={'client_id':unsplash_api_key, 'per_page':40}, timeout=5.0)
        z = r.json()

    return [{'url':x['links']['download'], 'photographer':x['user']['name']} for x in z]

def display_background_image(photo):

    try:
        response = requests.get(photo['url'], timeout=5.0)
    except Exception as e:
        print("response = requests.get(url) generated exception:", e)
        return

    try:
        img = wand.image.Image(file=BytesIO(response.content))
    except Exception as e:
        print("img = wand.image.Image(file=BytesIO(response.content)) generated exception:", e)
        if "Insufficient memory" in repr(e):
            sys.exit("Insufficient memory -- line 104")
        else:
            return

    img.transform(resize="{}x{}^".format(screen_width, screen_height)) #fits whether original smaller or bigger; ? can accept gravity='center'
    conv_img = img.convert('bmp')
    # need to close image or there is a memory leak
    # could do: with img.convert('bmp') as converted; converted.save(f)
    img.close()

    f = BytesIO()
    try:
        conv_img.save(f)
    except Exception as e:
        print("image.save(f) with error:", e)
        return

    # need to close image or there is a memory leak - could do with ... (see above)
    conv_img.close()

    f.seek(0)

    try:
        img = pygame.image.load(f).convert()
    except pygame.error as e:
        print(e)
        return

    f.close()
    img_rect = img.get_rect()
    pos = ((screen_width-img_rect.width)/2, 0)

    font = pygame.font.SysFont('notosans', 24)
    font.set_bold(True)

    text = font.render(photo.get('photographer', 'unknown'), True, (127,127,127))

    screen.blit(img, pos)      
    screen.blit(text, (0,0))

    t = datetime.now().strftime("%I:%M %p") #%I:%M:%S %p
    t = t[1:] if t[0] == '0' else t
    t = t[:-2] + t[-2:].lower()
    font = pygame.font.SysFont('notosans', 16)
    font.set_bold(False)
    text = font.render(t, True, (127,127,127))
    screen.blit(text, (screen_width-text.get_rect().width-5,5)) 

    pygame.display.flip()

    # create background image surface without any boxes drawn on it
    screen_image.blit(screen, (0,0))

    del positions[:]
    del foos[:]
    del sizes[:]
    del timing[:]

    for i in range(NUM_BOXES):
        positions.append((0,0))
        foos.append(pygame.Surface((0,0)))
        sizes.append((0,0))
        timing.append(0)

def display_image(x):

    print(x)
    try:
        response = requests.get(x, timeout=5.0)
    except Exception as e:
        print("response = requests.get(url) generated exception: ", e)
        # in some future better world may indicate that the image was bad

        return
    else:     
        try:
            img = wand.image.Image(file=BytesIO(response.content))
        except Exception as e:
            print("img = wand.image.Image(file=BytesIO(response.content)) generated exception from url:", x, "Exception:", e)
            # in some future better world may indicate that the image was bad

            return

    try:
        ww = img.width
        hh = img.height
        sq = ww if ww <= hh else hh
        t = ((ww-sq)//2,(hh-sq)//2,(ww+sq)//2,(hh+sq)//2) 
        img.crop(*t)
        # resize should take the image and enlarge it without cropping so will fill vertical but leave space for lyrics
        #img.resize(screen_height,screen_height)
        img.resize(400,400)
        conv_img = img.convert('bmp')
        img.close()
    except Exception as e:
        print("img.transfrom or img.convert error:", e)
        # in some future better world may indicate that the image was bad

        return

    f = BytesIO()
    try:
        conv_img.save(f)
        conv_img.close()
    except wand.exceptions.OptionError as e:
        print("Problem saving image:",e)
        # in some future better world may indicate that the image was bad

        return

    f.seek(0)
    img = pygame.image.load(f, 'bmp').convert()
    f.close()
    img_rect = img.get_rect()

    print("img_rect =", img_rect)

    foo = pygame.Surface((400,400)) # (800,800) someday will make this something that you pass with the image
    foo.fill((0,0,0))
    foo.set_alpha(175) #125
    
    foo.blit(img, (0,0))      

    return foo

# area used to figure out when there is a collision how much area overlapped
def area(a, b):
    dx = min(a[1][0], b[1][0])- max(a[0][0], b[0][0])
    dy = min(a[1][1], b[1][1]) - max(a[0][1], b[0][1])
    #if dx >= 0 and dy >= 0: # shouldn't need this since only checking if there was a collision
    return dx*dy

#phrases = [(u'{}', u'the holy grail '), (u'{blue}', u' is very nice '), (u'{red}', u' is it?')]
def get_phrases(line, start='{}'):

    if line.find('{') == -1:
        #print("phrases =", [(start, line)])
        return [(start, line)]

    if line[0]!='{':
        line = start+line

    line = line+'{}'

    z = re.finditer(r'{(.*?)}', line)
    s = [[m.group(), m.span()] for m in z]
    #print(s)
    if not s:
        return [('{}', line)]
    phrases = []
    for j in range(len(s)-1):
        phrases.append((s[j][0],line[s[j][1][1]:s[j+1][1][0]]))
    print("phrases =", phrases)
    return phrases

def on_message(client, userdata, msg):
    # {"pos":7, "uri":"https://s-media-cache-ak0.pinimg.com/originals/cb/e8/9d/cbe89da159842dd218ec722082ab50c5.jpg", "header":"Neil Young"}
    # {"pos":4, "header":"Wall Street Journal", "text":"["The rain in spain falls mainly on the plain", "I am a yankee doodle dandy"]}
    topic = msg.topic
    body = msg.payload
    print(topic+": "+str(body))

    try:
        z = json.loads(body)
    except Exception as e:
        print("error reading the mqtt message body: ", e)
        return

    #if topic in (info_topic, image_topic):

    new_screen = pygame.Surface.copy(screen_image) # screen image is the clean background image
    k = z.get('pos', 0)

    # because of changes this erases the whole screen until the next box is drawn
    if z.get('erase'):

        for i in sorted(range(len(timing)), key=lambda t:timing[t]):
            # paint a copy of the current screen except for the box that is moving/being updated
            if i==k:
                continue

            new_screen.blit(foos[i], positions[i], ((0,0), sizes[i])) 

        screen.blit(new_screen, (0,0)) 
        pygame.display.flip() 

        positions[k] = (0,0) 
        foos[k] = pygame.Surface((0,0)) 
        sizes[k] = (0,0)
        timing[k] = 0

        return

    col = z.get('color', next(color))
    dest = LAYOUT[k].get('location')
    dest = dest if dest else  z.get('dest')

    if topic==info_topic:

        #foo is the surface that we 'paint' the text and rectangles on
        #foo = pygame.Surface((MAX_WIDTH,MAX_HEIGHT)) # (800,800)
        foo = pygame.Surface((MAX_WIDTH,LAYOUT[k]['height'])) # (800,800)
        foo.fill((0,0,0))
        foo.set_alpha(175) #125
        #font = pygame.font.SysFont('Sans', 16) #18 changed 05212017
        font = pygame.font.SysFont('notosans', 16) #18 changed 05212017
        font.set_bold(True)
        header = "{} [{}] {}".format(z.get('header', 'no source'), k, dest if dest else " ") # problem if dest None would like to know what it was
        text = font.render(header, True, col)
        foo.blit(text, (5,5)) 
        font.set_bold(False)
        font_size = z.get('font size', 16)
        font_type = z.get('font type', 'notosans')
        if font_type=='monospace':
            font_type = 'notosansmono'
        antialias = z.get('antialias', True)
        bullets = z.get('bullets', True)
        font = pygame.font.SysFont(font_type, font_size)
        line_height = font.get_linesize()
        print("line_height =",line_height)

        line_widths = [0] # for situation when text = [''] otherwise line_widths = [] and can't do max

        n = line_height #20
        for item in z.get('text',['No text']): 
            if not item.strip():
                n+=line_height
                continue
            font.set_bold(False)
            max_chars_line = 66        
            indent = 17
            n+=4 if bullets else 0 # makes multi-line bullets more separated from prev and next bullet

            #if n+line_height > MAX_HEIGHT:
            if n+line_height > LAYOUT[k]['height']:
                break

            if item[0] == '#':
                item=item[1:]
                font.set_bold(True)
                max_chars_line = 60

            if item[0] == '*': 
                foo.blit(star, (2,n+7))
                item=item[1:]
            elif bullets:
                foo.blit(bullet_surface, (7,n+13)) #(4,n+13)
            # neither a star in front of item or a bullet
            else:
                max_chars_line+= 1 
                indent = 10

            lines = textwrap.wrap(item, max_chars_line) # if line is just whitespace it returns []

            for l,line in enumerate(lines):

                #if n+line_height > MAX_HEIGHT: #20
                if n+line_height > LAYOUT[k]['height']: #20
                    break

                if l:
                    phrases = get_phrases(line, phrase[0])
                else:
                    phrases = get_phrases(line)

                xx = 0
                for phrase in phrases:
                    try:
                        text = font.render(phrase[1], antialias, color_map.get(phrase[0], (255,255,255))) 
                    except UnicodeError as e:
                        print("UnicodeError in text lines: ", e)
                        continue
                    foo.blit(text, (indent + xx,n+5))
                    xx+=text.get_rect().width

                line_widths.append(xx)
                n+=line_height

        # determine the size of the rectangle for foo and its line border
        max_line = max(line_widths)
        if max_line > MAX_WIDTH:
            max_line = MAX_WIDTH
        elif max_line < MIN_WIDTH:
            max_line = MIN_WIDTH

        # item is the last item and if the last item is white space n gets incremented unnecessarily and this 'un'increments it
        if not item.strip():
            n-=line_height
        #height = min(n+12, MAX_HEIGHT)
        height = min(n+12, LAYOUT[k]['height'])
        new_size = (max_line+18,height)
        pygame.draw.rect(foo, col, ((0,0), new_size), 3)

        # put time in upper right of box
        t = datetime.now().strftime("%I:%M %p")
        t = t[1:] if t[0] == '0' else t
        t = t[:-2] + t[-2:].lower()
        text = pygame.font.SysFont('Sans', 18).render(t, True, col)
        foo.blit(text, (new_size[0]-text.get_rect().width-5,5)) 

    elif topic==image_topic: 

        uri = z.get('uri')
        if not uri:
            return
        foo = display_image(uri)
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

    foos[k] = foo 
    sizes[k] = new_size 
    timing[k] = time()
    # Need to repaint in the right order so boxes arranged correctly from front to back
    order = sorted(range(len(timing)), key=lambda t:timing[t])

    if dest:
        # negative coordinates are subtracted from the screen_width/height
        x,y = dest
        x = x if x > 0 else screen_width + x
        y = y if y > 0 else screen_height + y
        positions[k] = (x,y)
    else: # need to find a location and since it's moving do the animation
        attempts = 0
        collision_hx = []
        print("k =", k)
        while attempts < 10: #20
            new_pos = (random.randint(50,screen_width-new_size[0]), random.randint(50,screen_height-new_size[1]))
            rect = pygame.Rect((new_pos, new_size))    
            rectlist = [pygame.Rect(a,b) for a,b in zip([positions[j] for j in range(len(positions)) if j!=k], [sizes[i] for i in range(len(positions)) if i!=k])]
            print(rectlist)
            collisions = rect.collidelistall(rectlist)
            if not collisions:
                print("No collision")
                break
            else:
                print("Collision: new rectangle position collides with existing boxes: ", new_pos)
                collision_hx.append((new_pos, collisions)) 

            attempts+=1

        else:
            print("Couldn't find a clear area for box")
            print("collision_hx =", collision_hx)
            collision_areas = []
            for new_pos, collisions in collision_hx:
                overlap = 0
                new_xy = tuple(map(sum, zip(new_pos, new_size)))
                for j in collisions:
                    idx = j if j < k else j+1 
                    xy = tuple(map(sum, zip(positions[idx], sizes[idx])))
                    overlap += area((new_pos, new_xy), (positions[idx], xy)) 

                collision_areas.append((new_pos,overlap))   
            
            print("collision_areas =",collision_areas)
            new_pos, min_area = min(collision_areas, key=lambda x:x[1])
            if min_area < 0:
                raise ValueError("min_area should not be less than 0")
            print("new_pos =", new_pos)
            print("min_area =", min_area)
                

        blast_y = 0 if new_pos[1]+new_size[1]/2 > screen_height/2 else screen_height
        blast_x = random.randint(0,screen_width)
        blast_point = (blast_x,blast_y)

        pygame.draw.line(new_screen, col, new_pos, blast_point) 
        pygame.draw.line(new_screen, col, (new_pos[0],new_pos[1]+new_size[1]), blast_point) 
        pygame.draw.line(new_screen, col, (new_pos[0]+new_size[0],new_pos[1]), blast_point) 
        pygame.draw.line(new_screen, col, (new_pos[0]+new_size[0],new_pos[1]+new_size[1]), blast_point) 
        pygame.draw.rect(new_screen, col, (new_pos, new_size), 3)

        positions[k] = new_pos


        # here painting the boxes on top of the rays but don't worry about always on top
        for i in order:
            new_screen.blit(foos[i], positions[i], ((0,0), sizes[i])) 


        screen.blit(new_screen, (0,0)) 
        pygame.display.flip()
        sleep(2) 

    # here painting the new screen (will overwrite rays if they were drawn because no designated dest
    new_screen = pygame.Surface.copy(screen_image) # screen image is the clean background image

    for i in order:
        if i in on_top:
            continue
        new_screen.blit(foos[i], positions[i], ((0,0), sizes[i])) 

    for i in on_top:
        new_screen.blit(foos[i], positions[i], ((0,0), sizes[i])) 

    screen.blit(new_screen, (0,0)) 
    pygame.display.flip() 

    return

photos = get_unsplash_images()

L = len(photos)
print("Number of photos = {}".format(L))
if not photos:
    sys.exit("No photos")

screen.fill((0,0,0)) 
pygame.display.flip()

photo = random.choice(photos)
print("Next photo is:", photo.get('photographer', '').encode('ascii', errors='ignore'), photo.get('text','').encode('ascii', errors='ignore'))
display_background_image(photo)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(aws_mqtt_uri, 1883, 60)

prev_artist_track = None
t0 = time()
while 1:
    #pygame.event.get() or .poll() -- necessary to keep pygame window from going to sleep
    event = pygame.event.poll()
    
    if event.type == pygame.NOEVENT: 
        pass # appears necessary to check this although not sure why
    elif event.type == pygame.QUIT:
        sys.exit(0)

    #not calling client.loop_forever() but explicitly calling client.loop() below
    client.loop(timeout = 1.0)

    if time() - t0 > 3600: # picture flips each hour
        photo = random.choice(photos)
        print("Next photo is:", photo.get('photographer', '').encode('ascii', errors='ignore'), photo.get('text','').encode('ascii', errors='ignore'))
        display_background_image(photo)
        # shouldn't have to do this but I seem to be losing connection to mqtt broker
        # and this seems to be working
        client.disconnect()
        client.reconnect()

        t0 = time()

    sleep(1)
