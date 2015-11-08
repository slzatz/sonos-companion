'''
uses boto3(duh)
Radio Play {neil young|artist} radio
Radio Play {WNYC|artist} radio
Shuffle please shuffle {one|number} songs from {neil young|artist}
Deborah play {one|number} of Deborah's albums
WhatIsPlaying what is playing now
WhatIsPlaying what song is playing now
WhatIsPlaying what is playing
WhatIsPlaying what song is playing
Skip skip
Skip next
Skip skip this song
Skip next song
Pause pause #note pauses or plays
Louder louder
Louder loud
Quieter lower
Quieter quieter
Quieter quiet
Quieter softer
TurnTheVolume Turn the volume {volume}
TurnTheVolume Turn {volume} the volume
'''

import os
import time
from time import sleep
import random
import json
import argparse
import sys
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + sys.path
import soco
from soco import config
import boto3 

parser = argparse.ArgumentParser(description='Command line options ...')
parser.add_argument('player', default='all', help="This is the name of the player you want to control or all")
args = parser.parse_args()

sqs = boto3.resource('sqs', region_name='us-east-1') 
q = sqs.get_queue_by_name(QueueName='echo_sonos') 

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

meta_format_pandora = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="OOOX52876609482614338" parentID="0" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

meta_format_radio = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="-1" parentID="-1" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItem.audioBroadcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

didl_amazon = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="00030020{id_}" parentID="" restricted="true"><dc:title></dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON6663_X_#Svc6663-0-Token</desc></item></DIDL-Lite>'''

with open('deborah_albums') as f:
    z = f.read()
DEBORAH_ALBUMS = list(json.loads(z).items())

with open('stations') as f:
    z = f.read()

STATIONS = json.loads(z)

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

#def play_uri(uri, meta, title):
#    try:
#        master.play_uri(uri, meta)
#    except Exception as e:
#        print "had a problem switching to {}!".format(title)
#        print "exception:",e
#    else:
#        print "switched to {}".format(title)

while 1:
    
    print time.time(), "checking"

    try:
        r = q.receive_messages(MaxNumberOfMessages=1, VisibilityTimeout=0, WaitTimeSeconds=20) 
    except Exception as e:
        print "Alexa exception: ", e
        continue

    if r:
        m = r[0]
        body = m.body
        print "sqs messge body =", body

        try:
            z = json.loads(body)
        except Exception as e:
            print "Alexa json exception: ", e
            m.delete()
            continue

        m.delete()

        action = z.get('action', '')

        #An alternative would be to define a dictionaly of actions and related functions but not particularly motivated to do that right now
        #d = {'deborah':f1, 'shuffle':f2, 'louder':f3 ...} d.get('deborah')(z) def f1(**kw); kw = 

        if action == 'deborah' and z.get('number'):
            
            songs = []

            master.stop()
            master.clear_queue()

            for x in range(z['number']):
                n = random.randint(0,len(DEBORAH_ALBUMS)-1)
                print "album: ", DEBORAH_ALBUMS[n][0]
                songs+=DEBORAH_ALBUMS[n][1]

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
    
        elif action == 'radio' and z.get('artist'):

            #uri = station[1]
            station = STATIONS.get(z['artist'].lower())
            if station:
                uri = station[1]
                print "uri=",uri
                if uri.startswith('pndrradio'):
                    meta = meta_format_pandora.format(title=station[0], service=station[2])
                    master.play_uri(uri, meta, station[0]) # station[0] is the title of the station
                elif uri.startswith('x-sonosapi-stream'):
                    uri = uri.replace('&', '&amp;') # need to escape '&' in radio URIs
                    meta = meta_format_radio.format(title=station[0], service=station[2])
                    master.play_uri(uri, meta, station[0]) # station[0] is the title of the station
            else:
                print "Couldn't find Pandora station " + z.get('artist')

        elif action == 'shuffle' and z.get('artist') and z.get('number'):
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

        elif action == 'pause':
            state = master.get_current_transport_info()['current_transport_state']
            if state == 'PLAYING':   #'PAUSED_PLAYBACK'
                master.pause()
            else:
                master.play()

        elif action == 'skip':
            master.next()

        elif action in ('quieter','louder'):
            volume = master.volume
            
            new_volume = volume - 10 if action=='quieter' else volume + 10
            
            if args.player == 'all':
                for s in speakers:
                    s.volume = new_volume
            else:
                master.volume = new_volume

            print "args.player=",args.player
            print "I tried to make the volume "+action

        else:
            print "I have no idea what you said"

    sleep(0.3)

