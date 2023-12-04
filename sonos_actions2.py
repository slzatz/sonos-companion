'''
Script that is imported by sonos.py that deals with SoCo

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

If track is from Amazon Music (not purchased separately) the uri is:
x-sonosapi-hls-static:catalog%2ftracks%2fB01E0N3W66%2f%3falbumAsin%3dB01E0N386A?sid=201&flags=0&sn=1
x-sonosapi-hls-static:catalog/tracks/B01E0N3W66/?albumAsin?B01E0N386A?sid=201&flags=0&sn=1

x-sonosapi-hls-static:catalog%2ftracks%2fB086RGP393%2f?sid=201&flags=0&sn=1
x-sonosapi-hls-static:catalog/tracks/B086RGP393/?sid=201&flags=0&sn=1

x-sonos-spotify:spotify%3atrack%3a7ykaUgkdQWJLsMuOymTV2A?sid=12&flags=8224&sn=3
x-sonos-spotify:spotify:track:7ykaUgkdQWJLsMuOymTV2A?sid=12&flags=8224&sn=3

If track is Prime but moved to my music (but not purchased) then url is (not sure this applies anymore):
x-sonosapi-hls-static:library%2fartists%2fThe_20Avett_20Brothers%2fI_20And_20Love_20And_20You%2ff9aa6eac-6707-44bc-99ff-3aa2e5938d12%2f?sid=201&flags=0&sn=1' 
x-sonosapi-hls-static:library/artists/The_20Avett_20Brothers/I_20And_20Love_20And_20You/f9aa6eac-6707-44bc-99ff-3aa2e5938d12%2f.mp3?sid=201&flags=0&sn=1' 

If track has been purchased from Amazon:
x-sonos-http:library%2fartists%2fThe_20Avett_20Brothers%2fI_20And_20Love_20And_20You%2ff9aa6eac-6707-44bc-99ff-3aa2e5938d12%2f.mp3?sid=201&flags=0&sn=1' 
x-sonos-http:library/artists/The_20Avett_20Brothers/I_20And_20Love_20And_20You/f9aa6eac-6707-44bc-99ff-3aa2e5938d12%2f.mp3?sid=201&flags=0&sn=1' 

if track was put on queue as part of a playlist
x-sonos-http:library%2fplaylist%2f28f452a4-3414-456d-9146-9e9063868963%2f067b7994-615b-4f12-850b-4f12-850b-...mp3?sid...
x-sonos-http:library/playlist/28f452a4-3414-456d-9146-9e9063868963%2f067b7994-615b-4f12-850b-4f12-850b-...mp3?sid...

actions = {'play':play, 'turn_volume':turn_volume, 'set_volume':set_volume, 'playback':playback, 'what_is_playing':what_is_playing, 'recent_tracks':recent_tracks, 'play_station':play_station, 'list_queue': list_queue, 'clear_queue':clear_queue, 'mute':mute} 

'''

import os
from ipaddress import ip_address
from time import sleep
import json
import sys
import random
from operator import itemgetter 
import pysolr

import soco
from soco.discovery import by_name
from soco.music_services import MusicService
#from soco import config as soco_config
#from config import solr_uri
from config import music_service
from sonos_config import STATIONS, META_FORMAT_PANDORA, META_FORMAT_RADIO, \
                         DIDL_LIBRARY_PLAYLIST, DIDL_AMAZON, DIDL_SERVICE

import re
from unidecode import unidecode
#soco_config.CACHE_ENABLED = False

#solr = pysolr.Solr(solr_uri+'/solr/sonos_companion/', timeout=10) 
ms = MusicService(music_service)
 
def extract(uri):
    #print(f"{uri=}")
    # I am storing Spotify uris with colons not %3a
    match = re.search(r"spotify.*[:/](album|track|playlist)[:/](\w+)", uri)
    spotify_uri = "spotify:" + match.group(1) + ":" + match.group(2)
    #print(f"{spotify_uri=}")
    share_type = spotify_uri.split(":")[1]
    encoded_uri = spotify_uri.replace(":", "%3a")
    return (share_type, encoded_uri)


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

def set_master(speaker):
#    try:
#        ip_address(speaker)
#    except ValueError:
#        pass
#    else:
#        return soco.SoCo(speaker)
#
#    sps = get_sonos_players()
#    if not sps:
#        return None
#
#    sp_names = {s.player_name:s for s in sps}
#    return sp_names.get(speaker)

     return by_name(speaker)
    
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
            # this is a bought track and question also one that was uploaded one?
            i = uri.find('library')
            ii = uri.find('.')
            encoded_uri = uri[i:ii]
            meta = DIDL_AMAZON.format(id_=encoded_uri) #? if need parentID="" which isn't in DIDL_SERVICE
            #meta = DIDL_SERVICE.format(item_id="10030000"+encoded_uri, #interesting that id worked; from sharelink.py
            #        item_class = "object.item.audioItem.musicTrack",
            #        sn="51463")
            my_add_to_queue(encoded_uri, meta)
        elif 'static:library' in uri: # and 'static' in uri:
            # track moved from Prime into my account but not paid for - there is no reason to do this
            i = uri.find('library')
            ii = uri.find('?')
            encoded_uri = uri[i:ii]
            meta = DIDL_SERVICE.format(item_id="00032020"+encoded_uri, #that number is the sharelink "track" "key"
                    item_class = "object.item.audioItem.musicTrack",
                    sn="51463")
            my_add_to_queue(encoded_uri, meta)
        elif 'static:catalog' in uri: 
            # an Amazon music track
            i = uri.find('catalog')
            ii = uri.find('?')
            encoded_uri = uri[i:ii]
            meta = DIDL_SERVICE.format(item_id="00032020"+encoded_uri, #that number is the sharelink "track" "key"
                    item_class = "object.item.audioItem.musicTrack",
                    sn="51463")
            my_add_to_queue(encoded_uri, meta)
        elif 'spotify' in uri:
            (share_type, encoded_uri) = extract(uri)
            meta = DIDL_SERVICE.format(item_id="00032020"+encoded_uri, #interesting that id worked; from sharelink.py
                    item_class = "object.item.audioItem.musicTrack",
                    sn="3079") #2311 is Spotify Europe
            my_add_to_queue(encoded_uri, meta)

        else:
            print(f'The uri:{uri} was not recognized')
            continue

        #print(f"{encoded_uri=}\n") 

    # need this because may have selected multiple tracks and want to start from the top (like shuffle)
    if not add:
        play_from_queue(0) 
    else:
        queue = master.get_queue()
        play_from_queue(len(queue) - 1)

def play_station(station):
    station = STATIONS.get(station.lower())
    if station:
        uri = station[1]
        if uri.startswith('x-sonosapi-radio'):
            meta = META_FORMAT_PANDORA.format(title=station[0])
        elif uri.startswith('x-sonosapi-stream'):
            meta = META_FORMAT_RADIO.format(title=station[0])

        master.play_uri(uri, meta, station[0]) # station[0] is the title of the station

def list_queue():
    queue = master.get_queue()
    response = []
    for t in queue:
        if type(t) == soco.data_structures.DidlMusicTrack:
            response.append(f"{t.title}")
        else:
            response.append(f"{t.metadata['title']} (MSTrack)")
    return response

def clear_queue():
    try:
        master.clear_queue()
    except Exception as e:
        print("Encountered exception when trying to clear the queue:",e)
 
def shuffle(artists):
    master.stop() # not necessary but let's you know a new cmd is underway
    master.clear_queue()
    tracks = []
    results = ms.search("tracks", artists)
    random.shuffle(results)
    # get something playing right away
    master.add_to_queue(results[0])
    master.play_from_queue(0)
    tracks.append(results[0].title)
    for track in list(results)[1:]:
        # remove dups - not sure how common
        if track.title in tracks:
            continue
        track_metadata = track.metadata.get('track_metadata', None)
        #print(f"{track_metadata.metadata.get('artist')=}: {arg=}")
        if not track_metadata:
            continue
        # Occasionally the artist is in some field search looks at but it's not the artist for the song
        # may not be worth checking
        #if unidecode(track_metadata.metadata.get('artist').lower()) in artists.lower(): #added 07092023 
        #if artists.lower() in unidecode(track_metadata.metadata.get('artist').lower()): #added 07092023 
        track_artist = track_metadata.metadata.get('artist').lower()
        if not track_artist.isascii():
            track_artist = unidecode(track_artist)

        if any(word in track_artist for word in artists.lower().split()): #added 07092023 
        #if unidecode(track_metadata.metadata.get('artist').lower()) == artists.lower(): #added 07092023 
            try:
                master.add_to_queue(track)
            except Exception as e:
                print("Encountered exception when trying to clear the queue:",e)
            else:
                tracks.append(track.title)
    #master.play_from_queue(0)
    #return "\n".join(tracks)
    #if len(tracks) < 3:
    #    for track in list(results)[1:]:
    #        # remove dups - not sure how common
    #        if track.title in tracks:
    #            continue
    #        track_metadata = track.metadata.get('track_metadata', None)
    #        #print(f"{track_metadata.metadata.get('artist')=}: {arg=}")
    #        if not track_metadata:
    #            continue
    #        # Occasionally the artist is in some field search looks at but it's not the artist for the song
    #        # may not be worth checking
    #        try:
    #            master.add_to_queue(track)
    #        except Exception as e:
    #            print("Encountered exception when trying to clear the queue:",e)
    #        else:
    #            tracks.append(track.title)
    msg = ""
    for n, t in enumerate(tracks):
        msg += f"{n}. {t}\n"
    return msg

def old_shuffle(artists):
    tracklist = []
    msg = ""
    for artist in artists:
        s = 'artist:' + ' AND artist:'.join(artist.split())
        result = solr.search(s, fl='artist,title,uri', rows=500) 
        count = len(result)
        num_tracks = int(10/len(artists))
        if count:
            msg += f"Total track count for {artist} was {count}\n"
            tracks = result.docs
            k = num_tracks if count >= num_tracks else count
            random_tracks = random.sample(tracks, k)
            tracklist.extend(random_tracks)
        else:
            msg += f"I couldn't find any tracks for {artist.title()}\n"
            return msg

    random.shuffle(tracklist)
    uris = [t.get('uri') for t in tracklist]
    play(False, uris)

    titles = [t.get('title', '')+'-'+t.get('artist', '') for t in tracklist]
    title_list = "\n".join([f"{t[0]}. {t[1]}" for t in enumerate(titles, start=1)])
    msg += f"The mix for {' and '.join(artists)}:\n{title_list}"

    return msg
    
def list_(artist):
    s = 'artist:' + ' AND artist:'.join(artist.split())
    result = solr.search(s, fl='artist,title,uri', rows=500) 
    return result
    #count = len(result)
    #msg = ""
    #if count:
    #    msg += f"Track count for {artist.title()} was {count}:\n"
    #    tracks = result.docs
    #else:
    #    msg += f"I couldn't find any tracks for {artist.title()}\n"
    #    return msg

    #title_list = "\n".join([f"{t[0]}. {t[1]}" for t in enumerate(titles, start=1)])
    ##msg += f"The list for {artist}:\n{title_list}"
    #msg += title_list

    #return msg

def play_pause():
    try:
        state = master.get_current_transport_info()['current_transport_state']
    except Exception as e:
        print("Encountered error in state = master.get_current_transport_info(): ", e)
        state = 'ERROR'

    # check if sonos is playing music
    if state == 'PLAYING':
       # master.pause()
        playback('pause')
    else:
        playback('play')
    #elif state!='ERROR':
    #    master.play()

def play_track_old(title, artist=None):
    s = 'title:' + ' AND title:'.join(title.split())
    if artist:
        s = s + ' artist:' + ' AND artist:'.join(artist.split())

    result = solr.search(s, rows=1)

    if result:
        track = result.docs[0]
        uri = track['uri']
        play(True, [uri]) # add
        msg = f"{track.get('title', '')} by {track.get('artist', '')} " \
            f"from album {track.get('album', '')}"
    else:
        msg = f"Couldn't find track {title}{' by'+artist if artist else ''}"

    return msg

def play_track(track):
    results = ms.search("tracks", track)
    master.add_to_queue(results[0])
    queue = master.get_queue()
    master.play_from_queue(len(queue) - 1)
    return results[0].title

def play_album(album):
    master.stop() # not necessary but let's you know a new cmd is underway
    master.clear_queue()
    results = ms.search("albums", album)
    master.add_to_queue(results[0])
    master.play_from_queue(0)
    return list_queue()

def play_album_old(album, artist=None):
    s = 'album:' + ' AND album:'.join(album.split())
    if artist:
        s = s + ' artist:' + ' AND artist:'.join(artist.split())

    #only brings back actual matches but 25 seems like max for most albums
    result = solr.search(s, fl='score,track,uri,artist,title,album',
                         sort='score desc', rows=25) 

    tracks = result.docs
    if tracks:
        selected_album = tracks[0]['album']
        try:
            tracks = sorted([t for t in tracks],key=itemgetter('track'))
        except KeyError:
            pass
        # The if t['album']==selected_album only comes into play
        # if we retrieved more than one album
        selected_tracks = [t for t in tracks if t['album']==selected_album]
        uris = [t.get('uri') for t in selected_tracks]
        play(False, uris)
        titles = [t.get('title', '')+'-'+t.get('artist', '') for t in selected_tracks]
        title_list = "\n".join([f"{t[0]}. {t[1]}" for t in enumerate(titles, start=1)])
        msg = f"{len(uris)} tracks from {selected_album}:\n{title_list}"
    else:
        msg = f"I couldn't find {album}{ 'by {artist}' if artist else ''}"
        
    return msg
