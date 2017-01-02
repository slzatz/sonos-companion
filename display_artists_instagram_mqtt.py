import platform
import os
import pygame
from time import time, sleep
import random
import requests
import textwrap
import sys
from cStringIO import StringIO
import wand.image
from config import mqtt_uris, google_api_key, instagram_client_id, instagram_access_token 
import json
import paho.mqtt.client as mqtt
from artist_images_db import *
from apiclient import discovery #google custom search api
import httplib2 #needed by the google custom search engine module apiclient

#https://api.instagram.com/v1/users/search?q=brahmino&access_token=2.........
instagram_base_url =  "https://api.instagram.com/v1/users/{}/media/recent/"

with open('location') as f:
    location = f.read().strip()
topic = "sonos/{}/current_track".format(location)
mqtt_uri = mqtt_uris[location]

with open('instagram_ids') as f:
    data = f.read()

#can only show instagrammers who've accepted by app (willie and me)  willie is 265048195
ids = list(int(d.split('#')[0]) for d in data.split() if d.split('#')[0])

wrapper = textwrap.TextWrapper(width=72, replace_whitespace=False)  #instagram

# Environment varialbes for pygame
if platform.system() == 'Windows':
    os.environ['SDL_VIDEODRIVER'] = 'windib'
elif platform.system() == "Linux":
    os.environ['SDL_VIDEODRIVER'] = 'x11' 
    os.environ['SDL_VIDEO_CENTERED'] = '1'
else:
    sys.exit("Currently unsupported hardware/OS")

# Should be (6,0) if pygame inits correctly
r = pygame.init()
print "pygame init",r

if platform.machine()[:3] == 'arm': 
    pygame.mouse.set_visible(False)

if platform.system() == 'Windows':
    screen_width, screen_height = 1000,700
else:
    screen_width, screen_height = pygame.display.Info().current_w, pygame.display.Info().current_h

print "screen width =", screen_width, "; screen height =", screen_height

screen = pygame.display.set_mode((screen_width, screen_height))
screen.fill((0,0,0))

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
    client.subscribe(topic)

print "\n"

print "program running ..."

def get_photos(ids=None, num=40):

    photos = []
    d = divmod(num, 20)
    n = d[0] + 1 if d[1] else d[0]

    for _id in ids:
        max_id = None #need this for payload line which references max_id
        for i in range(n):
            payload = {'client_id':instagram_client_id, 'max_id':max_id} if i else {'client_id':instagram_client_id}
            payload = {}
            payload.update({'access_token':instagram_access_token})

            try:
                r = requests.get(instagram_base_url.format(_id), params=payload)
                z = r.json()['data'] 
                zz = r.json()['pagination']
                #max_id = zz['next_max_id'] #"108...."
                #print(max_id)
            except Exception as e:
                print("Exception in get_photos - request: {} related to id: {} ".format(e, _id))
            else:
                for d in z: 
                    try:
                        if d['type']=='image': #note they have a caption and the caption has text
                            dd = {}
                            dd['url'] = d['images']['standard_resolution']['url']
                            dd['url'] = dd['url'].replace('s640x640', 's1080x1080')
                            dd['text'] = d['caption']['text']
                            dd['photographer'] = d['caption']['from']['full_name']
                    except Exception as e:
                        print("Exception in get_photos - adding indiviual photo {} related to id: {} ".format(e, _id))
                    else:
                        photos.append(dd)

    return photos

def display_image(image):

    try:
        response = requests.get(image['url'])
    except Exception as e:
        print "response = requests.get(url) generated exception:", e
        return

    try:
        img = wand.image.Image(file=StringIO(response.content))
    except Exception as e:
        print "img = wand.image.Image(file=StringIO(response.content)) generated exception:", e
        return

    size = "{}x{}".format(screen_width,screen_height)
    img.transform(resize = size)
    img = img.convert('bmp')
    f = StringIO()

    try:
        img.save(f)
    except Exception as e:
        print "image.save(f) with error:", e
        return

    f.seek(0)

    try:
        img = pygame.image.load(f).convert()
    except pygame.error as e:
        print e
        return

    f.close()
    img_rect = img.get_rect()
    pos = ((screen_width-img_rect.width)/2, 0)
    img.set_alpha(75) # the lower the number the more faded - 75 seems too faded; try 100

    font = pygame.font.SysFont('Sans', 28)
    font.set_bold(True)

    text = font.render("Photographer: "+image.get('photographer', 'No photographer'), True, (255, 0, 0))

    screen.fill((0,0,0)) 
    screen.blit(img, pos)      
    screen.blit(text, (0,0))
    
    txt = image.get('text', 'No title')
    txt = wrapper.fill(txt)
    lines = txt.split('\n')
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

    sleep(3)
    screen.fill((0,0,0)) 
    img.set_alpha(255)
    screen.blit(img, pos)      
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

def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))
    body = msg.payload
    print "mqtt messge body =", body

    try:
        z = json.loads(body)
    except Exception as e:
        print "error reading the mqtt message body: ", e
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
    
images = get_photos(ids)
L = len(images)
print "Number of images = {}".format(L)
if images:
    display_image(random.choice(images))

prev_artist = "No artist"  #this is None so if the song title is the empty string, it's not equal
t1 = time()
nn = 0

def draw_lyrics(lyrics, x_coord):
    print "drawing lyrics"
    font = pygame.font.SysFont('Sans', 16)
    n = 10
    for line in lyrics:
        try:
            text = font.render(line.strip(), True, (255, 0, 0))
        except UnicodeError as e:
            print "UnicodeError in text lines: ", e
        else:
            screen.blit(text, (x_coord,n))
            n+=20
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
    #print "Artist =",artist 
    #print "Track =",track 
    if artist is None or artist == "":
        if images:
            if cur_time - t1 > 15:
                display_image(random.choice(images))
                t1 = time()
        sleep(1)
        continue
    artist_track = "{} - {}".format(artist,track)
    ######################################
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

        #below not necessary to create black background for artist-track
        #surface = pygame.Surface((screen_width,20)) 
        #surface.fill((0,0,0))
        #screen.blit(surface, (0,screen_height-16))

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
    # Don't want to keep displaying same artist forever and at some point links seem to go bad
    if nn > 24:
        trackinfo['artist'] = None


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
        #img.resize(700,700)
        img.resize(screen_height,screen_height)
        img = img.convert('bmp')
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
        img.save(f)
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
