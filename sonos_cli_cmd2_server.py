#!bin/python
'''
python3 script that imports sonos_actions.py and is the all-in-one sonos cli
script.
Config file inluces the aws solr uri and the local raspberry pi uri
Uses cmd2 (but not sure I'm using any cmd2 capabilities
'''

import random
from operator import itemgetter 
import pysolr
from cmd2 import Cmd
import sonos_actions
from config import solr_uri, local_urls #, user_id #,last_fm_api_key, user_id

#port 8983 is incorporated in the solr_uri
solr = pysolr.Solr(solr_uri+'/solr/sonos_companion/', timeout=10) 

def play_track(title, artist, add): #note the decorator will set add to None
    # title must be present; artist is optional
    print("artist =",artist)
    print("title =",title)
    print("add =", add)

    if not title:
        return "You didn't provide a track title."

    s = 'title:' + ' AND title:'.join(title.split())
    if artist:
        s = s + ' artist:' + ' AND artist:'.join(artist.split())

    result = solr.search(s, rows=1) #**{'rows':1})
    if not len(result):
        return "I couldn't find the track {} by {}.".format(title,artist)

    track = result.docs[0]
    uri = track['uri']
    sonos_actions.play(add, [uri])
    action = 'add' if add else 'play'
    return f"I will {action} {track.get('title', '')} by " \
            "{track.get('artist', '')} from album {track.get('album', '')}"

def play_album(album, artist, add=False):
    # album must be present; artist is optional

    print("album =",album)
    print("artist=",artist)
    print("add =", add)

    if not album:
        return "You didn't provide an album title."

    s = 'album:' + ' AND album:'.join(album.split())
    if artist:
        s = s + ' artist:' + ' AND artist:'.join(artist.split())

    #only brings back actual matches but 25 seems like max for most albums
    result = solr.search(s, fl='score,track,uri,album,title',
                         sort='score desc', rows=25) 

    tracks = result.docs
    if  tracks:
        selected_album = tracks[0]['album']
        try:
            tracks = sorted([t for t in tracks],key=itemgetter('track'))
        except KeyError:
            pass
        # The if t['album']==selected_album only comes into play
        # if we retrieved more than one album
        selected_tracks = [t for t in tracks if t['album']==selected_album]
        uris = [t.get('uri') for t in selected_tracks]
        sonos_actions.play(False, uris)
        titles = ', '.join([t.get('title', '') for t in selected_tracks])
        return f"I will play {len(uris)} tracks from {selected_album}: {titles}"
    else:
        return f"I couldn't find any tracks from album {album}."

def shuffle(artist):
    if not artist:
        return "I couldn't find the artist you were looking for.  Sorry."

    s = 'artist:' + ' AND artist:'.join(artist.split())
    result = solr.search(s, fl='artist,title,uri', rows=500) 
    count = len(result)
    if not count:
        return "I couldn't find any tracks for {}".format(artist)

    print("Total track count for {} was {}".format(artist, count))
    tracks = result.docs
    k = 10 if count >= 10 else count
    selected_tracks = random.sample(tracks, k)
    uris = [t.get('uri') for t in selected_tracks]
    sonos_actions.play(False, uris)
    titles = ', '.join([t.get('title') for t in selected_tracks])
    return f"I will shuffle {titles}."

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
                return f"I couldn't find any tracks for {artist}"
        else:
            return "I couldn't find one or both of the artists you were looking for."

    x = all_tracks[0]
    y = all_tracks[1]
    mix = [t for sublist in zip(x,y) for t in sublist]
    uris = [t.get('uri') for t in mix]
    sonos_actions.play(False, uris)
    titles_artists = ', '.join([t.get('title')+' - '+t.get('artist') for t in mix])
    return f"I will shuffle {titles_artists}."

def turn_volume(volume):
    if volume in ('increase','louder','higher','up'):
        msg = sonos_actions.turn_volume('louder')
        #print("Volume return msg from zmq:", msg)
        return "I will turn the volume up."
    elif volume in ('decrease', 'down','quieter','lower'):
        msg = sonos_actions.turn_volume('quieter')
        #print("Volume return msg from zmq:", msg)
        return "I will turn the volume down."
    else:
        return "I don't know what you asked me to do to the volume."

def set_volume(level):
    if level > 0 and level < 70: 
        msg = sonos_actions.set_volume(level)
        #print("SetVolume return msg from zmq:", msg)
        return "I will set the volume to {level}."
    else:
        return f"{level} is not in the range zero to seventy"

def what_is_playing():
    msg = sonos_actions.what_is_playing()
    print("WhatIsPlaying return msg from zmq:", msg)
    return msg

def recent_tracks():
    msg = sonos_actions.recent_tracks()
    print("RecentTracks return msg from zmq:", msg)
    return msg

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

    #print("PlayStation({}) return msg from zmq:".format(station), msg)
    return "I will try to play station {}.".format(station)
        
def list_queue():
    msg = sonos_actions.list_queue()
    print("ListQueue return msg from zmq:", msg)
    return msg

def clear_queue():
    msg = sonos_actions.clear_queue()
    print("ClearQueue return msg from zmq:", msg)
    return msg

class Sonos(Cmd):

    # Setting this true makes it run a shell command if a cmd2/cmd command doesn't exist
    # default_to_shell = True

    def __init__(self):
        self.raw = "Nothing"
        self.shortcuts.update({'#': 'play', '@':'add'})
        self.intro = "Welcome to sonos_cli"
        self.prompt = "sonos> "
        self.quit = False

        # Set use_ipython to True to enable the "ipy" command which embeds and interactive IPython shell
        super().__init__(use_ipython=False)

    def preparse(self, s):
        # this is only so when you do a track with no cmd it works
        self.raw = s
        return s

    def do_location(self, s):
        if s=='':
            s = input("what is the location? ")
        self.url = local_urls.get(s)
        print(f"The location is {s}")

    def do_play(self, s):
        if 'by' in s:
            title, artist = s.split(' by ')
        else:
            title, artist = s, ''

        self.msg = play_track(title, artist, False)

    def do_add(self, s):
        if 'by' in s:
            title, artist = s.split(' by ')
        else:
            title, artist = s ,''
        self.msg = play_track(title, artist, True)

    def do_album(self, s):
        if 'by' in s:
            album, artist = s.split(' by ')
        else:
            album, artist = s, ''
        self.msg = play_album(album, artist)

    def do_shuffle(self, s):
        self.msg = shuffle(s)

    def do_mix(self, s):
        if ' and ' not in s:
            self.msg = "command is: mix artistA and artistB"
            return

        artist1, artist2 = s.split(' and ')
        self.msg = sonos_actions.mix(artist1, artist2))

    def default(self, s):
        if 'by' in self.raw:
            self.values = self.raw.split(' by ')
        else:
            self.values = [self.raw ,'']
        print("play "+self.raw)

    def do_louder(self, s):
        self.msg = turn_volume('louder')

    def do_quieter(self, s):
        self.msg = turn_volume('quieter')

    def do_pause(self, s):
        sonos_actions.playback('pause')
        self.msg = "I will pause what was playing."

    def do_resume(self, s):
        sonos_actions.playback('play')
        self.msg = "I will resume what was playing."

    def do_next(self, s):
        sonos_actions.playback('pause')
        self.msg = "I will skip to the next track."

    def do_mute(self, s):
        sonos_actions.mute(True)
        self.msg = "I will mute the sound."

    def do_unmute(self, s):
        sonos_actions.mute(False)
        self.msg = "I will unmute the sound."

    def do_what(self, s):
        self.msg = sonos_actions.what_is_playing()

    def do_quit(self, s):
        self.quit = True

    def postcmd(self, stop, s):
        if self.quit:
            return True
        # the below prints the appropriate message after each command
        print(self.msg)

if __name__ == '__main__':
    c = Sonos()
    c.cmdloop()

