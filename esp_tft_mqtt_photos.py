'''
python2
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
import requests
import lxml.html

with open('location') as f:
    location = f.read().strip()

sonos_track_topic = "sonos/{}/track".format(location)
sonos_status_topic = "sonos/{}/status".format(location)
info_topic = "esp_tft"
sonos_status = ['STOPPED']

pub_topic = 'images'
publish_images = partial(mqtt_publish.single, pub_topic, hostname=aws_mqtt_uri, retain=False, port=1883, keepalive=60)
publish_lyrics = partial(mqtt_publish.single, info_topic, hostname=aws_mqtt_uri, retain=False, port=1883, keepalive=60)
trackinfo = {"artist":None, "track_title":None, "lyrics":None}

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

    for data in z.get('items', []): #['items']: # only empty search should be on artist='' and I think I am catching that but this makes sure
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

def get_url(artist, title):

    if artist is None or title is None:
        return None

    payload = {'func': 'getSong', 'artist': artist, 'song': title, 'fmt': 'realjson'}
    
    try:
         r = requests.get("http://lyrics.wikia.com/api.php", params=payload)
    except:
        print "Problem retrieving lyrics"
        url = None
         
    else:        
        q = r.json()
        
        url = q['url'] if 'url' in q else None
        
        if url and url.find("action=edit") != -1: 
            url = None 
            
    return url

def get_lyrics(artist,title):

    if artist is None or title is None:
        print "No artist or title" 
        return None

    print artist, title 
    
    url = get_url(artist, title)
    if not url:
        return None
    
    try:
        doc = lxml.html.parse(url)
    except IOError as e:
        print e
        return None

    try:
        lyricbox = doc.getroot().cssselect(".lyricbox")[0]        
    except IndexError as e:
        print e
        return None

    # look for a sign that it's instrumental
    if len(doc.getroot().cssselect(".lyricbox a[title=\"Instrumental\"]")):
        print "appears to be instrumental"
        return None

    lyrics = []
    if lyricbox.text is not None:
        lyrics.append(lyricbox.text)
    for node in lyricbox:
        if node.tail is not None:
            lyrics.append(node.tail)

    #for line in lyrics:
    #    print line

    return lyrics

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    #client.subscribe([(sonos_topic, 0), (info_topic,0)]) 
    client.subscribe([(sonos_track_topic, 0), (sonos_status_topic, 0)]) 

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

    if topic == sonos_track_topic:

        artist = z.get("artist", "")
        track_title = z.get("title", "")
        #lyrics = z.get("lyrics", "")

        print "artist =",artist
        print "track_title =",track_title
        #trackinfo.update({"artist":artist, "track_title":track_title, "lyrics":lyrics})
        trackinfo.update({"artist":artist, "track_title":track_title})

    elif topic == sonos_status_topic:
        sonos_status[0] = z.get('state')
        print "sonos_status[0] =",sonos_status[0]

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(aws_mqtt_uri, 1883, 60)
#not calling client.loop_forever() but explicitly calling client.loop() below

t1 = t0 = time()
uris = []
prev_artist = None
prev_track = None
prev_state = None
while 1:

    client.loop()

    #if sonos_status[0] == 'PLAYING': # don't think need to have this check here

    artist = trackinfo['artist']
    track = trackinfo['track_title']
    #lyrics = trackinfo['lyrics']
    state = sonos_status[0]

    if prev_artist != artist:
        prev_artist = artist

        if not artist:
            continue

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
            if len(images) < 8:
                print "fewer than 8 images so getting new set of images for artist"
                images = get_artist_images(artist)
                if not images:
                    print "Could not find images for {}".format(artist)
                    uris = []
                    continue

        uris = [image.link for image in images if image.ok] ########### unindented on 4-15-2017
        uri = cycle(uris)

        #{"pos":7, "uri":"https://s-media-cache-ak0.pinimg.com/originals/cb/e8/9d/cbe89da159842dd218ec722082ab50c5.jpg"}
        data = {"header":"{} - {}".format(artist.encode('ascii', 'ignore'), track.encode('ascii', 'ignore')), "uri":next(uri), "pos":7, "dest":(-410,30)} 
        print data
        publish_images(payload=json.dumps(data))
        t1 = time()
        print t1
        sonos_status[0] = 'PLAYING' # if we switched the picture and posted lyrics we're playing because there may be a lag in getting state/status info
        sleep(1)
        continue

    if prev_track != track:
        prev_track = track

        if not track:
            continue

        lyrics = get_lyrics(artist, track)

        if not lyrics:
            data = {"pos":8, "erase":True}
            publish_lyrics(payload=json.dumps(data))
            continue

        data = {"header":track, "text":lyrics, "pos":8, "bullets":False, "font size":14, "dest":(30,30)} #expects a list
        #print data
        publish_lyrics(payload=json.dumps(data))
        t1 = time()
        print t1
        sonos_status[0] = 'PLAYING' # if we switched the picture and posted lyrics we're playing because there may be a lag in getting state/status info
        sleep(1)
        continue

    if prev_state != state:
        
        prev_state = state

        if state != 'PLAYING':
            # erase artist image box and lyrics box
            data = {"pos":7, "erase":True}
            publish_images(payload=json.dumps(data))
            data = {"pos":8, "erase":True}
            publish_lyrics(payload=json.dumps(data))

            uris = []

            t1 = time()
            print t1

            sleep(1)
            continue

    if time() < t1+15:
        sleep(1)
        continue

    # there may be situations in which state is PLAYING but uris have not been obtained yet
    if not uris:
        sleep(1)
        continue

    # only gets here if status is PLAYING
    #{"pos":7, "uri":"https://s-media-cache-ak0.pinimg.com/originals/cb/e8/9d/cbe89da159842dd218ec722082ab50c5.jpg"}
    data = {"header":"{} - {}".format(artist.encode('ascii', 'ignore'), track.encode('ascii', 'ignore')), "uri":next(uri), "pos":7, "dest":(-410,30)} 
    print data
    publish_images(payload=json.dumps(data))

    t1 = time()
    print t1

    sleep(1)
