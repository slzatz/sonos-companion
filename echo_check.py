import os
import time
from time import sleep
import datetime
import random
import json
import argparse
import sys
import config as c
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + [os.path.join(home, 'pydub')] + [os.path.join(home, 'twitter')] + sys.path
import soco
from soco import config

import boto.sqs
from boto.sqs.message import Message

parser = argparse.ArgumentParser(description='Command line options ...')
parser.add_argument('player', default='all', help="This is the name of the player you want to control or all")
args = parser.parse_args()

conn = boto.sqs.connect_to_region(
    "us-east-1",
    aws_access_key_id=c.aws_access_key_id,
    aws_secret_access_key=c.aws_secret_access_key)

from amazon_music_db import *
from sqlalchemy.sql.expression import func

config.CACHE_ENABLED = False

n = 0
while 1:
    n+=1
    print "attempt "+str(n)
    try:
        sp = soco.discover(timeout=5)
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

print "program running ..."

#globals
#stations = [
#('Add 10 to number',),
#('WNYC-FM', 'x-sonosapi-stream:s21606?sid=254&flags=32', 'SA_RINCON65031_'), 
#('WSHU-FM', 'x-sonosapi-stream:s22803?sid=254&flags=32', 'SA_RINCON65031_'),
#('Neil Young Radio', 'pndrradio:52876154216080962', 'SA_RINCON3_slzatz@gmail.com'),
#('QuickMix', 'pndrradio:52877953807377986', 'SA_RINCON3_slzatz@gmail.com'),
#('R.E.M. Radio', 'pndrradio:637630342339192386', 'SA_RINCON3_slzatz@gmail.com'), 
#('Nick Drake Radio', 'pndrradio:409866109213435458', 'SA_RINCON3_slzatz@gmail.com'),
#('Dar Williams Radio', 'pndrradio:1823409579416053314', 'SA_RINCON3_slzatz@gmail.com'),
#('Patty Griffin Radio', 'pndrradio:52876609482614338', 'SA_RINCON3_slzatz@gmail.com'),
#('Lucinda Williams Radio', 'pndrradio:360878777387148866', 'SA_RINCON3_slzatz@gmail.com'),
#('Kris Delmhorst Radio', 'pndrradio:610111769614181954', 'SA_RINCON3_slzatz@gmail.com'),
#('Counting Crows Radio', 'pndrradio:1727297518525703746', 'SA_RINCON3_slzatz@gmail.com'), 
#('Vienna Teng Radio', 'pndrradio:138764603804051010', 'SA_RINCON3_slzatz@gmail.com')]

#echo = [x[0].lower() for x in stations]
#print "echo=",echo
#station_index = 0

#meta_format_pandora = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="OOOX52876609482614338" parentID="0" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

#meta_format_radio = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="-1" parentID="-1" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItem.audioBroadcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

didl_amazon = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="00030020{id_}" parentID="" restricted="true"><dc:title></dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON6663_X_#Svc6663-0-Token</desc></item></DIDL-Lite>'''

#def play_random_amazon():
#    master.stop()
#    master.clear_queue()
#
#    rows = session.query(Song).count()
#
#    for n in range(10):
#        r = random.randrange(1,rows-1)
#        song = session.query(Song).get(r)
#        print song.id
#        print song.artist
#        print song.album
#        print song.title
#        print song.uri
#        i = song.uri.find('amz')
#        ii = song.uri.find('.')
#        id_ = song.uri[i:ii]
#        print id_
#        meta = didl_amazon.format(id_=id_)
#        my_add_to_queue('', meta)
#        print "---------------------------------------------------------------"
#        
#    master.play_from_queue(0)

with open('deborah_albums') as f:
    z = f.read()

zz = json.loads(z)
zzz = [x for x in zz]

def my_add_to_queue(uri, metadata):
    response = master.avTransport.AddURIToQueue([
            ('InstanceID', 0),
            ('EnqueuedURI', uri),
            ('EnqueuedURIMetaData', metadata),
            ('DesiredFirstTrackNumberEnqueued', 0),
            ('EnqueueAsNext', 1)
            ])
    qnumber = response['FirstTrackNumberEnqueued']
    return int(qnumber)

q = conn.get_queue('echo_sonos')

while 1:
    
    print time.time(), "checking"
    try:
        #m = q.get_messages() # below have added wait time so not generating too many requests
        m = q.get_messages(1, visibility_timeout=100, wait_time_seconds=20)
    except Exception as e:
        print "Alexa exception: ", e
        continue

    if m:
        m = m[0]
        body = m.get_body()
        print "message =", m
        print "body =", body

        try:
            z = json.loads(body)
        except Exception as e:
            print "Alexa json exception: ", e
            q.delete_message(m)
            continue

        q.delete_message(m)

        print z.get('action', "no action present")
        print z.get('artist', "no artist present")
        print z.get('number', "no number present")

        if z.get('action') == 'deborah' and z.get('number'):
            
            songs = []

            master.stop()
            master.clear_queue()

            for x in range(int(z['number'])):
                n = random.randint(0,len(zzz)-1)
                print "album: ", zzz[n]
                songs+=zz[zzz[n]]

            for uri in songs:
                print uri
                i = uri.find('amz')
                ii = uri.find('.')
                id_ = uri[i:ii]
                print id_
                meta = didl_amazon.format(id_=id_)
                my_add_to_queue('', meta)
                print "---------------------------------------------------------------"

            master.play_from_queue(0)
    
        elif z.get('action') == 'shuffle' and z.get('artist') and z.get('number'):
            master.stop()
            master.clear_queue()

            songs = session.query(Song).filter(Song.artist==z['artist'].title()).order_by(func.random()).limit(int(z['number'])).all()

            for song in songs:
                print song.id
                print song.artist
                print song.album
                print song.title
                print song.uri
                i = song.uri.find('amz')
                ii = song.uri.find('.')
                id_ = song.uri[i:ii]
                print id_
                meta = didl_amazon.format(id_=id_)
                my_add_to_queue('', meta)
                print "---------------------------------------------------------------"

            master.play_from_queue(0)
    sleep(0.3)

