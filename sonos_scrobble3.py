#!bin/python

'''
Latest script to scrobble songs playing on Sonos to mqtt broker: 
current broker is mosquitto running on linode instance

current_track = master.get_current_track_info() --> {
            u'album': 'We Walked In Song', 
            u'artist': 'The Innocence Mission', 
            u'title': 'My Sisters Return From Ireland', 
            u'uri': 'pndrradio-http://audio-sv5-t3-1.pandora.com/access/5459257820921908950?version=4&lid=86206018&token=...', 
            u'playlist_position': '3', 
            u'duration': '0:02:45', 
            u'position': '0:02:38', 
            u'album_art': 'http://cont-ch1-2.pandora.com/images/public/amz/3/2/9/3/655037093923_500W_500H.jpg'}
'''

import os
from time import sleep
import json
import sys
from ipaddress import ip_address
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + sys.path
import soco
from soco.discovery import by_name
import paho.mqtt.publish as mqtt_publish
from config import mqtt_broker, speaker

topic = 'sonos/current_track'
print("topic =",topic)

topic2 = 'sonos/volume'
print("topic2 =",topic2)

master = by_name(speaker)

print("\nprogram running ...")

prev_title = ''
prev_volume = -1
track = {}

while 1:
    
    # get the current state to see if Sonos is actually playing
    try:
        state = master.get_current_transport_info()['current_transport_state']
    except Exception as e:
        print(f"Encountered error in state = master.get_current_transport_info(): {e}")
        state = 'ERROR'

    # check if sonos is playing music
    if state == 'PLAYING':
        cur_volume = master.volume
        if cur_volume != prev_volume:
            try:
                mqtt_publish.single(topic2, cur_volume, hostname=mqtt_broker, retain=False, port=1883, keepalive=60)
            except Exception as e:
                print(f"Exception trying to publish to mqtt broker: {e}")
            else:
                print(f"volume {cur_volume} sent successfully to mqtt broker")

            prev_volume = cur_volume

        # get track info to see if track has changed
        try:
            track = master.get_current_track_info()
        except Exception as e:
            print("Encountered error in track = master.get_current_track_info(): {e}")
            continue

    cur_title = track.get('title', '')
    
    if cur_title != prev_title:

        data = {'Artist':track.get('artist', ''), 'Title':cur_title}
        try:
            mqtt_publish.single(topic, json.dumps(data), hostname=mqtt_broker, retain=False, port=1883, keepalive=60)
        except Exception as e:
            print(f"Exception trying to publish to mqtt broker: {e}")
        else:
            print(f"{json.dumps(data)} sent successfully to mqtt broker")

        prev_title = cur_title


    sleep(0.5)

