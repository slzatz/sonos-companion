#!bin/python

'''
This script gets artists images and lyrics when sonos is playing
Relies on sonos_track_info3.py for artist and track, which is
currently generally running on a local raspberry pi

location = the sonos system that is being listened to

sonos status, artist images and lyrics are generate mqtt messages
that are listened to by openframeworks retrieve_google_images_N 
which is usually running on intel nuc as well as laptop

mqtt broker running on aws ec2 instance
'''
from itertools import cycle
import paho.mqtt.publish as mqtt_publish
import paho.mqtt.client as mqtt
import json
from time import time,sleep
from config import aws_mqtt_uri, google_api_key
from functools import partial
from artist_images_db import *
from lmdb_p import * 
from apiclient import discovery #google custom search api
import httplib2 #needed by the google custom search engine module apiclient
import requests
from bs4 import BeautifulSoup
from get_lyrics import get_lyrics #uses genius.com
from random import shuffle
import html
import wikipedia
import textwrap

max_chars_line = 50

with open('location') as f:
    location = f.read().strip()

sonos_track_topic = "sonos/{}/track".format(location)
sonos_status_topic = "sonos/{}/status".format(location)
lyric_topic = "display_lyrics2"
sonos_topic = 'display_artist2'
bio_topic = "display_bio"
sonos_status = ['STOPPED']
publish_images = partial(mqtt_publish.single, sonos_topic, hostname=aws_mqtt_uri, retain=False, port=1883, keepalive=60)
publish_lyrics = partial(mqtt_publish.single, lyric_topic, hostname=aws_mqtt_uri, retain=False, port=1883, keepalive=60)
publish_bio = partial(mqtt_publish.single, bio_topic, hostname=aws_mqtt_uri, retain=False, port=1883, keepalive=60)
trackinfo = {"artist":None, "track_title":None} #, "lyrics":None}

tasks = remote_session.query(Task).join(Context).filter(Context.title=='wisdom', Task.star==True, Task.completed==None, Task.deleted==False).all()
shuffle(tasks)

def get_wisdom():
    for task in tasks:
        #text = [f"[{task.context.title.capitalize()}] <bodyBold>{task.title}</bodyBold>"]
        note = html.escape(task.note) if task.note else '' # would be nice to truncate on a word

        print(task.title)

        text = f"<phrases>{task.title}</phrases><br/><bodyItalic>{note}</bodyItalic>"
        yield text

wisdom = get_wisdom() #generator

def get_artist_images(name):

    print(f"**************Google Custom Search Engine Request for for images for {name} **************")
    http = httplib2.Http()
    service = discovery.build('customsearch', 'v1',
                              developerKey=google_api_key, http=http)
    z = service.cse().list(q=name, searchType='image', imgType='face', #alternative type is photo
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
        print(f"a = session.query(Artist).filter(func.lower.. error: {e}") 
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
            
    print(f"images = {images}")
    return images 

def check_image_url(url):
    try:
        response = requests.get(url, timeout=3.0)
    except Exception as e:
        print("response = requests.get(url) generated exception: ", e)
        # in some future better world may indicate that the image was bad
        return False

    if response.headers is None:
        return False

    if response.status_code == 404:
        return False

    if response.headers.get("content-type") is None:
        return False

    if url[-4:] == ".jpg" or url[-4:] == ".png": #added under assumption that if url ends in .jpg that's what it is
        return True

    if not (response.headers.get("content-type").lower() in ['image/jpeg', 'image/png', 'application/octet-stream']):
        print(f"{response.headers.get('content-type').lower()}")
        return False

    return True

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")

    # Subscribing in on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    #client.subscribe([(sonos_topic, 0), (info_topic,0)]) 
    client.subscribe([(sonos_track_topic, 0), (sonos_status_topic, 0)]) 

def on_message(client, userdata, msg):

    topic = msg.topic
    body = msg.payload
    print(f"{topic}: {body}")

    try:
        z = json.loads(body)
    except Exception as e:
        print(f"error reading the mqtt message body: {e}")
        return

    print(f"z = json.loads(body) = {z}")

    if topic == sonos_track_topic:

        artist = z.get("artist", "")
        track_title = z.get("title", "")

        print(f"artist = {artist}")
        print(f"track_title = {track_title}")
        trackinfo.update({"artist":artist, "track_title":track_title})

    elif topic == sonos_status_topic:
        sonos_status[0] = z.get('state')
        print(f"sonos_status[0] = {sonos_status[0]}")

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
n = 0 # factor to slow down wisdom publishing
while 1:

    client.loop()

    artist = trackinfo['artist']
    track = trackinfo['track_title']
    state = sonos_status[0]
    print(f"state: {state}")

    if prev_artist != artist:

        data = {"header":"{} - {}".format(artist.encode('ascii', 'ignore'), track.encode('ascii', 'ignore')), "uri":"searching", "pos":7, "dest":(-410,30), "type":"image"} 
        try:
            publish_images(payload=json.dumps(data))
        except Exception as e:
            print(e)

        data = {"header":f"{artist}-{track}<br/>", "text":f"<bodyItalic>Looking for images of {artist}</bodyItalic>"}
        try:
            publish_lyrics(payload=json.dumps(data))
        except Exception as e:
            print(e)

        prev_artist = artist

        if not artist:
            continue

        print(f"about to query image database for artist: {artist}")

        try:
            a = session.query(Artist).filter(func.lower(Artist.name)==artist.lower()).one()
        except NoResultFound:
            print(f"No images in db for {artist}")
            images = get_artist_images(artist)
            if not images:
                print(f"Could not find images for {artist}")
                continue
        except Exception as e:
            print(f"error trying to find artist: {e}")
            continue
        else:
            images = a.images

        good_images = []
        for image in images:
            # check if image is good
            if check_image_url(image.link):
                good_images.append(image)

        if len(good_images) < 5:
            print(f"Only found {len(good_images)} images for {artist} - getting new images")
            # vetting these new ones but taking whatever is good
            images = get_artist_images(artist)
            if not images:
                print(f"Could not find images for {artist}")
                uris = []
                continue

            good_images = []
            for image in images:
                # check if image is good
                if check_image_url(image.link):
                    good_images.append(image)

        uris = [image.link for image in good_images] 
        uri = cycle(uris)
        data = {"header":f"{artist}-{track}", "uri":next(uri), "type":"image"} 
        print(data)
        try:
            publish_images(payload=json.dumps(data))
        except Exception as e:
            print(e)

        try:
            bio = wikipedia.summary(artist)
        except Exception as e:
            print("wikipedia: " + e)
            bio_wrap = f"Could not retrieve {artist} bio"
        else:
            bio_lines = textwrap.wrap(bio, max_chars_line)
            bio_wrap = "<br/>".join(bio_lines)

        #data = {"header":artist, "text":f"<br/><lyrics>{wikipedia.summary(artist)}</lyrics>"}
        data = {"header":f"{artist}<br/>", "text":bio_wrap}
        publish_bio(payload=json.dumps(data))
        print(wikipedia.summary(artist))

        t1 = time()
        print(t1)
        sonos_status[0] = 'PLAYING' # if we switched the picture and posted lyrics we're playing because there may be a lag in getting state/status info
        sleep(1)
        continue

    if prev_track != track:

        data = {"header":f"{artist}-{track}<br/>", "text":f"Looking for lyrics to {track}"} 
        try:
            publish_lyrics(payload=json.dumps(data))
        except Exception as e:
            print(e)

        prev_track = track

        if not track:
            continue

        lyrics = get_lyrics(artist, track)
   
        if not lyrics:
            # previously was erasing lyrics when no lyrics -- need to revisit 04192019
            data = {"header":f"{artist}-{track}<br/>", "text":f"Could not find the lyrics to {track}"} 
            publish_lyrics(payload=json.dumps(data))
            continue

        data = {"header":f"{artist}<br/>{track}<br/>", "text":lyrics}
        try:
            publish_lyrics(payload=json.dumps(data))
        except Exception as e:
            print(e)
        t1 = time()
        print(t1)
        sonos_status[0] = 'PLAYING' # if we switched the picture and posted lyrics we're playing because there may be a lag in getting state/status info
        sleep(1)
        continue

    if prev_state != state:
        
        prev_state = state

        if state != 'PLAYING':
            if state in ['STOPPED', 'PAUSED_PLAYBACK']:
                # now would want it to send some goldstein quotations 
                data = {"pos":7, "uri":"stopped"}
                try:
                    publish_images(payload=json.dumps(data))
                except Exception as e:
                    print(e)
                sleep(1)

                try:
                    text = next(wisdom)
                except StopIteration:
                    #tasks = remote_session.query(Task).join(Context).filter(Context.title=='wisdom', 
                    #                                                        Task.star==True,
                    #                                                        Task.completed==None,
                    #                                                        Task.deleted==False).all()
                    remote_session.expire_all()
                    shuffle(tasks)
                    wisdom = get_wisdom() # generator
                    text = next(wisdom)

                data = {"pos":8, "text":text, "bullets":False}
                try:
                    publish_lyrics(payload=json.dumps(data))
                except Exception as e:
                    print(e)

            uris = []
            prev_track = None #04192019 
            prev_artist = None #04192019
            trackinfo = {"artist":None, "track_title":None}

            t1 = time()
            print(t1)

            sleep(1)
            continue

    if time() < t1+15:
        sleep(1)
        continue

    if state in ['STOPPED', 'PAUSED_PLAYBACK']:
        if n < 2:
            n += 1
        else:
            try:
                text = next(wisdom)
            except StopIteration:
                #tasks = remote_session.query(Task).join(Context).filter(Context.title=='wisdom', 
                #                                                       Task.star==True,
                #                                                       Task.completed==None,
                #                                                       Task.deleted==False).all()
                remote_session.expire_all()
                shuffle(tasks)
                wisdom = get_wisdom() #generator
                text = next(wisdom)

            data = {"pos":8, "text":text}
            try:
                publish_lyrics(payload=json.dumps(data))
            except Exception as e:
                print(e)
            
            n = 0

    # Right now gets here no matter what state is but STOPPED and PAUSED_PLAYBACK have set uris = 0
    # uris could be empty although doesn't seem likely unless there was a timing issue where they hadn't been populated yet
    # more clear if below was just an else
    #if uris:
    elif uris:
        data = {f"header":f"{artist} - {track}", "uri":next(uri)} 
        print(data)
        try:
            publish_images(payload=json.dumps(data))
        except Exception as e:
            print(e)

    t1 = time()
    print(t1)

    sleep(1)
