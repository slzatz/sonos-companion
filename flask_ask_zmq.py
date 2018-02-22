'''
This is a python 2.7 program that is usually run on a raspberry pi
It receives task dictionaries via json from flask_ask_sonos.py

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
from time import time, sleep
import random
import json
import sys
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + sys.path
import soco
from soco import config as soco_config
from config import user_id, last_fm_api_key 
import zmq
import requests

soco_config.CACHE_ENABLED = False

#last.fm 
base_url = "http://ws.audioscrobbler.com/2.0/"

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
    print "{} -- coordinator: {}".format(s.player_name.encode('ascii', 'ignore'), s.group.coordinator.player_name.encode('ascii', 'ignore')) 

master_name = raw_input("Which speaker do you want to be master? ")
master = sp_names.get(master_name)
if master:
    if not master.is_coordinator:
        print "\nThe speaker you selected --{}-- is not the master of any group, so will unjoin it".format(master.player_name)
        master.unjoin()
        #sys.exit(1)
    print "\nMaster speaker is: {}".format(master.player_name) 
    print "\nMaster group:"
    for s in master.group.members:
        print "{} -- coordinator: {}".format(s.player_name.encode('ascii', 'ignore'), s.group.coordinator.player_name.encode('ascii', 'ignore')) 

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

#not in use
#uri = "radea:Tra.2056353.mp3?sn=3",
#id_ = "2056353
#didl_rhapsody = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="RDCPI:GLBTRACK:Tra.{id_}" parentID="-1" restricted="true"><dc:title></dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">''' + '''SA_RINCON1_{}</desc></item></DIDL-Lite>'''.format(user_id)

#main format in use`
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

# the 'action' functions
def what_is_playing():
    try:
        state = master.get_current_transport_info()['current_transport_state']
    except Exception as e:
        print "Encountered error in state = master.get_current_transport_info(): ", e
        state = 'error'

    # check if sonos is playing something
    if state == 'PLAYING':
        try:
            track = master.get_current_track_info()
        except Exception as e:
            print "Encountered error in track = master.get_current_track_info(): ", e
            output_speech = "I encountered an error trying to get current track info."
        else:
            output_speech = "The song is {}. The artist is {} and the album is {}.".format(track.get('title','No title'), track.get('artist', 'No artist'), track.get('album', 'No album'))
    else:
        output_speech = "Nothing appears to be playing right now, Steve"

    socket.send(output_speech)

def turn_volume(volume):
    #for s in m_group:
    for s in master.group.members:
        s.volume = s.volume - 10 if volume=='quieter' else s.volume + 10

def set_volume(level):
    #for s in m_group:
    for s in master.group.members:
        s.volume = level

def mute(bool_):
    #for s in m_group:
    for s in master.group.members:
        s.mute = bool_

def playback(type_):
    try:
        getattr(master, type_)()
    except soco.exceptions.SoCoUPnPException as e:
        print "master.{}:".format(type_), e

def play(add, uris):
    # must be a coordinator and possible that it stopped being a coordinator after launching program
    if not master.is_coordinator:
        master.unjoin()

    if not add:
    # with check on is_coordinator may not need the try/except
        try:
            master.stop()
            master.clear_queue()
        except (soco.exceptions.SoCoUPnPException,soco.exceptions.SoCoSlaveException) as e:
            print "master.stop or master.clear_queue exception:", e


    for uri in uris:
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

    if not add:
    # with check on is_coordinator may not need the try/except
        try:
            master.play_from_queue(0)
        except (soco.exceptions.SoCoUPnPException, soco.exceptions.SoCoSlaveException) as e:
            print "master.play_from_queue exception:", e

def recent_tracks():
    # right now look back is one week; note can't limit because you need all the tracks since we're doing the frequency count
    payload = {'method':'user.getRecentTracks', 'user':'slzatz', 'format':'json', 'api_key':last_fm_api_key, 'from':int(time())-604800} #, 'limit':10}
    
    try:
        r = requests.get(base_url, params=payload)
        z = r.json()['recenttracks']['track']
    except Exception as e:
        print "Exception in get_scrobble_info: ", e
        z = []

    if z:
        dic = {}
        for d in z:
            dic[d['album']['#text']+'_'+d['name']] = dic.get(d['album']['#text']+'_'+d['name'],0) + 1

        a = sorted(dic.items(), key=lambda x:(x[1],x[0]), reverse=True) 

        current_album = ''
        output_speech = "During the last week you listened to the following tracks"
        # if you wanted to limit the number of tracks that were reported on, could do it here
        for album_track,count in a[:10]: #[:10]
            album,track = album_track.split('_')
            if current_album == album:
                line = ", {} ".format(track)
            else:
                line = ". From {}, {} ".format(album,track)
                current_album = album
            
            if count==1:
                count_phrase = ""
            elif count==2:
                count_phrase = "twice"
            else:
                count_phrase = str(count)+" times"

            output_speech += line + count_phrase

    else:
        output_speech = "I could  not retrieve recently played tracks or there aren't any."

    socket.send(output_speech)

def play_station(station):
    station = STATIONS.get(station.lower())
    if station:
        uri = station[1]
        print "radio station uri=",uri
        if uri.startswith('pndrradio'):
            meta = meta_format_pandora.format(title=station[0], service=station[2])
            master.play_uri(uri, meta, station[0]) # station[0] is the title of the station
        elif uri.startswith('x-sonosapi-stream'):
            uri = uri.replace('&', '&amp;') # need to escape '&' in radio URIs
            meta = meta_format_radio.format(title=station[0], service=station[2])
            master.play_uri(uri, meta, station[0]) # station[0] is the title of the station

def list_queue():
    queue = master.get_queue()

    if len(queue) == 0:
        output_speech = "There is nothing in the queue"
    else:
        output_speech = ""
        for track in queue[:10]: # just pulling first 10
            output_speech+="{} from {} by {}, ".format(track.title, track.album, track.creator)

    socket.send(output_speech)

def clear_queue():
    try:
        master.clear_queue()
    except Exception as e:
        print "Encountered exception when trying to clear the queue:",e

#actions = {'play':play, 'turn_volume':turn_volume, 'set_volume':set_volume, 'playback':playback, 'what_is_playing':what_is_playing, 'recent_tracks':recent_tracks, 'play_station':play_station, 'list_queue': list_queue, 'clear_queue':clear_queue, 'mute':mute} 

while True:
    try:
        print 'waiting for message'
        msg = socket.recv_json()
        print msg
        action = msg.pop('action')
        # what_is_playing and recent_tracks have to do processing and return a response to flask_ask_sonos.py
        if action not in ('what_is_playing', 'recent_tracks', 'list_queue'):
            socket.send('OK')
        #actions[action](**msg) #could use locals() or eval and do away with actions but actions lets you see the list of actions
        eval(action)(**msg) #trying with eval
    except KeyboardInterrupt:
        sys.exit()

