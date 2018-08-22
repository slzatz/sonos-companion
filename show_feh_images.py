#!bin/python
'''
python3 script: places images in sonos-companion/images where feh
in slide show mode can display the single image automatically
feh is launched with feh -R X which causes it to reload every X
seconds.  

This script listens for the trackinfo broadcast by local raspberry
pi to AWS mqtt broker under the topic sonos/{loc}/track
'''

import paho.mqtt.client as mqtt
import json
import time
import threading
import wand.image
import requests
from io import BytesIO
from apiclient import discovery #google custom search api
import httplib2 #needed by the google custom search engine module apiclient
from config import aws_mqtt_uri, google_api_key
from artist_images_db import *

def check():
    while 1:
        c = session.connection() #########
        try:
            c.execute("select 1")
        except (sqla_exc.ResourceClosedError, sqla_exc.StatementError) as e:
            print(f"{datetime.datetime.now()} - {e}")
        time.sleep(500)

th = threading.Thread(target=check, daemon=True)
th.start()
trackinfo = {"artist":None, "track_title":None, "lyrics":None, "images":[]}
new_track_info = False

with open('location') as f:
    location = f.read().strip()

sonos_track_topic = "sonos/{}/track".format(location)

def display_image(image):
    '''image = sqlalchemy image object'''
    print(image.link)
    try:
        response = requests.get(image.link, timeout=5.0)
    except (requests.exceptions.ConnectionError,
            requests.exceptions.TooManyRedirects,
            requests.exceptions.ChunkedEncodingError,
            requests.exceptions.ReadTimeout) as e:
        print(f"requests.get({image.link}) generated exception:\n{e}")
        image.ok = False
        session.commit()
        print(f"{image.link} ok set to False")
        return

    print(f"status code = {response.status_code}")
    if response.status_code != 200:
        print(f"{image.link} returned a {response.status_code}")
        image.ok = False
        session.commit()
        print(f"{image.link} ok set to False")
        return
        
    if response.content.isascii():
        print(f"{image.link} returned ascii text and not an image")
        image.ok = False
        session.commit()
        print(f"{image.link} ok set to False")
        return

    # this try/except is needed for occasional bad/unknown file format
    try:
        img = wand.image.Image(file=BytesIO(response.content))
    except Exception as e:
        print(f"wand.image.Image(file=BytesIO(response.content))"\
              f"generated exception from {image.link} {e}")
        image.ok = False
        session.commit()
        print(f"{image.link} ok set to False")
        return

    ww = img.width
    hh = img.height
    sq = ww if ww <= hh else hh
    if ww > hh:
        t = ((ww-sq)//2,(hh-sq)//2,(ww+sq)//2,(hh+sq)//2) 
    else:
        t= ((ww-sq)//2, 0, (ww+sq)//2, sq)
    img.crop(*t)
    # resize should take the image and enlarge it without cropping 
    img.resize(800,800) #400x400
    img.save(filename = "images/zzzz")
    img.close()

def get_artist_images(name):

    print(f"**************Google Custom Search Engine Request for {name} **************")
    http = httplib2.Http()
    service = discovery.build('customsearch', 'v1',
                              developerKey=google_api_key, http=http)
    z = service.cse().list(q=name, searchType='image', imgType='face',
                           imgSize='xlarge', num=10,
                           cx='007924195092800608279:0o2y8a3v-kw').execute() 

    try:
        a = session.query(Artist).filter(func.lower(Artist.name)==name.lower()).one()
    except NoResultFound:
        print("Don't have that name in db so created it")
        a = Artist()
        a.name = name
        session.add(a)
        session.commit()
    except Exception as e:
        print("a = session.query(Artist).filter(func.lower.. error:", e) 
        return []

    # must delete images before you can add new whole new set of images
    session.query(Image).filter_by(artist_id=a.id).delete()
    session.commit()

    images = []

    for data in z.get('items', []): #['items']: # only empty search should be on artist='' and I think I am catching that but this makes sure
        image=Image()
        image.link = data['link']
        image.width = data['image']['width']
        image.height = data['image']['height']
        image.ok = True
        images.append(image)

    a.images = images
    session.commit()
            
    print("images = ", images)
    return images 

def on_connect(client, userdata, flags, rc):
    print(f"(Re)Connected with result code {rc}") 

    # Subscribing in on_connect() means that if we lose the 
    # connection and reconnect then subscriptions will be renewed.
    client.subscribe([(sonos_track_topic, 0)])
    #client.subscribe([(image_topic, 0)])

def on_disconnect():
    print("Disconnected from mqtt broker")

def on_message(client, userdata, msg):
    global new_track_info
    topic = msg.topic
    body = msg.payload
    print(topic+": "+str(body))

    try:
        z = json.loads(body)
    except Exception as e:
        print("error reading the mqtt message body: ", e)
        return

    print("z = json.loads(body) =",z)

    artist = z.get("artist", "")
    track_title = z.get("title", "")

    print("artist =",artist)
    print("track_title =",track_title)

    try:
        a = session.query(Artist).filter(func.lower(Artist.name)==artist.lower()).one()
    except NoResultFound:
        # must be new artist so get images
        images = get_artist_images(artist)
        #images = []
        if not images:
            print("Could not find images for {}".format(artist))
    except Exception as e:
        print("error trying to find artist:", e)
        images = []
    else:
        images = [im for im in a.images if im.ok]
        if len(images) < 5:
            print("fewer than 5 images so getting new set of images for artist")
            images = get_artist_images(artist)
            if not images:
                print(f"Could not find images for {artist}")

    new_track_info = True
    trackinfo.update({"artist":artist, "track_title":track_title, "images":images})

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(aws_mqtt_uri, 1883, 60)
# brief loop below lets the mqtt client connect to the broker
t0 = time.time()
while time.time() < t0 + 10:
    client.loop(timeout = 1.0)
    time.sleep(1)

images = []
while 1:
    client.loop(timeout = 0.25) #was 1.0
    if new_track_info:
        images = trackinfo["images"][::]
        new_track_info = False
    if images:
        if time.time() > t0 + 10:
            display_image(images.pop())
            t0 = time.time()
    else:
        images = trackinfo["images"][::]
    time.sleep(.1)
