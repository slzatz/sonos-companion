'''
This script takes the songs in the queue and turns them into a playlist that is placed in S3
python 3
takes track information from tracks playing in sonos and writes them to a file
along with file2solr was used to move sonos song information into solr
Can be used for Rhapsody or Amazon music tracks or the new Amazon 'library' format
'''
import os
from time import sleep
import sys
import json
import datetime
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + sys.path
import soco
from soco import config
import requests
import boto3

config.CACHE_ENABLED = False

n = 0
while 1:
    n+=1
    print("attempt "+str(n))
    try:
        sp = soco.discover(timeout=2)
        speakers = {s.player_name:s for s in sp}
    except TypeError as e:    
        print(e)
        sleep(1)       
    else:
        break 
    
for sn in speakers:
        print("{} -- coordinator:{}".format(sn, speakers[sn].group.coordinator.player_name))

master_name = input("Which speaker do you want to be master? ")
master = speakers.get(master_name)
if master:
    print("Master speaker is: {}".format(master.player_name))
else:
    print("Somehow you didn't pick a master or spell it correctly (case matters")
    sys.exit(1)

print('\n')

file_name = input("What do you want to call the file that will have the playlist track info for uploading to s3?")

queue = master.get_queue()
if len(queue) == 0:
    raise Exception("You must have at least one track in the queue")

tracks = []
for track in queue:
    title = track.title
    album = track.album
    #artist = track.creator
    id_ = album + ' ' + title
    id_ = id_.replace(' ', '_')
    tracks.append((id_, track.resources[0].uri))
    
with open(file_name, 'w') as f:
    f.write(json.dumps(tracks))

s3 = boto3.resource('s3')
s3.meta.client.upload_file(file_name, 'sonos-scrobble', 'playlists/'+file_name)
#object = s3.Object('sonos-scrobble', 'playlists'+'/'+playlist_name)
#object.put(Body='nyc')
