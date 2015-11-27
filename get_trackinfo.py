'''
takes track information from tracks playing in sonos and writes them to a file
along with file2cloudsearch was used to move rhapsody information into cloudsearch
Could be used for rhapsody or amazon tracks
'''
import os
import argparse
import sys
import json
import datetime
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + sys.path
import soco
from soco import config
import boto3 
import config as c
from amazon_music_db import *
from sqlalchemy.sql.expression import func
import musicbrainzngs

parser = argparse.ArgumentParser(description='Command line options ...')
parser.add_argument('player', default='all', help="This is the name of the player you want to control or all")
args = parser.parse_args()

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

print '\n'

prev_title = -1
tracks = []

while True:

    try:
        state = master.get_current_transport_info()['current_transport_state']
    except Exception as e:
        state = 'ERROR'
        print "Encountered error in state = master.get_current transport_info(): ", e

    # check if sonos is playing music and, if not, do nothing
    track = master.get_current_track_info()
    if state != 'PLAYING' or 'tunein' in track.get('uri', ''):

        continue
            
    print "{} checking to see if track has changed".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    
    if prev_title != track.get('title') and track.get('artist'): 
        
        prev_title = track.get('title') 

        for k in track.keys():
            print "{}={}".format(k,track.get(k,''))

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
    
with open('rhapsody_tracks', 'w') as f:
    f.write(json.dumps(tracks))
