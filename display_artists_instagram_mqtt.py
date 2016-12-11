import platform
import os
import pygame
import txtlib # may still use this for weather, lyrics, bio
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
from amazon_music_db import *
from apiclient import discovery #google custom search api
import httplib2 #needed by the google custom search engine module apiclient

#https://api.instagram.com/v1/users/search?q=brahmino&access_token=2.........
#can only show instagrammers who've accepted by app (willie and me)  willie is 265048195
instagram_base_url =  "https://api.instagram.com/v1/users/{}/media/recent/"

with open('location') as f:
    location = f.read().strip()
topic = "sonos/{}/current_track".format(location)
mqtt_uri = mqtt_uris[location]

with open('instagram_ids') as f:
    data = f.read()

ids = list(int(d.split('#')[0]) for d in data.split() if d.split('#')[0])
#ids = [4616106, 17789355, 986542, 230625139, 3399664, 6156112, 1607304, 24078, 277810, 1918184, 197656340, 200147864, 4769265] 

wrapper = textwrap.TextWrapper(width=72, replace_whitespace=False)  #instagram

# Environment varialbes for pygame
if platform.system() == 'Windows':
    os.environ['SDL_VIDEODRIVER'] = 'windib'
elif platform.system() == "Linux":
    os.environ['SDL_VIDEODRIVER'] = 'x11' #note: this works if you launch x (startx) and run terminal requires keyboard/mouse
    os.environ['SDL_VIDEO_CENTERED'] = '1'
else:
    sys.exit("Currently unsupported hardware/OS")

# Should be (6,0) if pygame inits correctly
r = pygame.init()
print "pygame init",r

if platform.machine() == 'armv6l': 
    pygame.mouse.set_visible(False)

if platform.system() == 'Windows':
    w,h = 1000,700
else:
    w, h = pygame.display.Info().current_w, pygame.display.Info().current_h

screen = pygame.display.set_mode((w, h))
screen.fill((0,0,0))

text = txtlib.Text((w, h), 'freesans', font_size=30)
text.text = "Sonos-Companion TFT Edition"
text.update()
screen.blit(text.area, (0,0))
pygame.display.flip()

trackinfo = {"artist":None, "track_title":None}

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    client.subscribe(topic)

print "\n"

print "program running ..."

def get_photos(ids=None, num=40):

    images = []
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
                        images.append(dd)

    return images

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

    size = "{}x{}".format(w,h)
    img.transform(resize = size)
    img = img.convert('bmp')
    f = StringIO()

    try:
        img.save(f)
    except Exception as e:
        print "image.save(f) with error:", e
        return

    f.seek(0)
    img = pygame.image.load(f).convert()
    f.close()
    img_rect = img.get_rect()
    center = ((w-img_rect.width)/2, 0)
    img.set_alpha(75) # the lower the number the more faded - 75 seems too faded; try 100

    font = pygame.font.SysFont('Sans', 28)
    font.set_bold(True)

    text = font.render("Photographer: "+image.get('photographer', 'No photographer'), True, (255, 0, 0))

    screen.fill((0,0,0)) 
    screen.blit(img, center)      
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
    screen.blit(img, center)      
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

    for image in a.images:
        # with change in cascade don on 12-11-2016 may be possible to do a.images = [];session.commit()
        print image.link, image.width, image.height,image.ok
        session.delete(image)
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

    print "on_message:artist =",artist
    print "on_message:track_title =",track_title
    trackinfo.update({"artist":artist, "track_title":track_title})

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(mqtt_uri, 1883, 60)
#not calling client.loop_forever() but explicitly calling client.loop() below
    
images = get_photos(ids)
L = len(images)
print "Number of images = {}".format(L)
if images:
    image = images[random.randrange(0,L-1)]
    display_image(image)

prev_artist = "No artist"  #this is None so if the song title is the empty string, it's not equal
t1 = time()

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
                image = images[random.randrange(0,L-1)]
                display_image(image)
                t1 = time()
        sleep(1)
        continue

    if prev_artist != artist:

        prev_artist = artist

        print "about to query image database for artist", artist

        try:
            a = session.query(Artist).filter(func.lower(Artist.name)==artist.lower()).one()
        except NoResultFound:
            z = get_artist_images(artist)
            if not z:
                print "Could not find images for {}".format(artist)
                continue
        except Exception as e:
            print "error trying to find artist:", e
            continue
        else:
            z = a.images

        if len([i for i in z if i.ok]) < 8:
            print "fewer than 8 images so getting new set of images for artist"
            z = get_artist_images(artist)
            if not z:
                print "Could not find images for {}".format(artist)
                continue

        #random.shuffle(z) - messes up things if you have to update an image with image.ok = False
        z0 = z[:]       
            
        # The below worked fine but just didn't seem as ORM-Pythonic
        #try:
        #    z = session.query(Image).join(Artist).filter(func.lower(Artist.name)==artist.lower()).all()
        #    random.shuffle(z)
        #    z0 = z[:]
        #except Exception as e:
        #    print "session.query(Image).join(Artist).filter(func.lower(Artist.name)==artist.lower() error:", e
        #    z = None

        #if not z:
        #    z = get_artist_images(artist)
        #    if not z:
        #        print "Could not find images for {}".format(artist)
        #        continue

        #    random.shuffle(z)
        #    z0 = z[:]

        t1 = 0

    if cur_time - t1 < 15:
        continue

    if not z:
        continue

    #x = z[random.randrange(0,len(z)-1)]
    if not z0:
        z0 = z[:]
    x = z0.pop()

    # moved farther down so time only moves forward on a good image
    #t1 = time()
    #print t1

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
        img.transform(resize = "{}x{}".format(w,h))
        img = img.convert('bmp')
    except Exception as e:
        print "img.transfrom or img.convert error:", e

        continue

    # moved from above so time only reset when there is really a new image
    t1 = time()
    print t1

    f = StringIO()
    try:
        img.save(f)
    except wand.exceptions.OptionError as e:
        print "Problem saving image:",e
        continue

    f.seek(0)
    img = pygame.image.load(f, 'bmp').convert()
    f.close()
    img_rect = img.get_rect()
    center = ((w-img_rect.width)/2, 0)
    
    screen.fill((0,0,0))
    screen.blit(img, center)      

    line = "{} - {}".format(artist,track)

    font = pygame.font.SysFont('Sans', 14)
    font.set_bold(True)
    text = font.render(line, True, (255,0,0))

    zzz = pygame.Surface((w,20)) 
    zzz.fill((0,0,0))
     
    screen.blit(zzz, (0,h-16))
    screen.blit(text, (0,h-16))

    pygame.display.flip()

    sleep(1)
