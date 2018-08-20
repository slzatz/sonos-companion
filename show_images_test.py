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
from artist_images_db import *
import random

def display_image(x):

    img_link = x.link
    print(img_link)
    try:
        response = requests.get(img_link, timeout=5.0)
    except Exception as e:
        print("response = requests.get(url) generated exception: ", e)
        x.ok = False
        session.commit()
        print(f"{img_link} ok set to False")
        return

    print(f"status code = {response.status_code}")
    #if response.status_code in (403,404, 503):
    if response.status_code != 200:
        print(f"{img_link} returned a {response.status_code}")
        x.ok = False
        session.commit()
        print(f"{img_link} ok set to False")
        return
        
    try:
        img = wand.image.Image(file=BytesIO(response.content))
    except Exception as e:
        print("img = wand.image.Image(file=BytesIO(response.content))"\
              "generated exception from url:", x, "Exception:", e)
        # in some future better world may indicate that the image was bad
        print(f"{img_link} is bad")
        x.ok = False
        session.commit()
        print(f"{img_link} ok set to False")
        return

    try:
        ww = img.width
        hh = img.height
        sq = ww if ww <= hh else hh
        t = ((ww-sq)//2,(hh-sq)//2,(ww+sq)//2,(hh+sq)//2) 
        img.crop(*t)
        # resize should take the image and enlarge it without cropping 
        img.resize(800,800) #400x400
    except Exception as e:
        print("image crop or resize error ", e)
        x.ok = False
        session.commit()
        print(f"{img_link} ok set to False")
        return

    try:
        img.save(filename = "images/zzzz")
        img.close()
    except Exception as e:
        print("img.save or img.close error:", e)
        print(f"{img_link} is bad")
        x.ok = False
        session.commit()
        print(f"{img_link} ok set to False")
        #return

ok_images = []
while 1:
    if ok_images:
        image = ok_images.pop()
        display_image(image)
    else:
        rand = random.randrange(0, session.query(Artist).count()) 
        artist = session.query(Artist).get(rand)
        print(artist.name)
        images = artist.images
        ok_images = [im for im in images if im.ok] 
        if len(ok_images) < 8:
            # find new uris
            print(f"{artist.name} has less than 8 images")
            # need to delete the bad ones and get new ones
        
    time.sleep(5)
