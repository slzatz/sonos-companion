'''
uses boto3(duh)
uses dynamodb for radio stations and shuffling songs
uses cloudsearch to enable searching on tracks and artists

Radio select {myartist} radio
Shuffle shuffle {myartist} MY_ARTIST -> Ten thousand Maniacs | A3 | Abra Moore | Adam Duritz ...
PlayTrack play {after the gold rush|trackinfo} #better maybe play {mytitle} by {myartist}
AddTrack add {after the gold rush|trackinfo} #better maybe add {mytitle} by {myartist}
PlayAlbum play album {myalbum} MY_ALBUM -> Nineteen | Twenty-one | Four Way Street ...
WhatIsPlaying what is playing now
WhatIsPlaying what song is playing now
WhatIsPlaying what is playing
WhatIsPlaying what song is playing
Skip skip
Skip next
PauseResume {pauseorresume} the music PAUSE_RESUME -> pause | stop | unpause | resume
TurnTheVolume Turn the volume {volume} VOLUME -> up | down | louder | higher | quieter | lower | mute
TurnTheVolume Turn {volume} the volume

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
import random
import json
import argparse
import sys
import datetime
from operator import itemgetter
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + sys.path
import soco
from soco import config
import requests
import boto3 
from boto3.dynamodb.conditions import Key
import config as c
#from amazon_music_db import *
#from sqlalchemy.sql.expression import func
import musicbrainzngs

parser = argparse.ArgumentParser(description='Command line options ...')
parser.add_argument('player', default='all', help="This is the name of the player you want to control or all")
args = parser.parse_args()

sqs = boto3.resource('sqs', region_name='us-east-1') 
sqs_queue = sqs.get_queue_by_name(QueueName='echo_sonos') 

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
scrobble_table = dynamodb.Table('scrobble_new')
amazon_music_table = dynamodb.Table('amazon_music')

cloudsearchdomain = boto3.client('cloudsearchdomain', endpoint_url=c.aws_cs_url, region_name='us-east-1')
config.CACHE_ENABLED = False

musicbrainzngs.set_useragent("Sonos", "0.1", contact="slzatz")

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

print "program running ..."

meta_format_pandora = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="OOOX52876609482614338" parentID="0" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

meta_format_radio = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="-1" parentID="-1" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItem.audioBroadcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

didl_amazon = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="00030020{id_}" parentID="" restricted="true"><dc:title></dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON6663_X_#Svc6663-0-Token</desc></item></DIDL-Lite>'''

didl_rhapsody = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="RDCPI:GLBTRACK:Tra.{id_}" parentID="-1" restricted="true"><dc:title></dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON1_{}</desc></item></DIDL-Lite>'''.format(c.user_id)

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

prev_title = ''

while 1:
    
    print "{} checking sqs queue for new message".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # check sqs_queue for new actions to take
    try:
        r = sqs_queue.receive_messages(MaxNumberOfMessages=1, VisibilityTimeout=0, WaitTimeSeconds=20) 
    except Exception as e:
        print "sqs receive error checking for posted actions: ", e
        continue

    if r:
        m = r[0]
        body = m.body
        print "sqs messge body =", body

        try:
            task = json.loads(body)
        except Exception as e:
            print "error reading the sqs message body: ", e
            m.delete()
            continue

        m.delete()

        action = task.get('action', '')

        #An alternative would be to define a dictionary of actions and related functions but not particularly motivated to do that right now
        #d = {'deborah':f1, 'shuffle':f2, 'louder':f3 ...} d.get('deborah')(task) def f1(**kw); kw = 

        if action == 'deborah' and task.get('number'):
            
            songs = []

            master.stop()
            master.clear_queue()

            try:
                number = int(task['number'])
            except ValueError as e:
                print e
                number = 1

            for x in range(number):
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
    
        elif action == 'radio' and task.get('artist'):

            station = STATIONS.get(task['artist'].lower())
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
                print "Couldn't find Pandora station " + task.get('artist')

        elif action in ('play','add') and task.get('trackinfo'): 

            #The query below only searches title and artist fields so you don't get every song on After the Gold Rush
            result = cloudsearchdomain.search(query=task['trackinfo'], queryOptions='{"fields":["title", "artist"]}')

            count = result['hits']['found']
            if count:
            #    if action == 'play':
            #        master.stop()
            #        master.clear_queue()
            #    for track in result['hits']['hit']:
            #        song = track['fields']
            #        try:
            #            print 'artist: ' + song.get('artist', ['No artist'])[0]
            #            print 'album: ' + song.get('album', ['No album'])[0]
            #            print 'song: ' + song.get('title', ['No title'])[0]
            #        except Exception as e:
            #            print "Unicode error"
            #        uri = song.get('uri', [''])[0]
            #        print 'uri: ' + uri
            #        i = uri.find('amz')
            #        ii = uri.find('.')
            #        id_ = uri[i:ii]
            #        print 'id: ' + id_
            #        if id_:
            #            meta = didl_amazon.format(id_=id_)
            #            my_add_to_queue('', meta)
            #        print "---------------------------------------------------------------"
                trak = result['hits']['hit'][random.randint(0, count-1)]
                song = trak['fields']
                try:
                    print 'artist: ' + song.get('artist', ['No artist'])[0]
                    print 'album: ' + song.get('album', ['No album'])[0]
                    print 'song: ' + song.get('title', ['No title'])[0]
                except Exception as e:
                    print "Unicode error"
                uri = song.get('uri', [''])[0]
                print 'uri: ' + uri
                print "---------------------------------------------------------------"

                if 'amz' in uri:
                    i = uri.find('amz')
                    ii = uri.find('.')
                    id_ = uri[i:ii]
                    meta = didl_amazon.format(id_=id_)
                else:
                    i = uri.find('.')+1
                    ii = uri.find('.',i)
                    id_ = uri[i:ii]
                    meta = didl_rhapsody.format(id_=id_)
                    print '---------------------------------------------------------------'
                    print 'meta: ',meta

                if action == 'play':
                    master.stop()
                    master.clear_queue()
                    my_add_to_queue('', meta)
                    master.play_from_queue(0)

                else:
                    my_add_to_queue('', meta)

            else:
                print "Could not find requested track " + task['trackinfo']

        elif action == 'play_album' and task.get('album'): 

            result = cloudsearchdomain.search(query=task['album'], queryOptions='{"fields":["album"]}')

            count = result['hits']['found']
            if count:
                master.stop()
                master.clear_queue()
                for trak in result['hits']['hit']:
                    song = trak['fields']
                    try:
                        print 'artist: ' + song.get('artist', ['No artist'])[0]
                        print 'album: ' + song.get('album', ['No album'])[0]
                        print 'song: ' + song.get('title', ['No title'])[0]
                    except Exception as e:
                        print "Unicode error"
                    uri = song.get('uri', [''])[0]
                    print 'uri: ' + uri
                    print "---------------------------------------------------------------"

                    if 'amz' in uri:
                        i = uri.find('amz')
                        ii = uri.find('.')
                        id_ = uri[i:ii]
                        meta = didl_amazon.format(id_=id_)
                    else:
                        i = uri.find('.')+1
                        ii = uri.find('.',i)
                        id_ = uri[i:ii]
                        meta = didl_rhapsody.format(id_=id_)
                        print '---------------------------------------------------------------'
                        print 'meta: ',meta

                    my_add_to_queue('', meta)

                master.play_from_queue(0)

            else:
                print "Could not find requested track " + task['trackinfo']

        elif action == 'shuffle' and task.get('artist') and task.get('number'):

            try:
                number = int(task['number'])
            except ValueError as e:
                print e
                number = 5

            # below could be cloudsearch artist search
            result = cloudsearchdomain.search(query=task['artist'], queryOptions='{"fields":["artist"]}', size=500)
            #result = amazon_music_table.query(IndexName='artist-index', KeyConditionExpression=Key('artist').eq(task['artist'].title()))

            #count = result['Count'] #amazondb

            if result['hits']['found']:
                master.stop()
                master.clear_queue()
                #songs = result['Items'] #amazondb
                tracks = result['hits']['hit']
                count = len(tracks)
                print "track count =",count
                k = number if number <= count else count
                for j in range(k):
                    n = random.randint(0, count-1)
                    #song = songs[n]
                    song = tracks[n]['fields']
                    try:
                        print 'artist: ' + song.get('artist', 'No artist')[0]
                        print 'album: ' + song.get('album', 'No album')[0]
                        print 'song: ' + song.get('title', 'No title')[0]
                    except Exception as e:
                        print "Unicode error"
                    uri = song.get('uri', '')[0]
                    print 'uri: ' + uri
                    print '---------------------------------------------------------------'

                    if 'amz' in uri:
                        i = uri.find('amz')
                        ii = uri.find('.')
                        id_ = uri[i:ii]
                        meta = didl_amazon.format(id_=id_)
                    else:
                        i = uri.find('.')+1
                        ii = uri.find('.',i)
                        id_ = uri[i:ii]
                        meta = didl_rhapsody.format(id_=id_)

                    print '---------------------------------------------------------------'
                    print 'meta: ',meta
                    my_add_to_queue('', meta)

                master.play_from_queue(0)

        elif action == 'pause':
            master.pause()

        elif action == 'resume':
            master.play()

        elif action == 'skip':
            try:
                master.next()
            except soco.exceptions.SoCoUPnPException as e:
                print "Probably tried to do 'next' when not possible:", e

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

    ###########################################################################################
    # Below is the check if the track has changed and if so it is scrobbled to dynamodb
    try:
        state = master.get_current_transport_info()['current_transport_state']
    except (requests.exceptions.ConnectionError, soco.exceptions.SoCoUPnPException) as e:
        state = 'ERROR'
        print "Encountered error in state = master.get_current transport_info(): ", e

    # check if sonos is playing music and, if not, do nothing
    track = master.get_current_track_info()
    if state != 'PLAYING' or 'tunein' in track.get('uri', ''):
        continue
            
    print "{} checking to see if track has changed".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    
    if prev_title != track.get('title') and track.get('artist'): 
        
        prev_title = track.get('title') 

        # Write the latest scrobble to dynamodb 'scrobble_new'
        data = {
                'location':'nyc',
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
    ###########################################################################################

    sleep(0.5)

