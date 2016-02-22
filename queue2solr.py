'''
THIS IS CURRENTLY THE SCRIPT TO USE TO MOVE TRACKS IN THE QUEUE INTO SOLR
This script allows you to move data from a file to solr
If the document already exists, the add operation will replace it. 
get_trackinfo.py was used to get tracks out of sonos into a file
It would be possible to add that code here so it went straight from sonos to solr
The output of get_trackinfo.py looks like this:

What do you want to call the file that will have the track info for uploading to solr?testing123
2016-01-23 06:30:21 checking to see if track has changed
playlist_position=1
duration=0:04:02
album_art=http://192.168.1.125:1400/getaa?s=1&u=x-sonos-http%3aamz%253atr%253a9f5a7c3b-38e1-4be7-b032-669dcc3c9365.mp3%3fsid%3d26%26flags%3d8224%26sn%3d1
uri=x-sonos-http:amz%3atr%3a9f5a7c3b-38e1-4be7-b032-669dcc3c9365.mp3?sid=26&flags=8224&sn=1
title=Speed Trap Town
album=Something More Than Free [Explicit]
position=0:00:01
artist=Jason Isbell
metadata=<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn
:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="-1" parentID="-1" restricted="true"><res protocolInfo="sonos.com-http:*:audio/mpeg:*" duration="0:04:02">x-sonos-http:amz%3atr%3a
9f5a7c3b-38e1-4be7-b032-669dcc3c9365.mp3?sid=26&amp;flags=8224&amp;sn=1</res><r:streamContent></r:streamContent><upnp:albumArtURI>/getaa?s=1&amp;u=x-sonos-http%3aamz%253atr%253a9f5a7
c3b-38e1-4be7-b032-669dcc3c9365.mp3%3fsid%3d26%26flags%3d8224%26sn%3d1</upnp:albumArtURI><dc:title>Speed Trap Town</dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class>
<dc:creator>Jason Isbell</dc:creator><upnp:album>Something More Than Free [Explicit]</upnp:album></item></DIDL-Lite>

Note: We do use album, album_art, uri, title, artist
We don't use duration or position and we don't use metadata, which doesn't fully match the metadata needed to play songs, which we get through wire shark

The upload format for SolrClient (python3 solr client program) is jsonifying a list of dictionaries:
[{'id':'After_The_Gold_Rush_Birds', 'artist':'Neil Young', 'title':'Birds', 'album':'After the Gold Rush',
'uri':'x-sonos-http:amz%3atr%3a44ce93d2-4105-416a-a905-51fe0f38ed9a.mp4?sid=26&flags=8224&sn=2'...}{...
'''

from SolrClient import SolrClient
import sys
import json
import requests
from config import ec_uri
import os
from time import sleep
import datetime
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + sys.path
import soco
from soco import config

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

#Note that will need album, title, artist, etc.
album = input("What is the album? ")
artist = input("Who is the artist? ")
# not idea if title = track.resources[0].title or album = track.resources[0].album ...
queue = master.get_queue()
if len(queue) == 0:
    raise Exception("You must have at least one track in the queue")

documents = []
n=1
for track in queue:
    title = track.title
    id_ = album + ' ' + title
    id_ = id_.replace(' ', '_')
    document = {"id":id_, "title":title, "uri":track.resources[0].uri, "album":album, "artist":artist, "track":n}
    print(document)
    documents.append(document)
    #print("track.resources[0].uri =",track.resources[0].to_dict(), track.resources[0].uri.replace("%2f","/").replace("%252520", " "))
    #print(dir(track.resources[0]))
    n+=1

solr = SolrClient(ec_uri+':8983/solr')
collection = 'sonos_companion'

cur_documents = json.dumps(documents) 
response = solr.index_json(collection, cur_documents) 
print(response)

# Since solr.commit didn't seem to work, substituted the below, which works
url = ec_uri+":8983/solr/"+collection+"/update"
r = requests.post(url, data={"commit":"true"})
print(r.text)

