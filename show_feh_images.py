#!bin/python
'''
python3 script: displays infoboxes with key determing which box is displayed
See below for mapping from pos (int) to topic of infobox
'''

from config import aws_mqtt_uri 
import paho.mqtt.client as mqtt
import json
import time
import wand.image
import requests
from io import BytesIO

image_topic = "images"

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
        img.resize(800,800) #400x400
        #conv_img = img.convert('bmp')
        img.save(filename = "images/zzzz")
        img.close()
    except Exception as e:
        print("img.transfrom or img.convert error:", e)
        # in some future better world may indicate that the image was bad

        return

def on_connect(client, userdata, flags, rc):
    print("(Re)Connected with result code "+str(rc)) 

    # Subscribing in on_connect() means that if we lose the 
    # connection and reconnect then subscriptions will be renewed.
    #client.subscribe([(info_topic, 0)])
    client.subscribe([(image_topic, 0)])

def on_disconnect():
    print("Disconnected from mqtt broker")

def on_message(client, userdata, msg):
    topic = msg.topic
    body = msg.payload
    #print(topic+": "+str(body))

    try:
        z = json.loads(body)
    except Exception as e:
        print("error reading the mqtt message body: ", e)
        return

    uri = z.get('uri')
    display_image(uri)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(aws_mqtt_uri, 1883, 60)
# brief loop below lets the mqtt client connect to the broker
t0 = time.time()
while time.time() < t0 + 10:
    client.loop(timeout = 1.0)
    time.sleep(1)

while 1:
    client.loop(timeout = 0.25) #was 1.0
    time.sleep(.1)
