#!bin/python
'''
Python 3.x version of sonos_track_info.py
Broadcasts messages via mqtt information about tracks that sonos is playing
Various scripts/devices subscribe to the messages including sonos_remote running on M5
as well as display_info_photos.py and dash_sonos.py
Currently uses the mqtt brokder running on my ec2 instance

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
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + sys.path
from config import location, aws_mqtt_uri
import soco
from soco import config as soco_config
import paho.mqtt.publish as mqtt_publish

print(f"The current location is {location}") 

sonos_track_topic = f'sonos/{location}/track'
print("sonos_track_topic =", sonos_track_topic)

sonos_status_topic = f'sonos/{location}/status'
print("sonos_status_topic =", sonos_status_topic)

sonos_volume_topic = f'sonos/{location}/volume'
print("sonos_volume_topic =", sonos_volume_topic)

soco_config.CACHE_ENABLED = False

n = 0
sp = None
while n < 10:
    n+=1
    print("attempt "+str(n)) 
    try:
        sp = list(soco.discover(timeout=2))
    except TypeError as e:    
        print(e) 
        sleep(1)       
    else:
        break 

if not sp:
    print("Could not discover the speakers")
    sys.exit()

text = [f"{s.player_name} <-- {s.group.coordinator.player_name}" for s in sp]

for idx, line in enumerate(text):
    print('  %2d. %s' % (idx + 1, line))

while True:
    response = input("Which speaker do you want to become the master speaker? ")

    try:
        response = int(response)
        master = sp[response - 1]
        break
    except (ValueError, IndexError):
        print("{!r} isn't a valid choice. Pick a number between 1 and {}:\n".format(response,
      len(text)))

print("Master speaker is: {}".format(master.player_name))

print("\nprogram running ...")

prev_title = ''
prev_volume = -1
prev_state = ''
track = {}

while 1:
    
    # get the current state to see if Sonos is actually playing
    try:
        state = master.get_current_transport_info()['current_transport_state']
    except Exception as e:
        print("Encountered error in state = master.get_current_transport_info(): ", e)
        state = 'ERROR'
        sleep(1)
        continue

    if prev_state != state:
        try:
            volume = master.volume
        except Exception as e:
            print("volume = master.volume error", e)
            volume = -1

        data = {'header':'Sonos Status - '+location, 'text':["state: "+state, "volume: "+str(volume)], 'pos':10}
        try:
            mqtt_publish.single('esp_tft', json.dumps(data), hostname=aws_mqtt_uri, retain=False, port=1883, keepalive=60)

            # at least one of the listeners for the below is esp_tft_mqtt_photos.py
            mqtt_publish.single(sonos_status_topic, json.dumps({'state':state}), hostname=aws_mqtt_uri, retain=False, port=1883, keepalive=60)
        except Exception as e:
            print("Encountered error in mqtt_publish_single ...", e)

        prev_state = state

    try:
        volume = master.volume
    
    #except requests.exceptions.ConnectionError as e: # requests not actually imported must be by SoCo
    except Exception as e:
        print("volume = master.volume error:", e)
        volume =-1

    else:
        if volume != prev_volume:
            data = {'header':'Sonos Status - '+location, 'text':["state: "+state, "volume: "+str(volume)], 'pos':10}
            mqtt_publish.single('esp_tft', json.dumps(data), hostname=aws_mqtt_uri, retain=False, port=1883, keepalive=60)

            prev_volume = volume

    # check if sonos is playing music

    if state == 'PLAYING':

        try:
            track = master.get_current_track_info()
        except Exception as e:
            print("Encountered error in track = master.get_current_track_info(): ", e)
            sleep(1)
            continue

    title = track.get('title', '')
    
    if prev_title != title:

        artist = track.get('artist', '')
        # Below is for esp_tft_mqtt_photos but not intended for display_info_photos.py
        # publishing track info to box 9
        data = {'artist':artist, 'title':title}
        mqtt_publish.single(sonos_track_topic, json.dumps(data), hostname=aws_mqtt_uri, retain=False, port=1883, keepalive=60)

        # this is for display_info_photos
        data = {'header':'Track Info - '+location, 'text':[artist, title], 'pos':9}
        mqtt_publish.single('esp_tft', json.dumps(data), hostname=aws_mqtt_uri, retain=False, port=1883, keepalive=60)

        prev_title = title

    sleep(1)

