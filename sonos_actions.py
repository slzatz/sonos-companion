'''
This is a python 3 script that is imported by sonos_cli2.py and sonos_server.py
and contains the SoCo functionality that the importing script needs

it uses the xml format that sonos uses to interact with Amazon music

current_track = master.get_current_track_info() --> {
            u'album': 'We Walked In Song', 
            u'artist': 'The Innocence Mission', 
            u'title': 'My Sisters Return From Ireland', 
            u'uri': 'pndrradio-http://audio-sv5-t3-1.pandora.com/access/5459257820921908950?version=4&lid=86206018&token=...', 
            u'playlist_position': '3', 
            u'duration': '0:02:45', 
            u'position': '0:02:38', 
            u'album_art': 'http://cont-ch1-2.pandora.com/images/public/amz/3/2/9/3/655037093923_500W_500H.jpg'}

If track is Prime, then url is:
x-sonosapi-hls-static:catalog%2ftracks%2fB01E0N3W66%2f%3falbumAsin%3dB01E0N386A?sid=201&flags=0&sn=1
x-sonosapi-hls-static:catalog/tracks/B01E0N3W66/?albumAsin?B01E0N386A?sid=201&flags=0&sn=1

If track is Prime but moved to my music (but not purchased) then url is (and generally metadata works):
x-sonosapi-hls-static:library%2fartists%2fThe_20Avett_20Brothers%2fI_20And_20Love_20And_20You%2ff9aa6eac-6707-44bc-99ff-3aa2e5938d12%2f?sid=201&flags=0&sn=1' 

If track has been purchased from Amazon:
x-sonos-http:library%2fartists%2fThe_20Avett_20Brothers%2fI_20And_20Love_20And_20You%2ff9aa6eac-6707-44bc-99ff-3aa2e5938d12%2f.mp3?sid=201&flags=0&sn=1' 
x-sonos-http:library/artists/The_20Avett_20Brothers/I_20And_20Love_20And_20You/f9aa6eac-6707-44bc-99ff-3aa2e5938d12%2f.mp3?sid=201&flags=0&sn=1' 

if track was put on queue as part of a playlist
x-sonos-http:library%2fplaylist%2f28f452a4-3414-456d-9146-9e9063868963%2f067b7994-615b-4f12-850b-4f12-850b-...mp3?sid...
x-sonos-http:library/playlist/28f452a4-3414-456d-9146-9e9063868963%2f067b7994-615b-4f12-850b-4f12-850b-...mp3?sid...


actions = {'play':play, 'turn_volume':turn_volume, 'set_volume':set_volume, 'playback':playback, 'what_is_playing':what_is_playing, 'recent_tracks':recent_tracks, 'play_station':play_station, 'list_queue': list_queue, 'clear_queue':clear_queue, 'mute':mute} 

'''

import os
from time import time, sleep
import json
import sys
import random
import pysolr
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + sys.path
import soco
from soco import config as soco_config
from config import solr_uri
from sonos_config import STATIONS, META_FORMAT_PANDORA, META_FORMAT_RADIO, \
                         DIDL_LIBRARY_PLAYLIST, DIDL_AMAZON, ARTISTS

soco_config.CACHE_ENABLED = False

solr = pysolr.Solr(solr_uri+'/solr/sonos_companion/', timeout=10) 

#last.fm 
#base_url = "http://ws.audioscrobbler.com/2.0/"

# the meta formats should be imported from sonos_config
# pandora format changed at some point and was updated on 05302018
# format is "x-sonosapi-radio:ST:138764603804051010?sid=236&amp;flags=8300&amp;sn=2"
# numeric part is the url of the station if you access through pandora web site
# note that the parameters following the ? appear to be necessary
meta_format_pandora = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="100c206cST:52876609482614338" parentID="10082064myStations" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItem.audioBroadcast.#station</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON60423_X_#Svc60423-0-Token</desc></item></DIDL-Lite>'''

meta_format_radio = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="-1" parentID="-1" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItem.audioBroadcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON65031_</desc></item></DIDL-Lite>'''

# a few songs were moved off playlist that I should just get rid of
didl_library_playlist = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="{id_}" parentID="" restricted="true"><dc:title></dc:title><upnp:class>object.container.playlistContainer</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON51463_X_#Svc51463-0-Token</desc></item></DIDL-Lite>'''

#this is the current format (06252018) that works for my uploaded music and
#music bought from Amazon and for music moved from prime and left in prime
didl_amazon = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="10030000{id_}" parentID="" restricted="true"><dc:title></dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON51463_X_#Svc51463-0-Token</desc></item></DIDL-Lite>'''

def get_sonos_players():
    # master is assigned in sonos_cli2.py
    n = 0
    sp = None
    while n < 10:
        n+=1
        #print("attempt "+str(n)) 
        try:
            sp = soco.discover(timeout=2)
            #sp_names = {s.player_name:s for s in sp}
        except TypeError as e:    
            print(e) 
            sleep(1)       
        else:
            break 
    return sp    

def my_add_to_queue(uri, metadata):
    # generally don't need the uri (can be passed as '') although passing it in
    try:
        response = master.avTransport.AddURIToQueue([
                ('InstanceID', 0),
                ('EnqueuedURI', uri), #x-sonos-http:library ...
                ('EnqueuedURIMetaData', metadata),
                ('DesiredFirstTrackNumberEnqueued', 0),
                ('EnqueueAsNext', 1)
                ])
    except soco.exceptions.SoCoUPnPException as e:
        print("my_add_to_queue exception:", e)
        print("uri:", uri)
        print("metadata:", metadata)
        return 0
    else:
        qnumber = response['FirstTrackNumberEnqueued']
        return int(qnumber)

#def my_add_playlist_to_queue(uri, metadata):
#    try:
#        response = master.avTransport.AddURIToQueue([
#                ('InstanceID', 0),
#                ('EnqueuedURI', uri), #x-rincon-cpcontainer:0006206clibrary
#                ('EnqueuedURIMetaData', metadata),
#                ('DesiredFirstTrackNumberEnqueued', 0),
#                ('EnqueueAsNext', 0) #0
#                ])
#    except soco.exceptions.SoCoUPnPException as e:
#        print("my_add_to_queue exception:", e)
#        return 0
#    else:
#        qnumber = response['FirstTrackNumberEnqueued']
#        return int(qnumber)

# the 'action' functions
def current_track_info(text=True):
    try:
        state = master.get_current_transport_info()['current_transport_state']
    except Exception as e:
        print("Encountered error in state = master.get_current_transport_info(): ", e)
        state = 'ERROR'

    # check if sonos is playing something
    if state == 'PLAYING':
        try:
            track = master.get_current_track_info()
        except Exception as e:
            print("Encountered error in track = master.get_current_track_info(): ", e)
            response = "I encountered an error trying to get current track info."
        else:
            title = track.get('title', '')
            artist = track.get('artist', '')
            album = track.get('album', '')
            if text:
                response = f"The track is {title}, the artist is {artist} and the album is {album}."
            else:
                response = {'title':title, 'artist':artist, 'album':album}
    else:
        #response = "Nothing appears to be playing right now, Steve"
        response = None

    return response

def current():
    try:
        state = master.get_current_transport_info()['current_transport_state']
    except Exception as e:
        print("Encountered error in state = master.get_current_transport_info(): ", e)
        state = 'error'

    # check if sonos is playing something
    if state == 'PLAYING':
        try:
            track = master.get_current_track_info()
        except Exception as e:
            print("Encountered error in track = master.get_current_track_info(): ", e)
            return

        return track

def turn_volume(volume):
    for s in master.group.members:
        s.volume = s.volume - 10 if volume=='quieter' else s.volume + 10

def set_volume(level):
    for s in master.group.members:
        s.volume = level

def mute(bool_):
    for s in master.group.members:
        s.mute = bool_

def unjoin():
    for s in master.group.members:
        s.unjoin()

def play_from_queue(pos):
    try:
        master.play_from_queue(pos)
    except (soco.exceptions.SoCoUPnPException, soco.exceptions.SoCoSlaveException) as e:
        print("master.play_from_queue exception:", e)
    
def playback(type_):
    try:
        getattr(master, type_)()
    except soco.exceptions.SoCoUPnPException as e:
        print("master.{}:".format(type_), e)
        if type_ == 'play':
            try:
                master.play_from_queue(0)
            except (soco.exceptions.SoCoUPnPException, soco.exceptions.SoCoSlaveException) as e:
                print("master.play_from_queue exception:", e)

def play(add, uris):
    # must be a coordinator and possible that it stopped being a coordinator
    # after launching program
    if not master.is_coordinator:
        master.unjoin()

    if not add:
    # with check on is_coordinator may not need the try/except
        try:
            master.stop()
            master.clear_queue()
        except (soco.exceptions.SoCoUPnPException,soco.exceptions.SoCoSlaveException) as e:
            print("master.stop or master.clear_queue exception:", e)

    for uri in uris:
        #print('uri: ' + uri)
        #print("---------------------------------------------------------------")

        # a few songs from Deborah album Like You've Never Seen Water are a playlist
        if 'library_playlist' in uri:
            i = uri.find(':')
            id_ = uri[i+1:]
            meta = DIDL_LIBRARY_PLAYLIST.format(id_=id_)
        elif 'library' in uri and not 'static' in uri:
            # this is a bought track and question uploaded one?
            i = uri.find('library')
            ii = uri.find('.')
            id_ = uri[i:ii]
            meta = DIDL_AMAZON.format(id_=id_)
        elif 'static:library' in uri: # and 'static' in uri:
            # track moved from Prime into my account but not paid for
            i = uri.find('library')
            ii = uri.find('?')
            id_ = uri[i:ii]
            meta = DIDL_AMAZON.format(id_=id_)
        elif 'static:catalog' in uri: # and 'catalog' in uri:
            # track sitting in Prime not moved to my music
            i = uri.find('catalog')
            ii = uri.find('?')
            id_ = uri[i:ii]
            meta = DIDL_AMAZON.format(id_=id_)
        else:
            print(f'The uri:{uri} was not recognized')
            continue

        #print('meta: ',meta)
        #print('---------------------------------------------------------------')

        my_add_to_queue(uri, meta)

    queue = master.get_queue()
        # with check on is_coordinator may not need the try/except
    try:
        master.play_from_queue(len(queue) - 1)
    except (soco.exceptions.SoCoUPnPException, soco.exceptions.SoCoSlaveException) as e:
        print("master.play_from_queue exception:", e)

def play_station(station):
    station = STATIONS.get(station.lower())
    if station:
        uri = station[1]
        #print("radio station uri=",uri)
        if uri.startswith('x-sonosapi-radio'):
            meta = meta_format_pandora.format(title=station[0])
        elif uri.startswith('x-sonosapi-stream'):
            meta = META_FORMAT_RADIO.format(title=station[0])

        master.play_uri(uri, meta, station[0]) # station[0] is the title of the station

def list_queue():
    queue = master.get_queue()
    response = []
    for t in queue:
        if type(t) == soco.data_structures.DidlMusicTrack:
            #response.append(f"{t.title} from {t.album} by {t.creator}")
            response.append(f"{t.title}")
        else:
            response.append(f"{t.metadata['title']} (MSTrack)")
    #response = [f"{t.title} by {t.artist}" for t in queue]
    #response = [f"{t}" for t in queue]
    #response = [f"{type(t)} -- {dir(t)}" for t in queue]
    return response

def clear_queue():
    try:
        master.clear_queue()
    except Exception as e:
        print("Encountered exception when trying to clear the queue:",e)

def shuffle(artist):
    if not artist:
        return

    s = 'artist:' + ' AND artist:'.join(artist.split())
    result = solr.search(s, fl='album,title,uri', rows=500) 
    count = len(result)
    if not count:
        return f"I couldn't find any tracks for {artist}"

    #print(f"Total track count for {artist} was {count}")
    tracks = result.docs
    k = 10 if count >= 10 else count
    selected_tracks = random.sample(tracks, k)
    uris = [t.get('uri') for t in selected_tracks]
    play(False, uris)
    titles = [t.get('title', '')+'-'+t.get('album', '') for t in selected_tracks]
    title_list = "\n".join([f"{t[0]}. {t[1]}" for t in enumerate(titles, start=1)])
    return f"Total track count for {artist} was {count}:\n{title_list}."

def play_pause():
    try:
        state = master.get_current_transport_info()['current_transport_state']
    except Exception as e:
        print("Encountered error in state = master.get_current_transport_info(): ", e)
        state = 'ERROR'

    # check if sonos is playing music
    if state == 'PLAYING':
        master.pause()
    elif state!='ERROR':
        master.play()
