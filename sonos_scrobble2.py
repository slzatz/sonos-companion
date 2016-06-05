'''
Current script to scrobble songs playing on Sonos to mqtt broker: have used
aws ec2 for mqtt broker but probably does make more sense to use a local
raspberry pi -- so config.py needs to set the mqtt_uri to localhost or ec2
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
from time import sleep
import json
import sys
import datetime
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + sys.path
from config import mqtt_uri, location
import soco
from soco import config as soco_config
#import boto3 
import paho.mqtt.publish as mqtt_publish

# Now just putting location in the config file
#s3 = boto3.resource('s3')
#s3obj = s3.Object('sonos-scrobble','location')
#location = s3obj.get()['Body'].read()
print("The current location is {}".format(location))

topic = 'sonos/{}/current_track'.format(location)
print("topic =",topic)

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
prev_time = datetime.datetime.now()

while 1:
    
    # get the current state
    try:
        state = master.get_current_transport_info()['current_transport_state']
    except Exception as e:
        print "Encountered error in state = master.get_current_transport_info(): ", e
        state = 'error'

    track = {}
    # check if sonos is playing music
    if state == 'PLAYING':

        try:
            track = master.get_current_track_info()
        except Exception as e:
            print "Encountered error in track = master.get_current_track_info(): ", e

    #cur_time = datetime.datetime.now()
    cur_title = track.get('title', '')
    
    if cur_title != prev_title:
        oled_data = {'artist':track.get('artist', ''), 'title':cur_title}
        # publish to MQTT - could require less code by using micropython mqtt client
        try:
            mqtt_publish.single(topic, json.dumps(oled_data), hostname=mqtt_uri, retain=False, port=1883, keepalive=60)
        except Exception as e:
            print "Exception trying to publish to mqtt broker: ", e
        else:
            print "{} sent successfully to mqtt broker".format(json.dumps(oled_data))

        prev_title = cur_title

    sleep(0.5)

