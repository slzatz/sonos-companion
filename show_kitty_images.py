#!bin/python
'''
python3 script: places images in sonos-companion/images 
then open image for display on kitty terminal
should not have to save the image to disk

'''
import paho.mqtt.client as mqtt
import json
import time
import threading
from apiclient import discovery #google custom search api
import httplib2 #needed by the google custom search engine module apiclient
from config import aws_mqtt_uri, google_api_key
from artist_images_db import *
from show_png_jpg import display_image

# keep the postgres session alive
def check():
    while 1:
        c = session.connection() 
        try:
            c.execute("select 1")
        except (sqla_exc.ResourceClosedError, sqla_exc.StatementError) as e:
            print(f"{datetime.datetime.now()} - {e}")
        time.sleep(500)


def get_artist_images(name):
    print(f"**************Google Custom Search Engine Request for {name} **************")
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
    # connection and reconnect then subscriptions will be renewed
    client.subscribe([(sonos_track_topic, 0)])

def on_disconnect():
    print("Disconnected from mqtt broker")

def on_message(client, userdata, msg):
    global new_track_info
    topic = msg.topic
    body = msg.payload
    #print(topic+": "+str(body))

    try:
        z = json.loads(body)
    except Exception as e:
        print("error reading the mqtt message body: ", e)
        return

    #print("z = json.loads(body) =",z)

    artist = z.get("artist", "")
    track_title = z.get("title", "")

    #print("artist =",artist)
    #print("track_title =",track_title)

    try:
        a = session.query(Artist).filter(func.lower(Artist.name)==artist.lower()).one()
    except NoResultFound:
        # must be new artist so get images
        images = get_artist_images(artist)
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

if __name__ == "__main__":

    th = threading.Thread(target=check, daemon=True)
    th.start()
    trackinfo = {"artist":None, "track_title":None, "lyrics":None, "images":[]}
    new_track_info = False

    with open('location') as f:
        location = f.read().strip()

    sonos_track_topic = "sonos/{}/track".format(location)

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
                image = images.pop()
                display_image(image.link, 600, 600)
                print(f"\n{trackinfo['artist']}: {trackinfo['track_title']}\n{image.link}")
                t0 = time.time()
        else:
            images = trackinfo["images"][::]
        time.sleep(.1)


