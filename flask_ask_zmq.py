'''
This is a python 2.7 program that is usually run  on a raspberry pi
It receives task dictionaries from sonos_echo_app.py

current_track = master.get_current_track_info() --> {
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
from time import sleep
import random
import json
import sys
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + sys.path
import soco
from soco import config as soco_config
from config import user_id, solr_uri #location
import zmq
import pysolr

soco_config.CACHE_ENABLED = False

n = 0
while 1:
    n+=1
    print "attempt "+str(n) 
    try:
        sp = soco.discover(timeout=2)
        sp_names = {s.player_name:s for s in sp}
    except TypeError as e:    
        print e 
        sleep(1)       
    else:
        break 
    
for s in sp:
    print "{} -- coordinator:{}".format(s.player_name, s.group.coordinator.player_name) 

master_name = raw_input("Which speaker do you want to be master? ")
master = sp_names.get(master_name)
if master:
    print "Master speaker is: {}".format(master.player_name) 
    m_group = [s for s in sp if s.group.coordinator is master]
    print "Master group:"
    for s in m_group:
        print "{} -- coordinator:{}".format(s.player_name, s.group.coordinator.player_name) 

else:
    print "Somehow you didn't pick a master or spell it correctly (case matters)" 
    sys.exit(1)

print "\nprogram running ..."

context = zmq.Context()
socket = context.socket(zmq.REP)
#socket.bind('tcp://127.0.0.1:5555')
socket.bind('tcp://127.0.0.1:5554')

meta_format_pandora = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="OOOX52876609482614338" parentID="0" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

meta_format_radio = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="-1" parentID="-1" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItem.audioBroadcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

#uri = "x-sonos-http:amz%3atr%3a6b5d9c09-7dbe-44bc-89e1-85ac5ed45093.mp3?sid=26&flags=8224&sn=1",
#id_ = "amz%3atr%3a6b5d9c09-7dbe-44bc-89e1-85ac5ed45093
didl_amazon = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="00030020{id_}" parentID="" restricted="true"><dc:title></dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON6663_X_#Svc6663-0-Token</desc></item></DIDL-Lite>'''

#uri = "radea:Tra.2056353.mp3?sn=3",
#id_ = "2056353
didl_rhapsody = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="RDCPI:GLBTRACK:Tra.{id_}" parentID="-1" restricted="true"><dc:title></dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">''' + '''SA_RINCON1_{}</desc></item></DIDL-Lite>'''.format(user_id)

#uri = "x-sonos-http:library%2fartists%2fAmanda%252520Shires%2fCarrying%252520Lightning%2fca20888a-1a68-484a-ac90-058e53b13084%2f.mp4?sid=201&flags=8224&sn=5"
#id_ = "library%2fartists%2fAmanda%252520Shires%2fCarrying%252520Lightning%2fca20888a-1a68-484a-ac90-058e53b13084%2f"
didl_library = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="00032020{id_}" parentID="" restricted="true"><dc:title></dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON51463_X_#Svc51463-0-Token</desc></item></DIDL-Lite>'''

#uri = "x-rincon-cpcontainer:0006206clibrary%2fplaylists%2f7c7704e9-04b6-431a-afe6-c5db44cb77f1%2f%23library_playlist"
#id_ = "0006206clibrary%2fplaylists%2f7c7704e9-04b6-431a-afe6-c5db44cb77f1%2f%23library_playlist"
#for playlists metadata does not need to include any value for title or parent but unlike tracks, you do need to pass the uri to add_playlist_to_queue
#for the record for An Unarmorial Age, the parentID was "00082064library%2fplaylists%2f%23library_playlists"
didl_library_playlist = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="{id_}" parentID="" restricted="true"><dc:title></dc:title><upnp:class>object.container.playlistContainer</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON51463_X_#Svc51463-0-Token</desc></item></DIDL-Lite>'''

with open('stations') as f:
    z = f.read()

STATIONS = json.loads(z)

solr = pysolr.Solr(solr_uri+'/solr/sonos_companion/', timeout=10) #8983 is incorporated in the ngrok url

def my_add_to_queue(uri, metadata):
    try:
        response = master.avTransport.AddURIToQueue([
                ('InstanceID', 0),
                ('EnqueuedURI', uri), #x-sonos-http:library ...
                ('EnqueuedURIMetaData', metadata),
                ('DesiredFirstTrackNumberEnqueued', 0),
                ('EnqueueAsNext', 1)
                ])
    except soco.exceptions.SoCoUPnPException as e:
        print "my_add_to_queue exception:", e
        return 0
    else:
        qnumber = response['FirstTrackNumberEnqueued']
        return int(qnumber)

def my_add_playlist_to_queue(uri, metadata):
    try:
        response = master.avTransport.AddURIToQueue([
                ('InstanceID', 0),
                ('EnqueuedURI', uri), #x-rincon-cpcontainer:0006206clibrary
                ('EnqueuedURIMetaData', metadata),
                ('DesiredFirstTrackNumberEnqueued', 0),
                ('EnqueueAsNext', 0) #0
                ])
    except soco.exceptions.SoCoUPnPException as e:
        print "my_add_to_queue exception:", e
        return 0
    else:
        qnumber = response['FirstTrackNumberEnqueued']
        return int(qnumber)

COMMON_ACTIONS = {'pause':'pause', 'resume':'play', 'next':'next'}

def play_deborah_radio(k):
    s = 'album:(c)'
    result = solr.search(s, fl='uri', rows=600) 
    count = len(result)
    print "Total track count for Deborah tracks was {}".format(count)
    tracks = result.docs
    uris = []
    master.stop()
    master.clear_queue()
    for j in range(k):
        while 1:
            n = random.randint(0, count-1)
            uri = tracks[n]['uri']
            if not uri in uris:
                uris.append(uri)
                print 'uri: ' + uri
                print "---------------------------------------------------------------"
                if 'library' in uri:
                    i = uri.find('library')
                    ii = uri.find('.')
                    id_ = uri[i:ii]
                    meta = didl_library.format(id_=id_)
                else:
                    print 'The uri:{}, was not recognized'.format(uri)
                    break

                print 'meta: ',meta
                print '---------------------------------------------------------------'

                my_add_to_queue('', meta)
                break

    master.play_from_queue(0)

# The callback when echo_flask_ask_sonos.py sends a message
def on_message(task):
    print "in on message", task
    action = task.get('action', '')

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
            if 'library_playlist' in uri:
                i = uri.find(':')
                id_ = uri[i+1:]
                meta = didl_library_playlist.format(id_=id_)
                playlist = True
            elif 'library' in uri:
                i = uri.find('library')
                ii = uri.find('.')
                id_ = uri[i:ii]
                meta = didl_library.format(id_=id_)
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

    elif action in ('pause', 'resume', 'skip'):

        try:
            getattr(master, COMMON_ACTIONS[action])()
        except soco.exceptions.SoCoUPnPException as e:
            print "master.{}:".format(action), e

    elif action in ('quieter','louder'):
        
        for s in m_group:
            s.volume = s.volume - 10 if action=='quieter' else s.volume + 10

        print "I tried to make the volume "+action

    # At the moment this can't work because echo_flask_ask_sonos.py can't provide the response
    # ahead of this code
    elif action == "whatisplaying":
        try:
            state = master.get_current_transport_info()['current_transport_state']
        except Exception as e:
            print "Encountered error in state = master.get_current_transport_info(): ", e
            state = 'error'

        # check if sonos is playing music
        if state == 'PLAYING':
            try:
                track = master.get_current_track_info()
            except Exception as e:
                print "Encountered error in track = master.get_current_track_info(): ", e
                track = {}
            output_speech = "The song is {}. The artist is {} and the album is {}.".format(track.get('title','No title'), track.get('artist', 'No artist'), track.get('album', 'No album'))
        else:
            output_speech = "Nothing appears to be playing right now, Steve"

        socket.send(output_speech)

    else:
        print "I have no idea what you said"

while True:
    try:
        print 'waiting for message'
        msg = socket.recv_json()
        print msg
        print msg.get('action')
        print msg.get('action') == 'whatisplaying'
        if msg.get('action') != 'whatisplaying':
            print "Sending OK"
            socket.send('OK')
        on_message(msg)
    except KeyboardInterrupt:
        sys.exit()

