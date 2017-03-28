'''
python3
This script gathers information about things like weather and tides using Web apis
and then sends that information in an mqtt message with topic "esp_tft" 
The format is {"header":"Tides", "text":"The next high tide is ...", "pos":2}
pos is the position on the tft screen and is 0, 1, 2 etc
Information may be tides, stock prices, news, weather
The mqtt message is picked up by the esp8266 + feather tft
The script is esp_display_info.py
Schedule.every().hour.at(':00').do(job)
https://www.worldtides.info/api?extremes&lat=41.117597&lon=-73.407897&key=a417...
Documentation at https://www.worldtides.info/apidocs
Need to use the following for To Dos and Facts
'''
import os
import sys
home = os.path.split(os.getcwd())[0]
#sys.path = [os.path.join(home, 'twitter')] + sys.path
sys.path =  sys.path + [os.path.join(home,'sqlalchemy','lib')] 
from operator import itemgetter
from itertools import cycle
import paho.mqtt.publish as mqtt_publish
import paho.mqtt.client as mqtt
import json
from time import time,sleep
from config import aws_mqtt_uri, google_api_key
from functools import partial
from artist_images_db import *
from apiclient import discovery #google custom search api
import httplib2 #needed by the google custom search engine module apiclient

with open('location') as f:
    location = f.read().strip()
sonos_topic = "sonos/{}/current_track".format(location)

pub_topic = 'images'
publish = partial(mqtt_publish.single, pub_topic, hostname=aws_mqtt_uri, retain=False, port=1883, keepalive=60)
trackinfo = {"artist":None, "track_title":None}
prev_artist_track = None

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

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    client.subscribe([(sonos_topic, 0)])

def on_message(client, userdata, msg):

    topic = msg.topic
    body = msg.payload
    print(topic+": "+str(body))

    try:
        z = json.loads(body)
    except Exception as e:
        print "error reading the mqtt message body: ", e
        return

    print "z = json.loads(body) =",z
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

t1 = t0 = time()
while 1:

    client.loop()

    cur_time = time()

    if cur_time - t0 > 300:
        try:
            alive = session.query(session.query(Artist).exists()).all()
        except Exception as e:
             print "Exception checking if db alive: ", e
        else:
            if alive[0][0]:
                print cur_time, "The connection to Artsit db is alive"
            else:
                print cur_time, "There is a problem with the Artist db connection"

        t0 = time()

    artist = trackinfo['artist']
    track = trackinfo['track_title']

    if not artist:
        sleep(1)
        continue

    artist_track = "{} - {}".format(artist,track)

    if prev_artist_track != artist_track:

        prev_artist_track = artist_track

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

            uris = [image.link for image in images if image.ok]

        if len(images) < 8:
            print "fewer than 8 images so getting new set of images for artist"
            images = get_artist_images(artist)
            uris = [image.link for image in images if image.ok]
            if not images:
                print "Could not find images for {}".format(artist)
                continue

        uri = cycle(uris)

        t1 = 0

    if cur_time - t1 < 15:
        continue

    if not uris:
        continue

    #{"pos":7, "uri":"https://s-media-cache-ak0.pinimg.com/originals/cb/e8/9d/cbe89da159842dd218ec722082ab50c5.jpg"}
    data = {"header":artist, "uri":next(uri), "pos":7} #expects a list
    print data
    publish(payload=json.dumps(data))

    t1 = time()
    print t1

    sleep(1)
