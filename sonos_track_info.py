'''
Current script to scrobble songs playing on Sonos to mqtt broker: have used
aws ec2 for mqtt broker but probably does make more sense to use a local
raspberry pi -- so config.py needs to set the local_mqtt_uri to localhost
uri

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
from time import sleep, time
import json
import sys
import datetime
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + sys.path
from config import local_mqtt_uri, location, mqtt_uris, aws_mqtt_uri
import soco
from soco import config as soco_config
import paho.mqtt.publish as mqtt_publish
import requests
import lxml.html

print("The current location is {}".format(location))

sonos_track_topic = 'sonos/{}/track'.format(location)
print("sonos_track_topic =",sonos_track_topic)

sonos_status_topic = 'sonos/{}/status'.format(location)
print("sonos_status_topic =",sonos_status_topic)

topic2 = 'sonos/{}/volume'.format(location)
print("topic2 =",topic2)

#aws_host = mqtt_uris['other']
#aws_host = aws_mqtt_uri

#topic3 = 'sonos/{}/lyrics'.format(location)
#print("topic3 =",topic3)

soco_config.CACHE_ENABLED = False

n = 0
while 1:
    n+=1
    print "attempt "+str(n) 
    try:
        sp = soco.discover(timeout=2)
        speakers = {s.player_name:s for s in sp}
    except TypeError as e:    
        print e 
        sleep(1)       
    else:
        break 
    
for s in sp:
    print "{} -- coordinator:{}".format(s.player_name, s.group.coordinator.player_name) 

master_name = raw_input("Which speaker do you want to be master? ")
master = speakers.get(master_name)
if master:
    print "Master speaker is: {}".format(master.player_name) 
    sp = [s for s in sp if s.group.coordinator is master]
    print "Master group:"
    for s in sp:
        print "{} -- coordinator:{}".format(s.player_name, s.group.coordinator.player_name) 

else:
    print "Somehow you didn't pick a master or spell it correctly (case matters)" 
    sys.exit(1)

print "\nprogram running ..."

prev_title = ''
prev_volume = -1
track = {}

def get_url(artist, title):

    if artist is None or title is None:
        return None

    payload = {'func': 'getSong', 'artist': artist, 'song': title, 'fmt': 'realjson'}
    
    try:
         r = requests.get("http://lyrics.wikia.com/api.php", params=payload)
    except:
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

    for line in lyrics:
        print line

    return lyrics

t0 = time()
while 1:
    
    # get the current state to see if Sonos is actually playing
    try:
        state = master.get_current_transport_info()['current_transport_state']
    except Exception as e:
        print "Encountered error in state = master.get_current_transport_info(): ", e
        state = 'ERROR'

    # check if sonos is playing music
    if state == 'PLAYING':

        # get volume for neopixel display
        cur_volume = master.volume
        
        if cur_volume != prev_volume:
            try:
                mqtt_publish.single(topic2, cur_volume, hostname=local_mqtt_uri, retain=False, port=1883, keepalive=60)
            except Exception as e:
                print "Exception trying to publish to mqtt broker: ", e
            else:
                print "volume {} sent successfully to mqtt broker".format(cur_volume)

            prev_volume = cur_volume

        # get track info to see if track has changed
        try:
            track = master.get_current_track_info()
        except Exception as e:
            print "Encountered error in track = master.get_current_track_info(): ", e
            continue

    cur_title = track.get('title', '')
    
    if cur_title != prev_title:

        data = {'artist':track.get('artist', ''), 'title':cur_title}
        lyrics = get_lyrics(track.get('artist'), cur_title)
        if lyrics:
            data['lyrics'] = lyrics
        # publish to MQTT - could require less code by using micropython mqtt client
        data2 = {'header':'Track Info - '+location, 'text':[data['artist'], cur_title], 'pos':9}
        try:
            #mqtt_publish.single(topic, json.dumps(data), hostname=local_mqtt_uri, retain=False, port=1883, keepalive=60)
            # The line below is currently being picked up by esp_tft_mqtt_photos and don't really want it to be picked up by 
            # display_info_photos because it would just be published directly
            mqtt_publish.single(sonos_track_topic, json.dumps(data), hostname=aws_mqtt_uri, retain=False, port=1883, keepalive=60)
            mqtt_publish.single('esp_tft', json.dumps(data2), hostname=aws_mqtt_uri, retain=False, port=1883, keepalive=60)
        except Exception as e:
            print "Exception trying to publish to mqtt broker: ", e
        else:
            print "{} sent successfully to mqtt broker".format(json.dumps(data))

        prev_title = cur_title

    if time() > t0+60:
        data3 = {'header':'Sonos Status - '+location, 'text':[state], 'pos':2}
        mqtt_publish.single('esp_tft', json.dumps(data3), hostname=aws_mqtt_uri, retain=False, port=1883, keepalive=60)
        # at least one of the listeners for the below is esp_tft_mqtt_photos.py
        mqtt_publish.single(sonos_status_topic, json.dumps({'state':'state'}), hostname=aws_mqtt_uri, retain=False, port=1883, keepalive=60)
        t0 = time()
        
    sleep(0.5)

