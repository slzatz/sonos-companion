'''
current_track = master.get_current_track_info() --> {
            u'album': 'We Walked In Song', 
            u'artist': 'The Innocence Mission', 
            u'title': 'My Sisters Return From Ireland', 
            u'uri': 'pndrradio-http://audio-sv5-t3-1.pandora.com/access/5459257820921908950?version=4&lid=86206018&token=...', 
            u'playlist_position': '3', 
            u'duration': '0:02:45', 
            u'position': '0:02:38', 
            u'album_art': 'http://cont-ch1-2.pandora.com/images/public/amz/3/2/9/3/655037093923_500W_500H.jpg'}
To Do:
- Artist shuffling could move from dynamodb to cloudsearch: result = cloudsearchdomain.search(query=task['artist'], queryOptions='{"fields":["artist"]}')
- Could also have an Album search -> Album play album {after the gold rush|albumtitle} - could be custom slot but not sure any real benefit
- May not need a special album search just "play ..." since I could look for word song or album remove them from search and limit search fields
'''

import os
from time import time, sleep
import json
import sys
import datetime
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + sys.path
from config as ec_uri
import soco
from soco import config
import boto3 
import requests

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
scrobble_table = dynamodb.Table('scrobble_new')

s3 = boto3.resource('s3')
s3obj = s3.Object('sonos-scrobble','location')
location = s3obj.get()['Body'].read()

config.CACHE_ENABLED = False

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
    
    # Below is the check if the track has changed and if so it is scrobbled to dynamodb
    try:
        state = master.get_current_transport_info()['current_transport_state']
    except Exception as e:
        print "Encountered error in state = master.get_current_transport_info(): ", e
        sleep(0.5)
        continue

    try:
        # check if sonos is playing music and, if not, do nothing
        track = master.get_current_track_info()
    except Exception as e:
        print "Encountered error in state = master.get_current_track_info(): ", e
        sleep(0.5)
        continue

    if state != 'PLAYING' or 'tunein' in track.get('uri', ''):
        sleep(0.5)
        continue
            
    cur_time = datetime.datetime.now()

    if cur_time - prev_time > datetime.timedelta(seconds=10):
        print "{} {}".format(cur_time.strftime('%Y-%m-%d %H:%M:%S'), master.player_name)
        prev_time = cur_time
    
    if prev_title != track.get('title') and track.get('artist'): 
        
        prev_title = track.get('title') 

        # Write the latest scrobble to dynamodb 'scrobble_new'
        data = {
                'location':location,
                'artist':track.get('artist'),
                'ts': int(time()), # shouldn't need to truncate to an integer but getting 20 digits to left of decimal point in dynamo
                'title':track.get('title'),
                'album':track.get('album'),
                'date':track.get('date')}
                #'scrobble':track.get('scrobble')} #it's a string although probably should be converted to a integer

        data = {k:v for k,v in data.items() if v} 
        try:
            scrobble_table.put_item(Item=data)
        except Exception as e:
            print "Exception trying to write dynamodb scrobble table:", e
        else:
            print "{} sent successfully to dynamodb".format(json.dumps(data))

        oled_data = {'artist':track.get('artist', 'No artist'), 'title':track.get('title', 'No title')}
        url = ec_uri+":5000/scrobble"
        r = requests.post(url, json=oled_data)
        print r.text

    sleep(0.5)

