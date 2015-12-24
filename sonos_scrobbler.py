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
import time
from time import sleep
import json
import argparse
import sys
import datetime
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + sys.path
import config as c
import soco
from soco import config
import boto3 

parser = argparse.ArgumentParser(description='Command line options ...')
parser.add_argument('player', default='all', help="This is the name of the player you want to control or all")
args = parser.parse_args()

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
scrobble_table = dynamodb.Table('scrobble_new')

config.CACHE_ENABLED = False

n = 0
while 1:
    n+=1
    print "\nattempt "+str(n)+"\n"
    try:
        sp = soco.discover(timeout=5)
        speakers = list(sp)
    except TypeError as e:    
        print e
        sleep(1)       
    else:
        break 

d = {}
for s in speakers:
    print s.player_name
    gc = s.group.coordinator
    d[gc] = d[gc] + 1 if gc in d else 1

for gc in d:
    print "{}:{}".format(gc.player_name, d[gc])

master = max(d.keys(), key=lambda k: d[k])
print "master = ", master.player_name

print "\n"

print "program running ..."

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
                'location':c.location,
                'artist':track.get('artist'),
                'ts': int(time.time()), # shouldn't need to truncate to an integer but getting 20 digits to left of decimal point in dynamo
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

    sleep(0.5)

