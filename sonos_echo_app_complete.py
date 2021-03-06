'''
This single script handles echo and sonos - no mqtt
Also requires echo_flask_sonos :

Also need ngrok http 5000
and url will look like 1234.ngrok.io/sonos
it is set on Alexa configuration page
Requires pysolr.py, config.py, requests - note pysolr.py needs requests
Below are the Alexa intents
PlayStation play {mystation} radio
PlayStation play {mystation} pandora
PlayStation play {mystation} station
PlayTrack play {mytitle} by {myartist}
PlayTrack play {mytitle}
AddTrack add {mytitle} by {myartist}
AddTrack add {mytitle}
AddTrack add {mytitle} to the queue
AddTrack add {mytitle} by {myartist} to the queue
Shuffle shuffle {myartist}
Shuffle play some {myartist}
Shuffle play some music from {myartist}
SetShuffleNumber Set shuffle number to {mynumber}
GetShuffleNumber What is the shuffle number
WhatIsPlaying what is playing
WhatIsPlaying what song is playing
Skip skip
Skip next
Skip skip song
Skip next song
PlayAlbum play album {myalbum}
PlayAlbum play the album {myalbum}
AddAlbum add album {myalbum}
AddAlbum add the album {myalbum}
PauseResume {pauseorresume} the music
PauseResume {pauseorresume} the radio
PauseResume {pauseorresume} sonos
TurnTheVolume Turn the volume {volume}
TurnTheVolume Turn {volume} the volume
SetLocation Set location to {location}
SetLocation I am in {location}
GetLocation Where am I
GetLocation What is the location
'''
import json
from time import sleep
import sys
import os
import random
from operator import itemgetter 
from decimal import Decimal
import time
import pysolr
import requests
from multiprocessing.connection import Client 
from config import solr_uri, last_fm_api_key, user_id #location

home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + sys.path
import soco
from soco import config as soco_config
soco_config.CACHE_ENABLED = False

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
    
for s in sp:
    print "{} -- coordinator:{}".format(s.player_name, s.group.coordinator.player_name) 

master_name = raw_input("Which speaker do you want to be master? ")
master = speakers.get(master_name)
if master:
    print "Master speaker is: {}".format(master.player_name) 
    sp = [s for s in sp if s.group.coordinator is master]
    print "Master group:"
    for s in sp:
        print "{} -- coordinator:{}".format(s.player_name, s.group.coordinator.player_name) 

else:
    print "Somehow you didn't pick a master or spell it correctly (case matters)" 
    sys.exit(1)

print "\nConnected to Sonos\n"

#last.fm 
base_url = "http://ws.audioscrobbler.com/2.0/"

appVersion = '1.0'

solr = pysolr.Solr(solr_uri+'/solr/sonos_companion/', timeout=10) #port 8983 is incorporated in the ngrok url

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

COMMON_ACTIONS = {'pause':'pause', 'resume':'play', 'skip':'next'}

address = ('localhost', 6000)
conn = Client(address, authkey='secret password')

def lambda_handler(event, context=None):
    session = event['session']
    request = event['request']
    requestType = request['type']
	
    if requestType == "LaunchRequest":
        response = launch_request(session, request)
    elif requestType == "IntentRequest":
        response = intent_request(session, request)
    else:
        output_speech = "I couldn't tell which type of request that was.  Try again."
        response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':False}

    print json.dumps(response) 

    return {"version":appVersion,"response":response}

def launch_request(session, request):
    output_speech = "Welcome to Sonos. Some things you can do are: Select Neil Young radio or Shuffle Neil Young or Play After the Gold Rush or ask what is playing or skip, louder, quieter"
    response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':False}
    return response

def intent_request(session, request):

    intent = request['intent']['name']
    print "intent_request: {}".format(intent)

    if intent ==  "PlayStation":

        mystation = request['intent']['slots']['mystation']['value']
        mystation = mystation.lower()
        if mystation == 'deborah':
            # This took too long so using multiprocessing to send to echo_check_mp.py
            conn.send({'action':'deborah'})
            output_speech = "Deborah Radio will start playing soon."
        else:
            station = STATIONS.get(mystation)
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
                output_speech = station[0] + " will start playing soon."
            else:
                output_speech = "{} is not a preset station.".format(mystation)

        response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':True}
        return response

    elif intent ==  "PlayAlbum" or intent == "AddAlbum":
        # album must be present; artist is optional

        album = request['intent']['slots']['myalbum'].get('value', '')
        artist = request['intent']['slots']['myartist'].get('value', '')
        print "album =",album
        print "artist=",artist

        if album:
            s = 'album:' + ' AND album:'.join(album.split())
            if artist:
                s = s + ' artist:' + ' AND artist:'.join(artist.split())

            result = solr.search(s, fl='score,track,uri,album', sort='score desc', rows=25) #**{'rows':25}) #only brings back actual matches but 25 seems like max for most albums
            tracks = result.docs
            if  tracks:
                selected_album = tracks[0]['album']
                try:
                    tracks = sorted([t for t in tracks],key=itemgetter('track'))
                except KeyError:
                    pass
                # The if t['album']==selected_album only comes into play if we retrieved more than one album
                uris = [t['uri'] for t in tracks if t['album']==selected_album]

                if intent == 'PlayAlbum':
                    master.stop()
                    master.clear_queue()

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

                    my_add_to_queue('', meta)

                if intent == 'PlayAlbum':
                    master.play_from_queue(0)

                output_speech = "I will play {} songs from {}".format(len(uris), selected_album)
                end_session = True
            else:
                output_speech = "I couldn't find {}. Try again.".format(album)
                end_session = False

        else:
            output_speech = "I couldn't find the album. Try again."
            end_session = False

        response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':end_session}
        return response

    elif intent in ("PlayTrack", "AddTrack"):
        # title must be present; artist is optional

        title = request['intent']['slots']['mytitle'].get('value', '')
        artist = request['intent']['slots']['myartist'].get('value', '')
        print "artist =",artist
        print "title =",title

        if title:
            s = 'title:' + ' AND title:'.join(title.split())
            if artist:
                s = s + ' artist:' + ' AND artist:'.join(artist.split())

            result = solr.search(s, rows=1) #**{'rows':1})
            if len(result):
                track = result.docs[0]
                uri = track['uri']

                print 'uri: ' + uri
                print "---------------------------------------------------------------"
                if 'library' in uri:
                    i = uri.find('library')
                    ii = uri.find('.')
                    id_ = uri[i:ii]
                    meta = didl_library.format(id_=id_)
                else:
                    print 'The uri:{}, was not recognized'.format(uri)
                    output_speech = "That is not a uri format that I can deal with."
                    response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':True}
                    return response

                print 'meta: ',meta
                print '---------------------------------------------------------------'

                my_add_to_queue('', meta)

                if intent == 'PlayTrack':
                    queue = master.get_queue()
                    master.play_from_queue(len(queue)-1)
                    action = 'play'
                else:
                    action = 'add'

                output_speech = "I will {} {} by {} from album {}".format(action, track['title'], track['artist'], track['album'])
                end_session = True
            else:
                output_speech = "I couldn't find the song {} by {}. Try again.".format(title,artist)
                end_session = False
        else:
            output_speech = "I couldn't find the song. Try again."
            end_session = False

        response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':end_session}
        return response

    elif intent == "Shuffle":

        artist = request['intent']['slots']['myartist'].get('value')
        if artist:
            conn.send({'action':'shuffle', 'artist':artist})
            output_speech = "I will shuffle songs by {}.".format(artist)
            end_session = True
        else:
            output_speech = "I couldn't find the artist you were looking for. Try again."
            end_session = False

        response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':end_session}
        return response

    elif intent == "Mix":

        artist1 = request['intent']['slots']['myartist1'].get('value')
        artist2 = request['intent']['slots']['myartist2'].get('value')

        if artist1 and artist2:
            conn.send({'action':'mix', 'artists':[artist1, artist2]})##########################
            output_speech = "I will try to mix songs by {} and {}.".format(artist1,artist2)
            end_session = True
        else:
            output_speech = "I couldn't find the artists you were looking for. Try again."
            end_session = False

        response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':end_session}
        return response

    elif intent == "ShowQueue":
        queue = master.get_queue()

        if len(queue) == 0:
            output_speech = "There is nothing in the queue"
        else:
            output_speech = ""
            for track in queue:
                output_speech+="{} from {} by {}, ".format(track.title, track.album, track.creator)

        response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':True}
        return response

    elif intent == "ClearQueue":
        try:
            master.clear_queue()
        except Exception as e:
            print "Encountered exception when trying to clear the queue:",e

        response = {'outputSpeech': {'type':'PlainText','text':"I'll try to clear the queue"},'shouldEndSession':True}
        return response

    elif intent == "WhatIsPlaying":
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

        response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':True}
        return response

    elif intent == "RecentTracks":
        # right now look back is one week; note can't limit because you need all the tracks since we're doing the frequency count
        payload = {'method':'user.getRecentTracks', 'user':'slzatz', 'format':'json', 'api_key':last_fm_api_key, 'from':int(time.time())-604800} #, 'limit':10}
        
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
            for album_track,count in a: #[:10]
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

        response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':True}
        return response

    elif intent == "AMAZON.NextIntent":
        try:
            master.next()
        except soco.exceptions.SoCoUPnPException as e:
            print "master.{}:".format('next'), e
        response = {'outputSpeech': {'type':'PlainText','text':'skipped'},'shouldEndSession':True}
        return response

    elif intent == "AMAZON.PreviousIntent":
        try:
            master.previous()
        except soco.exceptions.SoCoUPnPException as e:
            print "master.{}:".format('previous'), e
        response = {'outputSpeech': {'type':'PlainText','text':'previous'},'shouldEndSession':True}
        return response

    elif intent == "AMAZON.PauseIntent":
        try:
            master.pause()
        except soco.exceptions.SoCoUPnPException as e:
            print "master.{}:".format('pause'), e
        response = {'outputSpeech': {'type':'PlainText','text':'I will pause'},'shouldEndSession':True}
        return response

    elif intent == "AMAZON.ResumeIntent":
        try:
            master.play()
        except soco.exceptions.SoCoUPnPException as e:
            print "master.{}:".format('play'), e
        response = {'outputSpeech': {'type':'PlainText','text':'I will resume'},'shouldEndSession':True}
        return response

    elif intent == "TurnTheVolume":

        volume = request['intent']['slots']['volume']['value']

        if volume in ('increase','louder','higher','up'):
            for s in sp:
                s.volume = s.volume + 10
            output_speech = "I will make the volume louder"
        elif volume in ('decrease', 'down','quieter','lower'):
            for s in sp:
                s.volume = s.volume - 10
            output_speech = "I will turn the volume down"
        else:
            output_speech = "I don't know what you wanted me to do with the volume"

        response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':True}
        return response

    else:
        output_speech = "I couldn't tell which type of intent request that was.  Try again."
        response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':False}
        return response
