'''
THIS IS THE CURRENT SCRIPT TO GET TRACK INFO AND WRITE IT TO A FILE SO FILE2SOLR.PY CAN WRITE TO SOLR
python 3
takes track information from tracks playing in sonos and writes them to a file
along with file2solr is used to move Sonos song information into solr
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

file_name = input("What do you want to call the file that will have the track info for uploading to solr?")

prev_title = ''
prev_album = ''
tracks = []

while True:

    try:
        state = master.get_current_transport_info()['current_transport_state']
    except (requests.exceptions.ConnectionError, soco.exceptions.SoCoUPnPException) as e:
        print("Encountered error in state = master.get_current_transport_info(): ", e)
        sleep(0.5)
        continue

    try:
        # check if sonos is playing music and, if not, do nothing
        track = master.get_current_track_info()
    except (requests.exceptions.ConnectionError, soco.exceptions.SoCoUPnPException) as e:
        print("Encountered error in state = master.get_current_track_info(): ", e)
        sleep(0.5)
        continue

    if state != 'PLAYING' or 'tunein' in track.get('uri', ''):
        sleep(0.5)
        continue
            
    print("{} checking to see if track has changed".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    
    if prev_title != track.get('title') and prev_album != track.get('album') and track.get('artist'): 
        
        prev_title = track.get('title') 
        prev_album = track.get('album') 

        for k in track.keys():
            print("{}={}".format(k,track.get(k,'')))

        z = tracks.append(track)

        #media_info = master.avTransport.GetMediaInfo([('InstanceID', 0)])

        #media_uri = media_info['CurrentURI']
        #media_meta = media_info['CurrentURIMetaData']
        #print "media_info uri=", media_uri
        #print "media_meta=",media_meta

    try:
        master.next()
    except:
       break 

    sleep(5)
    
with open(file_name, 'w') as f:
    f.write(json.dumps(tracks))
