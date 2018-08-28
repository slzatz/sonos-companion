#!bin/python
'''
python3 script: displays infoboxes with key determing which box is displayed
See below for mapping from pos (int) to topic of infobox
'''

#from config import aws_mqtt_uri 
#import paho.mqtt.client as mqtt
#import json
import time
import wand.image
import requests
from io import BytesIO
from apiclient import discovery #google custom search api
import httplib2 #needed by the google custom search engine module apiclient
from config import google_api_key
from artist_images_db import *
#from artists import artists
from sonos_config import ARTISTS as artists
import random

num_artists = session.query(Artist).count()

def display_image(image):
    '''image = sqlalchemy image object'''
    print(image.link)
    try:
        response = requests.get(image.link, timeout=5.0)
    #except Exception as e:
    except (requests.exceptions.ConnectionError,
            requests.exceptions.TooManyRedirects,
            requests.exceptions.ReadTimeout) as e:

        print(f"requests.get({image.link}) generated exception:\n{e}")
        image.ok = False
        session.commit()
        print(f"{image.link} ok set to False")
        return

    print(f"status code = {response.status_code}")
    print(f"encoding = {response.encoding}")
    print(f"is ascii = {response.content.isascii()}")
    if response.status_code != 200:
        print(f"{image.link} returned a {response.status_code}")
        image.ok = False
        session.commit()
        print(f"{image.link} ok set to False")
        return
        
    # it is possible to have encoding == None and ascii == True
    if response.encoding or response.content.isascii():
        print(f"{image.link} returned ascii={response.content.isascii()} "\
              f"and encoding={response.encoding} and is not an image")
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
    t = ((ww-sq)//2,(hh-sq)//2,(ww+sq)//2,(hh+sq)//2) 
    img.crop(*t)
    # resize should take the image and enlarge it without cropping 
    img.resize(800,800) #400x400
    img.save(filename = "images/zzzz")
    img.close()

def get_artist_images(artist):

    print(f"**************Google Custom Search Engine Request for {artist.name} **************")
    http = httplib2.Http()
    service = discovery.build('customsearch', 'v1',  developerKey=google_api_key, http=http)
    z = service.cse().list(q=artist.name, searchType='image', imgType='face',
                           imgSize='xlarge', num=10, 
                           cx='007924195092800608279:0o2y8a3v-kw').execute() 


    # must delete images before you can add new whole new set of images
    session.query(Image).filter_by(artist_id=artist.id).delete()
    session.commit()

    images = []

    #['items']: # only empty search should be on artist='' 
    # and I think I am catching that but this makes sure
    for data in z.get('items', []): 
        image=Image()
        image.link = data['link']
        image.width = data['image']['width']
        image.height = data['image']['height']
        image.ok = True
        images.append(image)

    artist.images = images
    session.commit()
            
    #print("images = ", images)
    #return images 
    artists.append(artist.name)

images = []
while 1:
    if images:
        display_image(images.pop())
    else:
        if artists:
            name = artists.pop()
            artist = session.query(Artist).filter(func.lower(Artist.name)==name.lower()).one()
        else:
            rand = random.randrange(0, num_artists) 
            artist = session.query(Artist).get(rand)
            if not artist:
                continue

        print(artist.name)
        images = [im for im in artist.images if im.ok] 
        if len(images) < 8:
            # find new uris
            print(f"{artist.name} has less than 8 images")
            # need to delete the bad ones and get new ones
            get_artist_images(artist)
        
    time.sleep(10)
