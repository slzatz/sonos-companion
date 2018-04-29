#!bin/python
'''
python3 script that imports sonos_actions.py and is the backend for sonos_cli.py
The script uses the flask extension flask-ask, which was written specifically for python-
based Alexa apps. In this case, I am not using Alexa but am using Alexa-like syntax
for text-based requests.
sonos_cli.py has a config file that needs the local uri of sonos_cli_server.py
'''

from flask import Flask #, request
from flask_ask import Ask, statement
import itertools
import random
from operator import itemgetter 
import pysolr
import sonos_actions
from config import solr_uri #, user_id #,last_fm_api_key, user_id

app = Flask(__name__)
app.config['ASK_VERIFY_REQUESTS'] = False
ask = Ask(app, '/sonos')

solr = pysolr.Solr(solr_uri+'/solr/sonos_companion/', timeout=10) #port 8983 is incorporated in the ngrok url

@ask.intent('PlayAlbum', mapping={'album':'myalbum', 'artist':'myartist'})
def play_album(album, artist):
    # album must be present; artist is optional

    print("album =",album)
    print("artist=",artist)

    if album:
        s = 'album:' + ' AND album:'.join(album.split())
        if artist:
            s = s + ' artist:' + ' AND artist:'.join(artist.split())

        result = solr.search(s, fl='score,track,uri,album,title', sort='score desc', rows=25) #**{'rows':25}) #only brings back actual matches but 25 seems like max for most albums
        tracks = result.docs
        if  tracks:
            selected_album = tracks[0]['album']
            try:
                tracks = sorted([t for t in tracks],key=itemgetter('track'))
            except KeyError:
                pass
            # The if t['album']==selected_album only comes into play if we retrieved more than one album
            selected_tracks = [t for t in tracks if t['album']==selected_album]
            uris = [t.get('uri') for t in selected_tracks]
            msg = sonos_actions.play(False, uris)
            print("PlayAlbum return msg from zmq:", msg)
            titles = ', '.join([t.get('title', '') for t in selected_tracks])
            output_speech = f"I will play {len(uris)} tracks from {selected_album}: {titles}"
        else:
            output_speech = "I couldn't find any songs from album {}.".format(album)

    else:
        output_speech = "I couldn't even find the album."

    return statement(output_speech)

@ask.intent('Shuffle', mapping={'artist':'myartist'})
def shuffle(artist):
    if not artist:
        return statement("I couldn't find the artist you were looking for.  Sorry.")

    s = 'artist:' + ' AND artist:'.join(artist.split())
    result = solr.search(s, fl='artist,title,uri', rows=500) 
    count = len(result)
    if not count:
        return statement("I couldn't find any tracks for {}".format(artist))

    print("Total track count for {} was {}".format(artist, count))
    tracks = result.docs
    k = 10 if count >= 10 else count
    selected_tracks = random.sample(tracks, k)
    uris = [t.get('uri') for t in selected_tracks]
    msg = sonos_actions.play(False, uris)
    print("Shuffle return msg from zmq:", msg)
    titles = ', '.join([t.get('title') for t in selected_tracks])
    return statement(f"I will shuffle {titles}.")

@ask.intent('Mix', mapping={'artist1':'myartista', 'artist2':'myartistb'})
def mix(artist1, artist2):
    print("artist1, artist2 = ",artist1,artist2)
    all_tracks = [] 
    for artist in (artist1, artist2):
        if artist:
            s = 'artist:' + ' AND artist:'.join(artist.split())
            result = solr.search(s, fl='artist,title,uri', rows=500) 
            count = len(result)
            if count:
                print("Total track count for {} was {}".format(artist, count))
                tracks = result.docs
                k = 5 if count >= 5 else count
                selected_tracks = random.sample(tracks, k)
                all_tracks.append(selected_tracks)
            else:
                output_speech = "I couldn't find any tracks for {}".format(artist)
                return statement(output_speech)
        else:
            output_speech = "I couldn't find one or both of the artists you were looking for."
            return statement(output_speech)

    x = all_tracks[0]
    y = all_tracks[1]
    mix = [t for sublist in zip(x,y) for t in sublist]
    uris = [t.get('uri') for t in mix]
    msg = sonos_actions.play(False, uris)
    print("Mix return msg from zmq:", msg)
    titles_artists = ', '.join([t.get('title')+' - '+t.get('artist') for t in mix])
    return statement(f"I will shuffle {titles_artists}.")

#note the decorator will set add to None when accessed via URL but not when called directly by add_track
@ask.intent('PlayTrack', mapping={'title':'mytitle', 'artist':'myartist'})
def play_track(title, artist, add): #note the decorator will set add to None
    # title must be present; artist is optional
    print("artist =",artist)
    print("title =",title)
    print("add =", add)

    if not title:
        return statement("I couldn't find the track.")

    s = 'title:' + ' AND title:'.join(title.split())
    if artist:
        s = s + ' artist:' + ' AND artist:'.join(artist.split())

    result = solr.search(s, rows=1) #**{'rows':1})
    if not len(result):
        return statement("I couldn't find the track {} by {}.".format(title,artist))

    track = result.docs[0]
    uri = track['uri']
    msg = sonos_actions.play(False, [uri])
    print("PlayTrack return msg from zmq:", msg)
    action = 'add' if add else 'play'
    return statement(f"I will {action} {track.get('title', '')} by {track.get('artist', '')} from album {track.get('album', '')}")

@ask.intent('AddTrack', mapping={'title':'mytitle', 'artist':'myartist'})
def add_track(title, artist):
    r = play_track(title, artist, True)
    return r

@ask.intent('AMAZON.ResumeIntent')
def resume():
    msg = sonos_actions.playback('play')
    print("Resume return msg from zmq:", msg)
    return statement("I will resume what was playing.")

@ask.intent('AMAZON.PauseIntent')
def pause():
    msg = sonos_actions.playback('pause')
    print("Pause return msg from zmq:", msg)
    return statement("I will pause what was playing.")

@ask.intent('AMAZON.NextIntent')
def next_():
    msg = sonos_actions.playback('pause')
    print("Next return msg from zmq:", msg)
    return statement("I will skip to the next track.")

@ask.intent('Mute')
def mute():
    msg = sonos_actions.mute(True)
    print("Mute return msg from zmq:", msg)
    return statement("I will mute the sound.")

@ask.intent('UnMute')
def unmute(bool_):
    msg = sonos_actions.mute(False)
    print("UnMute return msg from zmq:", msg)
    return statement("I will unmute the sound.")

@ask.intent('TurnVolume')
def turn_volume(volume):
    if volume in ('increase','louder','higher','up'):
        msg = sonos_actions.turn_volume('louder')
        print("Volume return msg from zmq:", msg)
        return statement("I will turn the volume up.")
    elif volume in ('decrease', 'down','quieter','lower'):
        msg = sonos_actions.turn_volume('quieter')
        print("Volume return msg from zmq:", msg)
        return statement("I will turn the volume down.")
    else:
        return statement("I don't know what you asked me to do to the volume.")

@ask.intent('SetVolume', convert={'level':int})
def set_volume(level):
    if level > 0 and level < 70: 
        msg = sonos_actions.set_volume(level)
        print("SetVolume return msg from zmq:", msg)
        return statement("I will set the volume to {}.".format(level))
    else:
        return statement("{} is not in the range zero to seventy".format(level))

@ask.intent('WhatIsPlaying')
def what_is_playing():
    msg = sonos_actions.what_is_playing()
    print("WhatIsPlaying return msg from zmq:", msg)
    return statement(msg)

@ask.intent('RecentTracks')
def recent_tracks():
    msg = sonos_actions.recent_tracks()
    print("RecentTracks return msg from zmq:", msg)
    return statement(msg)

@ask.intent('PlayStation', mapping={'station':'mystation'})
def play_station(station):
    if station.lower()=='deborah':
        s = 'album:(c)'
        result = solr.search(s, fl='uri', rows=600) 
        count = len(result)
        print("Total track count for Deborah tracks was {}".format(count))
        tracks = result.docs
        selected_tracks = random.sample(tracks, 20) # randomly decided to pick 20 songs
        uris = [t.get('uri') for t in selected_tracks]
        msg = sonos_actions.play(False, uris)
    else:
        msg = sonos_actions.play_station(station)

    print("PlayStation({}) return msg from zmq:".format(station), msg)
    return statement("I will try to play station {}.".format(station))
        
@ask.intent('ListQueue')
def list_queue():
    msg = sonos_actions.list_queue()
    print("ListQueue return msg from zmq:", msg)
    return statement(msg)

@ask.intent('ClearQueue')
def clear_queue():
    msg = sonos_actions.clear_queue()
    print("ClearQueue return msg from zmq:", msg)
    return statement(msg)

try:
    app.run(debug=True,
            port=5000,
            threaded=False,
            use_reloader=False,
            use_debugger=True,
            host='0.0.0.0'
            )
finally:
    print("Disconnecting clients")

print("Done")

