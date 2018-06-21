'''
This is a python 3 script that is imported by sonos_cli2.py and sonos_server.py
and contains the SoCo functionality that the importing script needs

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

If track is Prime but moved to my music (but not purchased) then url is (and generally metadata works):
x-sonosapi-hls-static:library%2fartists%2fThe_20Avett_20Brothers%2fI_20And_20Love_20And_20You%2ff9aa6eac-6707-44bc-99ff-3aa2e5938d12%2f?sid=201&flags=0&sn=1' 

If track has been purchased from Amazon:
x-sonos-http:library%2fartists%2fThe_20Avett_20Brothers%2fI_20And_20Love_20And_20You%2ff9aa6eac-6707-44bc-99ff-3aa2e5938d12%2f.mp3?sid=201&flags=0&sn=1' 

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

soco_config.CACHE_ENABLED = False

solr = pysolr.Solr(solr_uri+'/solr/sonos_companion/', timeout=10) 

#last.fm 
#base_url = "http://ws.audioscrobbler.com/2.0/"

# pandora format changed at some point and was updated on 05302018 using wireshark
# format is "x-sonosapi-radio:ST:138764603804051010?sid=236&amp;flags=8300&amp;sn=2"
# numeric part is the url of the station if you go to the pandora site
# the parameters appear to be important
meta_format_pandora = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="100c206cST:52876609482614338" parentID="10082064myStations" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItem.audioBroadcast.#station</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON60423_X_#Svc60423-0-Token</desc></item></DIDL-Lite>'''

meta_format_radio = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="-1" parentID="-1" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItem.audioBroadcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON65031_</desc></item></DIDL-Lite>'''

#meta_format_radio = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="-1" parentID="-1" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItem.audioBroadcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

#uri = "x-sonos-http:amz%3atr%3a6b5d9c09-7dbe-44bc-89e1-85ac5ed45093.mp3?sid=26&flags=8224&sn=1",
#id_ = "amz%3atr%3a6b5d9c09-7dbe-44bc-89e1-85ac5ed45093
didl_amazon = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="00030020{id_}" parentID="" restricted="true"><dc:title></dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON6663_X_#Svc6663-0-Token</desc></item></DIDL-Lite>'''

#main format in use
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

with open('artists') as f:
    zz = f.read()

ARTISTS = json.loads(zz)

def get_sonos_players():
    # master is assigned in sonos_cli2.py
    n = 0
    sp = None
    while n < 10:
        n+=1
        print("attempt "+str(n)) 
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
        print("my_add_to_queue exception:", e)
        return 0
    else:
        qnumber = response['FirstTrackNumberEnqueued']
        return int(qnumber)

# the 'action' functions
def what_is_playing():
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
            response = "I encountered an error trying to get current track info."
        else:
            title = track.get('title', '')
            artist = track.get('artist', '')
            album = track.get('album', '')
            response = f"The track is {title}, the artist is {artist} and the album is {album}."
    else:
        response = "Nothing appears to be playing right now, Steve"

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

        playlist = False
        if 'library_playlist' in uri:
            i = uri.find(':')
            id_ = uri[i+1:]
            meta = didl_library_playlist.format(id_=id_)
            playlist = True
        elif 'library' in uri and not 'static' in uri:
            # this is a bought track
            i = uri.find('library')
            ii = uri.find('.')
            id_ = uri[i:ii]
            meta = didl_library.format(id_=id_)
        elif 'static:library' in uri: # and 'static' in uri:
            # this is a track moved from prime into my account but not paid for
            # baffling but this sometimes generates correct meta data and sometimes doesn't
            i = uri.find('library')
            ii = uri.find('?')
            id_ = uri[i:ii]
            meta = didl_library.format(id_=id_)
        elif 'static:catalog' in uri: # and 'catalog' in uri:
            # this is a track sitting in prime -- queues it up but right now
            #I can't generate metadata
            master.add_uri_to_queue(uri)
            continue
        else:
            print(f'The uri:{uri} was not recognized')
            continue

        #print('meta: ',meta)
        #print('---------------------------------------------------------------')

        # could not uri be why static:library (Amazon Prime not bought) doesn't work???
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
            print("master.play_from_queue exception:", e)

def play_station(station):
    station = STATIONS.get(station.lower())
    if station:
        uri = station[1]
        #print("radio station uri=",uri)
        if uri.startswith('x-sonosapi-radio'):
            meta = meta_format_pandora.format(title=station[0])
        elif uri.startswith('x-sonosapi-stream'):
            meta = meta_format_radio.format(title=station[0])

        master.play_uri(uri, meta, station[0]) # station[0] is the title of the station

def list_queue():
    queue = master.get_queue()
    response = [f"{t.title} from {t.album} by {t.creator}" for t in queue]
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

    print(f"Total track count for {artist} was {count}")
    tracks = result.docs
    k = 10 if count >= 10 else count
    selected_tracks = random.sample(tracks, k)
    uris = [t.get('uri') for t in selected_tracks]
    play(False, uris)
    titles = [t.get('title', '')+'-'+t.get('album', '') for t in selected_tracks]
    title_list = "\n".join([f"{t[0]}. {t[1]}" for t in enumerate(titles, start=1)])
    return f"I will shuffle:\n{title_list}."


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
