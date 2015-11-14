'''
This scripts collects metadata on Amazon Music Cloud songs and place it in a database amazon_music.db
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
'''
import os
#import argparse
import time
from time import sleep
#import datetime
#import xml.etree.ElementTree as ET
import sys

#import requests

home = os.path.split(os.getcwd())[0]
soco_dir = os.path.join(home,'SoCo')
sys.path = [soco_dir] + sys.path
print sys.path
import soco
from soco import config

from amazon_music_db import *

config.CACHE_ENABLED = False

n = 0
while 1:
    n+=1
    print "attempt "+str(n)
    try:
        speakers = list(soco.discover())
    except TypeError:
        sleep(1)
    else:
        break
    sleep(0.1)
    
print speakers ################

# appears that the property coordinator of s.group is not getting set properly and so can't use s.group.coordinator[.player_name]

for s in speakers:
    if s:
        #print "speaker: {} - master: {}".format(s.player_name, s.group)  #s.group.coordinator.player_name)
        print s.player_name

for s in speakers:
    if s.is_coordinator:
        master = s
        print "\nNOTE: found coordinator and master =",master.player_name
        break
else:
    master = speakers[0]
    print "\nALERT: id not find coordinator so took speaker[0] =",master.player_name

# for s in speakers:
    # if s != master:
        # s.join(master)

print "\nprogram running ..."

# not in use in this script
def get_info():

    info = master.avTransport.GetMediaInfo([('InstanceID', 0)])
    uri = info['CurrentURI']
    meta = info['CurrentURIMetaData']
    print "uri = ", uri
    print "meta = ", meta
    
orig_rows = session.query(Song).count()
print "starting out total of rows = ", orig_rows

while 1:

    try:
        state = master.get_current_transport_info()['current_transport_state']
    except Exception as e:
        state = 'ERROR'
        print "Encountered error in state = master.get_current transport_info(): ", e

    if state != 'PLAYING':
        print "state=",state
        continue
        
    print str(time.time()), "retrieving track information"
    #current_track = master.get_current_track_info()
    track = master.get_current_track_info()
    
    #track = dict(current_track)

    if track.get('uri','').find(':amz') != -1:

        try:
            s = Song(artist=track.get('artist'),title=track.get('title'),album=track.get('album'), album_art=track.get('album_art'), uri=track.get('uri'))
            session.add(s)
            session.commit()

        except (IntegrityError, OperationalError) as e:
            session.rollback()
            print "IntegrityError: ",e

        else:
            try:
                print u"\n{} {} {} {} added to db\n".format(track.get('artist'), track.get('title'), track.get('album'), track.get('uri'))
            except UnicodeEncodeError as e:
                print "UnicodeEncodeError: ",e

    try:
        master.next()
    except:
        sys.exit(1)

    sleep(5)

print "starting out total of rows=",orig_rows
rows = session.query(Song).count()
print "total rows now = ", rows
