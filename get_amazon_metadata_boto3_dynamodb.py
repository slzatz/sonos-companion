'''
This script collects metadata on Amazon Music Cloud songs and place it in a aws dynamodb database amazon_music
Presumably you have to queue all of your amazon songs

    get_current_track_info() =  {
        u'album': 'We Walked In Song', 
        u'artist': 'The Innocence Mission', 
        u'title': 'My Sisters Return From Ireland', 
        u'uri': 'pndrradio-http://audio-sv5-t3-1.pandora.com/access/5459257820921908950?version=4&lid=86206018&token=...', 
        u'playlist_position': '3', 
        u'duration': '0:02:45', 
        u'position': '0:02:38', 
        u'album_art': 'http://cont-ch1-2.pandora.com/images/public/amz/3/2/9/3/655037093923_500W_500H.jpg'}

Partition Key and Sort Key  A composite primary key, composed of two attributes. The first attribute is the partition key, and the second attribute is the sort key. DynamoDB uses the partition key value as input to an internal hash function; the output from the hash function determines the partition where the item will be stored. All items with the same partition key are stored together, in sorted order by sort key value. It is possible for two items to have the same partition key value, but those two items must have different sort key values.
album and title should be the unique constraint -- it is possible for one album to have the same tititle (although usually labeled differently) or possibly for two different albums to have the same album name and song title but that's life.  The alternative is to make up a unique key like album-title-artist
Seems to me that the partition should be album and the sort should be title
Note that you just create the table with the two indexes and then add items that have additional attributes like uri, artist, etc.
'''

import os
import time
from time import sleep
import argparse
import sys
import datetime
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + sys.path
import soco
from soco import config
import requests
import boto3 
import config as c

parser = argparse.ArgumentParser(description='Command line options ...')
parser.add_argument('player', default='all', help="This is the name of the player you want to control or all")
args = parser.parse_args()

sqs = boto3.resource('sqs', region_name='us-east-1') 
sqs_queue = sqs.get_queue_by_name(QueueName='echo_sonos') 

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('amazon_music')

config.CACHE_ENABLED = False

n = 0
while 1:
    n+=1
    print "attempt "+str(n)
    try:
        sp = soco.discover(timeout=20)
        speakers = list(sp)
        #speakers = list(soco.discover(timeout=5))
    except TypeError as e:    
        print e
        sleep(1)       
    else:
        break 
    
print speakers 

# appears that the property coordinator of s.group is not getting set properly and so can't use s.group.coordinator[.player_name]

for s in speakers:
    if s:
        #print "speaker: {} - master: {}".format(s.player_name, s.group)  #s.group.coordinator.player_name)
        print s.player_name
           
if args.player.lower() == 'all':

    for s in speakers:
        if s.is_coordinator:
            master = s
            print "\nNOTE: found coordinator and master =", master.player_name
            break
    else:
        master = speakers[0]
        print "\nALERT: id not find coordinator so took speaker[0] =",master.player_name

    for s in speakers:
        if s != master:
            s.join(master)
    
else:

    for s in speakers:
        if s:
            print s.player_name
            if s.player_name.lower() == args.player.lower():
                master = s
                print "The single master speaker is: ", master.player_name
                break
    else:
        print "Could not find the specified speaker"
        sys.exit()

print "\n"

orig_rows = table.item_count
print "starting out total of rows = ", orig_rows

while 1:
    
    print "{} next song".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    try:
        state = master.get_current_transport_info()['current_transport_state']
    except Exception as e:
        state = 'ERROR'
        print "Encountered error in state = master.get_current transport_info(): ", e

    if state != 'PLAYING':
        print "state=",state
        continue

    track = master.get_current_track_info()
            
    if track.get('album') and track.get('title') and track.get('uri','').find(':amz') != -1:

        data = {
                'album':track['album'],
                'title':track['title'],
                'artist':track.get('artist'),
                'album_art':track.get('album_art'),
                'uri':track['uri']} #it's a string ? should be converted to a integer

        data = {k:v for k,v in data.items() if v} 
        try:
            table.put_item(Item=data)
        except Exception as e:
            print "Exception trying to write dynamodb scrobble table:", e
        else:
            try:
                print u"\n{} {} {} {} added to dynamodb\n".format(
                                                             track.get('artist'),
                                                             track['title'],
                                                             track['album'],
                                                             track['uri'])
            except UnicodeEncodeError as e:
                print "UnicodeEncodeError: ",e

    try:
        master.next()
    except:
        sys.exit(1)

    sleep(5)

print "starting out total of rows=",orig_rows
rows = table.item_count
print "total rows now = ", rows

