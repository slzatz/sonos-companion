'''
created to have a python2.7 version of echo check that uses solr
uses pysolr while the python3 version:  echo_check_solr.py uses SolrClient

uses boto3
uses dynamodb for radio stations and shuffling songs
uses solr and pysolr, which works on python 2.7 to enable searching on tracks and artists

PlayStation play {myartist} radio
PlayStation play {myartist} pandora
PlayStation play {myartist} station
PlayTrack play {mytitle} by {myartist}
AddTrack add {mytitle} by {myartist}
Shuffle shuffle {myartist}
WhatIsPlaying what is playing
WhatIsPlaying what song is playing
Skip skip
Skip next
PlayAlbum play album {myalbum}
PauseResume {pauseorresume} the music
TurnTheVolume Turn the volume {volume}
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

    >>> z = solr.search("artist:Cat AND artist:Stevens")
    >>> z
    <pysolr.Results object at 0x02C792F0>
    >>> for r in z:
    ...     print r['title'],r['album'],r['artist'],r['uri']

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
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + sys.path
import soco
from soco import config
import boto3 
import config as c
#import pysolr

parser = argparse.ArgumentParser(description='Command line options ...')
parser.add_argument('--player', '-p', default='all', help="This is the name of the player you want to control or all")
args = parser.parse_args()

s3 = boto3.resource('s3')
s3object = s3.Object('sonos-scrobble','location')
location = s3object.get()['Body'].read()
print("The current location is {}".format(location))

sqs = boto3.resource('sqs', region_name='us-east-1') 
queue_name = 'echo_sonos_ct' if location=='ct' else 'echo_sonos'
sqs_queue = sqs.get_queue_by_name(QueueName=queue_name) 

#solr = pysolr.Solr(c.ec_uri+':8983/solr/sonos_companion/', timeout=10)
    
config.CACHE_ENABLED = False

n = 0
while 1:
    n+=1
    print "attempt "+str(n) 
    try:
        sp = soco.discover(timeout=2)
        speakers = {s.player_name:s for s in sp}
    except TypeError as e:    
        print e 
        sleep(1)       
    else:
        break 
    
for sn in speakers:
        print "{} -- coordinator:{}".format(sn, speakers[sn].group.coordinator.player_name) 

master_name = raw_input("Which speaker do you want to be master? ")
master = speakers.get(master_name)
if master:
    print "Master speaker is: {}".format(master.player_name) 
else:
    print "Somehow you didn't pick a master or spell it correctly (case matters)" 
    sys.exit(1)

print "\nprogram running ..."

meta_format_pandora = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="OOOX52876609482614338" parentID="0" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

meta_format_radio = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="-1" parentID="-1" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItem.audioBroadcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

#uri = "x-sonos-http:amz%3atr%3a6b5d9c09-7dbe-44bc-89e1-85ac5ed45093.mp3?sid=26&flags=8224&sn=1",
#id_ = "amz%3atr%3a6b5d9c09-7dbe-44bc-89e1-85ac5ed45093
didl_amazon = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="00030020{id_}" parentID="" restricted="true"><dc:title></dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON6663_X_#Svc6663-0-Token</desc></item></DIDL-Lite>'''

#uri = "radea:Tra.2056353.mp3?sn=3",
#id_ = "2056353
didl_rhapsody = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="RDCPI:GLBTRACK:Tra.{id_}" parentID="-1" restricted="true"><dc:title></dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">''' + '''SA_RINCON1_{}</desc></item></DIDL-Lite>'''.format(c.user_id)

#uri = "x-sonos-http:library%2fartists%2fAmanda%252520Shires%2fCarrying%252520Lightning%2fca20888a-1a68-484a-ac90-058e53b13084%2f.mp4?sid=201&flags=8224&sn=5"
#id_ = "library%2fartists%2fAmanda%252520Shires%2fCarrying%252520Lightning%2fca20888a-1a68-484a-ac90-058e53b13084%2f"
didl_library = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="00032020{id_}" parentID="" restricted="true"><dc:title></dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON51463_X_#Svc51463-0-Token</desc></item></DIDL-Lite>'''

#uri = "x-rincon-cpcontainer:0006206clibrary%2fplaylists%2f7c7704e9-04b6-431a-afe6-c5db44cb77f1%2f%23library_playlist"
#id_ = "0006206clibrary%2fplaylists%2f7c7704e9-04b6-431a-afe6-c5db44cb77f1%2f%23library_playlist"
#for playlists metadata does not need to include any value for title or parent but unlike tracks, you do need to pass the uri to add_playlist_to_queue
#for the record for An Unarmorial Age, the parentID was "00082064library%2fplaylists%2f%23library_playlists"
didl_library_playlist = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="{id_}" parentID="" restricted="true"><dc:title></dc:title><upnp:class>object.container.playlistContainer</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON51463_X_#Svc51463-0-Token</desc></item></DIDL-Lite>'''

with open('deborah_albums') as f:
    z = f.read()
#DEBORAH_ALBUMS = list(json.loads(z).items())
z = json.loads(z)
DEBORAH_TRACKS = []
for x in z:
    DEBORAH_TRACKS.extend(z[x])

def play_deborah_radio(num):

    songs = []

    master.stop()
    master.clear_queue()

    for x in range(num):
        n = random.randint(0,len(DEBORAH_TRACKS)-1)
        songs.append(DEBORAH_TRACKS[n])

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

with open('stations') as f:
    z = f.read()

STATIONS = json.loads(z)

def my_add_to_queue(uri, metadata):
    response = master.avTransport.AddURIToQueue([
            ('InstanceID', 0),
            ('EnqueuedURI', uri), #x-sonos-http:library ...
            ('EnqueuedURIMetaData', metadata),
            ('DesiredFirstTrackNumberEnqueued', 0),
            ('EnqueueAsNext', 1)
            ])
    qnumber = response['FirstTrackNumberEnqueued']
    return int(qnumber)

def my_add_playlist_to_queue(uri, metadata):
    response = master.avTransport.AddURIToQueue([
            ('InstanceID', 0),
            ('EnqueuedURI', uri), #x-rincon-cpcontainer:0006206clibrary
            ('EnqueuedURIMetaData', metadata),
            ('DesiredFirstTrackNumberEnqueued', 0),
            ('EnqueueAsNext', 0) #0
            ])
    qnumber = response['FirstTrackNumberEnqueued']
    return int(qnumber)
prev_title = ''
COMMON_ACTIONS = {'pause':'pause', 'resume':'play', 'skip':'next'}

while 1:
    
    print "{} checking sqs queue; {}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), master.player_name)

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

        if action == 'deborah':
            play_deborah_radio(20)         
    
        elif action == 'radio' and task.get('station'):

            if task['station'].lower() == 'deborah':
                play_deborah_radio(20)
            else:
                station = STATIONS.get(task['station'].lower())
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
                    print "{} radio is not a preset station.".format(task['station'])

        elif action in ('play','add') and task.get('uris'):
            if action == 'play':
                master.stop()
                master.clear_queue()

            for uri in task['uris']:
                print 'uri: ' + uri
                print "---------------------------------------------------------------"
                playlist = False
                if 'amz' in uri:
                    i = uri.find('amz')
                    ii = uri.find('.')
                    id_ = uri[i:ii]
                    meta = didl_amazon.format(id_=id_)
                elif 'library_playlist' in uri:
                    i = uri.find(':')
                    id_ = uri[i+1:]
                    meta = didl_library_playlist.format(id_=id_)
                    playlist = True
                elif 'library' in uri:
                    i = uri.find('library')
                    ii = uri.find('.')
                    id_ = uri[i:ii]
                    meta = didl_library.format(id_=id_)
                elif 'radea' in uri:
                    i = uri.find('.')+1
                    ii = uri.find('.',i)
                    id_ = uri[i:ii]
                    meta = didl_rhapsody.format(id_=id_)
                else:
                    print 'The uri:{}, was not recognized'.format(uri)
                    continue

                print 'meta: ',meta
                print '---------------------------------------------------------------'

                if not playlist:
                    my_add_to_queue('', meta)
                else:
                    # unlike adding a track to the queue, you need the uri
                    my_add_playlist_to_queue(uri, meta)

            if action == 'play':
                master.play_from_queue(0)

        elif  action in ('pause', 'resume', 'skip'):
            #d= {'pause':'pause', 'resume':'play', 'skip':'next'}
            try:
                getattr(master, COMMON_ACTIONS[action])()
            except soco.exceptions.SoCoUPnPException as e:
                print "master.{}:".format(action), e

        elif action in ('quieter','louder'):
            volume = master.volume
            
            new_volume = volume - 10 if action=='quieter' else volume + 10
            
            if args.player == 'all':
                for s in sp:
                    s.volume = new_volume
            else:
                master.volume = new_volume

            print "args.player=",args.player
            print "I tried to make the volume "+action
        elif action == 'get sonos queue':
            s3object = s3.Object('sonos-scrobble','queue')
            queue = []            
            sonos_queue = master.get_queue()
            for track in sonos_queue:
                title = track.title
                album = track.album
                #artist = track.creator #this works just not using artist for my sonos-companion playlists
                id_ = album + ' ' + title
                id_ = id_.replace(' ', '_')
                uri = track.resources[0].uri
                #try:
                #    print('\n')
                #    print(n)
                #    print('id: ' + id_)
                #    print('artist: ' + artist)
                #    print('album: ' + album)
                #    print('song: ' + title)
                #    print('uri: ' + track['uri'])
                #except Exception as e:
                #    print(e)
                #print('---------------------------------------------------------------')
                queue.append((id_, uri))
                response = s3object.put(Body=json.dumps(queue))
                print("response to s3 put =",response)

        else:
            print "I have no idea what you said"

    sleep(0.5)

