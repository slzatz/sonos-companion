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
import pysolr

parser = argparse.ArgumentParser(description='Command line options ...')
parser.add_argument('--player', '-p', default='all', help="This is the name of the player you want to control or all")
args = parser.parse_args()

s3 = boto3.resource('s3')
object = s3.Object('sonos-scrobble','location')
location = object.get()['Body'].read()
print("The current location is {}".format(location))

sqs = boto3.resource('sqs', region_name='us-east-1') 
queue_name = 'echo_sonos_ct' if location=='ct' else 'echo_sonos'
sqs_queue = sqs.get_queue_by_name(QueueName=queue_name) 

solr = pysolr.Solr(c.ec_uri+':8983/solr/sonos_companion/', timeout=10)
    
config.CACHE_ENABLED = False

print "\n"
n = 0
while 1:
    n+=1
    print "attempt "+str(n)
    sp = soco.discover(timeout=5)
    if sp:
        break
    else:
        sleep(1) 

if args.player=='all':
    d = {}
    print "\nSpeakers->"
    for s in sp:
        print s.player_name
        gc = s.group.coordinator
        d[gc] = d[gc] + 1 if gc in d else 1

    print "\nGroup Coordinators->"
    for gc in d:
        print "{}:{}".format(gc.player_name, d[gc])

    master = max(d.keys(), key=lambda k: d[k])

else:
    for s in sp:
        if s.player_name==args.player:
            master = s
            break
    else:
        print "{} is not a speaker".format(args.player)
        sys.exit(1)

print "\nmaster = ", master.player_name

print "\nprogram running ..."

meta_format_pandora = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="OOOX52876609482614338" parentID="0" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

meta_format_radio = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="-1" parentID="-1" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItem.audioBroadcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

didl_amazon = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="00030020{id_}" parentID="" restricted="true"><dc:title></dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON6663_X_#Svc6663-0-Token</desc></item></DIDL-Lite>'''

didl_rhapsody = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="RDCPI:GLBTRACK:Tra.{id_}" parentID="-1" restricted="true"><dc:title></dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">''' + '''SA_RINCON1_{}</desc></item></DIDL-Lite>'''.format(c.user_id)

#uri = "x-sonos-http:library%2fartists%2fAmanda%252520Shires%2fCarrying%252520Lightning%2fca20888a-1a68-484a-ac90-058e53b13084%2f.mp4?sid=201&flags=8224&sn=5"
#id_ = "library%2fartists%2fAmanda%252520Shires%2fCarrying%252520Lightning%2fca20888a-1a68-484a-ac90-058e53b13084%2f"
didl_library = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="00032020{id_}" parentID="-1" restricted="true"><dc:title></dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON51463_X_#Svc51463-0-Token</desc></item></DIDL-Lite>'''

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
            ('EnqueuedURI', uri),
            ('EnqueuedURIMetaData', metadata),
            ('DesiredFirstTrackNumberEnqueued', 0),
            ('EnqueueAsNext', 1)
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

        #elif action in ('play','add') and task.get('trackinfo'): 
        elif action in ('play','add') and task.get('title'):

            #from echo_check2 -- trackinfo = "{} {}".format(artist, title) - so right now not distinguishing between title and artist but probably should
            #The query below only searches title and artist fields so you don't get every song on After the Gold Rush
            #s = 'artist:' + ' artist:'.join(task['trackinfo'].split()) + ' title:' + ' title:'.join(task['trackinfo'].split())
            s = 'title:' + ' AND title:'.join(task['title'].split())
            if task['artist']:
                s = s + ' artist:' + ' AND artist:'.join(task['artist'].split())
            result = solr.search(s, **{'rows':1}) # or rows=1

            if len(result):
                track = result.docs[0]
                try:
                    print 'artist: ' + track.get('artist', 'No artist')
                    print 'album: ' + track.get('album', 'No album')
                    print 'song: ' + track.get('title', 'No title')
                except Exception as e:
                    print "Unicode error"
                uri = track.get('uri', '')
                print 'uri: ' + uri
                print "---------------------------------------------------------------"

                if 'amz' in uri:
                    i = uri.find('amz')
                    ii = uri.find('.')
                    id_ = uri[i:ii]
                    meta = didl_amazon.format(id_=id_)
                elif 'library' in uri:
                    i = uri.find('library')
                    ii = uri.find('.')
                    id_ = uri[i:ii]
                    meta = didl_library.format(id_=id_)
                else:
                    i = uri.find('.')+1
                    ii = uri.find('.',i)
                    id_ = uri[i:ii]
                    meta = didl_rhapsody.format(id_=id_)

                print 'meta: ',meta
                print '---------------------------------------------------------------'

                if action == 'play':
                    master.stop()
                    master.clear_queue()
                    my_add_to_queue('', meta)
                    master.play_from_queue(0)

                else:
                    my_add_to_queue('', meta)

            else:
                print "Could not find requested track " + task['title'] + ' by ' + task['artist']

        elif action == 'play_album' and task.get('album'): 

            s = 'album:' + ' AND album:'.join(task['album'].split())
            result = solr.search(s, **{'rows':25}) #only brings back actual matches but 25 seems like max for most albums

            if len(result):
                master.stop()
                master.clear_queue()
                for track in result:
                    try:
                        print 'artist: ' + track.get('artist', 'No artist')
                        print 'album: ' + track.get('album', 'No album')
                        print 'song: ' + track.get('title', 'No title')
                    except Exception as e:
                        print "Unicode error"
                    uri = track.get('uri', '')
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
                print "Could not find requested album " + task['album']

        elif action == 'shuffle' and task.get('artist') and task.get('number'):

            try:
                number = int(task['number'])
            except ValueError as e:
                print e
                number = 8

            s = 'artist:' + ' AND artist:'.join(task['artist'].split())
            result = solr.search(s, **{'rows':500}) 

            count = len(result)
            print "Total track count for {} was {}".format(task['artist'], count)

            if count:
                master.stop()
                master.clear_queue()
                tracks = result.docs
                k = number if number <= count else count
                picks = []
                for j in range(k):
                    while 1:
                        n = random.randint(0, count-1) if count > number else j
                        if not n in picks:
                            picks.append(n)
                            break
                    track = tracks[n]
                    try:
                        print 'artist: ' + track.get('artist', 'No artist')
                        print 'album: ' + track.get('album', 'No album')
                        print 'song: ' + track.get('title', 'No title')
                    except Exception as e:
                        print "Unicode error"
                    uri = track.get('uri', '')
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

                    #print '---------------------------------------------------------------'
                    #print 'meta: ',meta
                    my_add_to_queue('', meta)

                master.play_from_queue(0)

        elif  action in ('pause', 'resume', 'skip'):
            d= {'pause':'pause', 'resume':'play', 'skip':'next'}
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

        else:
            print "I have no idea what you said"

    sleep(0.5)

