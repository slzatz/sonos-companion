#!bin/python
'''
python3 script that imports sonos_actions.py and is the all-in-one sonos cli
script.
Config file inludes the aws solr uri and the local raspberry pi uri
Uses cmd2 (but not sure I'm using any cmd2 capabilities
modified cmd2 because the following line means entering 0 on a select chooses
the last item:  result = fulloptions[response - 1][0]
'''

import random
from operator import itemgetter 
import pysolr
from cmd2 import Cmd
import sonos_actions
from config import solr_uri 

solr = pysolr.Solr(solr_uri+'/solr/sonos_companion/', timeout=10) 

def play_track(title, artist, add): #note the decorator will set add to None
    # title must be present; artist is optional

    if not title:
        return "You didn't provide a track title."

    s = 'title:' + ' AND title:'.join(title.split())
    if artist:
        s = s + ' artist:' + ' AND artist:'.join(artist.split())

    result = solr.search(s, rows=1) 
    if not len(result):
        return f"I couldn't find the track {title} by {artist}."

    track = result.docs[0]
    uri = track['uri']
    sonos_actions.play(add, [uri])
    action = 'add' if add else 'play'
    return f"I will {action} {track.get('title', '')} by " \
            f"{track.get('artist', '')} from album {track.get('album', '')}"

def play_album(album, artist, add=False):
    # album must be present; artist is optional

    if not album:
        return "You didn't provide an album title."

    s = 'album:' + ' AND album:'.join(album.split())
    if artist:
        s = s + ' artist:' + ' AND artist:'.join(artist.split())

    #only brings back actual matches but 25 seems like max for most albums
    result = solr.search(s, fl='score,track,uri,artist,title,album',
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
        titles = [t.get('title', '')+'-'+t.get('artist', '') for t in selected_tracks]
        title_list = "\n".join([f"{t[0]}. {t[1]}" for t in enumerate(titles, start=1)])
        return f"I will play {len(uris)} tracks from {selected_album}:\n{title_list}."
    else:
        return f"I couldn't find any tracks from album {album}."

def shuffle(artist):
    if not artist:
        return "I couldn't find the artist you were looking for.  Sorry."

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
    sonos_actions.play(False, uris)
    titles = [t.get('title', '')+'-'+t.get('album', '') for t in selected_tracks]
    title_list = "\n".join([f"{t[0]}. {t[1]}" for t in enumerate(titles, start=1)])
    return f"I will shuffle:\n{title_list}."

def mix(artist1, artist2):
    all_tracks = [] 
    for artist in (artist1, artist2):
        if artist:
            s = 'artist:' + ' AND artist:'.join(artist.split())
            result = solr.search(s, fl='artist,title,uri', rows=500) 
            count = len(result)
            if count:
                print(f"Total track count for {artist} was {count}")
                tracks = result.docs
                k = 5 if count >= 5 else count
                random_tracks = random.sample(tracks, k)
                all_tracks.append(random_tracks)
            else:
                return f"I couldn't find any tracks for {artist}"
        else:
            return "I couldn't find one or both of the artists you were looking for."

    x = all_tracks[0]
    y = all_tracks[1]
    selected_tracks = [t for sublist in zip(x,y) for t in sublist]
    uris = [t.get('uri') for t in selected_tracks]
    sonos_actions.play(False, uris)
    
    titles = [t.get('title', '')+'-'+t.get('artist', '') for t in selected_tracks]
    title_list = "\n".join([f"{t[0]}. {t[1]}" for t in enumerate(titles, start=1)])
    return f"The mix for {artist1} and {artist2}:\n{title_list}."

def turn_volume(volume):
    if volume in ('increase','louder','higher','up'):
        sonos_actions.turn_volume('louder')
        return "I will turn the volume up."
    elif volume in ('decrease', 'down','quieter','lower'):
        sonos_actions.turn_volume('quieter')
        return "I will turn the volume down."
    else:
        return "I don't know what you asked me to do to the volume."

def set_volume(level):
    if level > 0 and level < 70: 
        sonos_actions.set_volume(level)
        return f"I will set the volume to {level}."
    else:
        return f"{level} is not less than 70"

def play_station(station):
    if station.lower()=='deborah':
        s = 'album:(c)'
        result = solr.search(s, fl='uri,title,artist', rows=600) 
        count = len(result)
        print(f"Total track count for Deborah tracks was {count}")
        tracks = result.docs
        selected_tracks = random.sample(tracks, 20) # randomly decided to pick 20 songs
        uris = [t.get('uri') for t in selected_tracks]
        sonos_actions.play(False, uris)
        titles = [t.get('title', '')+'-'+t.get('artist', '') for t in selected_tracks]
        title_list = "\n".join([f"{t[0]}. {t[1]}" for t in enumerate(titles, start=1)])
        return f"I will play these songs that Deborah chose:\n{title_list}."

    else:
        sonos_actions.play_station(station)

    return f"I will try to play station {station}."
        
class Sonos(Cmd):

    # Setting this true makes it run a shell command if a cmd2/cmd command doesn't exist
    # default_to_shell = True

    def __init__(self):
        self.raw = "Nothing"
        #self.shortcuts.update({'#': 'play', '@':'add'}) # I think alias better
        self.intro = "Welcome to sonos_cli"
        self.prompt = "sonos[]> "
        self.quit = False
        self.msg = ''

        super().__init__(use_ipython=False, startup_script='sonos_cli2_startup')

    def preparse(self, s):
        # this is only so when you do a track with no cmd it works
        self.raw = s
        self.msg = ''
        return s

    def do_master(self, s):
        '''Select the master speaker that will be controlled; no arguments'''
        sp = sonos_actions.get_sonos_players()
        sp_names = {s.player_name.lower():s for s in sp}

        if s:
            master = sonos_actions.master = sp_names.get(s.lower())
            if master is None:
                self.msg = "Whatever you typed is not a speaker name"
                return
            new_master_name = s
        else:
            lst = [f"{s.player_name}-coord'or: {s.group.coordinator.player_name}"\
               for s in sp]
            z = list(zip(sp_names, lst))
            new_master_name = self.select(z, "Which speaker do you want to become the master speaker? ")
            master = sonos_actions.master = sp_names.get(new_master_name)

        members = "+".join([s.player_name for s in sonos_actions.master.group if s!=master])
        self.prompt = f"sonos[{new_master_name}{'+'+members if members else ''}]> "
        self.msg = f"New master is {new_master_name}"

    def do_play(self, s):
        '''
        With a phrase like 'Harvest by Neil Young' will find best match
        and replace the queue with the selected track

        With no phrase, will resume playing
        '''
        if s == '':
            sonos_actions.playback('play')
            self.msg = "I will resume what was playing."
            return
        if 'by' in s:
            title, artist = s.split(' by ')
        else:
            title, artist = s, ''

        # play adds to queue and doesn't erase it
        self.msg = play_track(title, artist, True)
        lst = sonos_actions.list_queue()
        sonos_actions.play_from_queue(len(lst)-1)
        self.msg.replace('add', 'play', 1)
        self.msg = self.msg+f", which is {len(lst)} in the queue"

    def do_add(self, s):
        '''
        With a phrase like 'Harvest by Neil Young' will find best match
        and add the selected track to the queue
        '''
        if 'by' in s:
            title, artist = s.split(' by ')
        else:
            title, artist = s ,''
        self.msg = play_track(title, artist, True)

    def do_album(self, s):
        '''
        With a phrase like 'Harvest by Neil Young' will find best match
        and replace the queue with the tracks of the selected album
        '''
        if 'by' in s:
            album, artist = s.split(' by ')
        else:
            album, artist = s, ''
        self.msg = play_album(album, artist)

    def do_shuffle(self, s):
        '''
        Selects random tracks from artist
        '''

        if s:
            self.msg = sonos_actions.shuffle(s)
        else:
            artists = sonos_actions.ARTISTS
            artist = self.select(artists, "Which artist? ")
            if artist:
                sonos_actions.shuffle(artist)
                self.msg = self.colorize(f"I'll play {artist} now", 'green')
            else:
                self.msg = self.colorize("OK, I won't play anything.", 'red')

    def do_mix(self, s):
        '''
        Mix artist_a and artist_b
        '''
        if ' and ' not in s:
            self.msg = self.colorize("The command is: mix artistA and artistB", 'red')
            return

        artist1, artist2 = s.split(' and ')
        self.msg = mix(artist1, artist2)

    def default(self, s):
        if 'by' in self.raw:
            title, artist = self.raw.split(' by ')
        else:
            title, artist = self.raw, ''
        self.msg = play_track(title, artist, True)

    def do_louder(self, s):
        self.msg = turn_volume('louder')

    def do_quieter(self, s):
        self.msg = turn_volume('quieter')

    def do_set(self, s):
        self.msg = set_volume(int(s))

    def do_pause(self, s):
        sonos_actions.playback('pause')
        self.msg = "I will pause what was playing."

    def do_resume(self, s):
        sonos_actions.playback('play')
        self.msg = "I will resume what was playing."

    def do_next(self, s):
        sonos_actions.playback('next')
        self.msg = "I will skip to the next track."

    def do_mute(self, s):
        sonos_actions.mute(True)
        self.msg = "I will mute the sound."

    def do_unmute(self, s):
        sonos_actions.mute(False)
        self.msg = "I will unmute the sound."

    def do_unjoin(self, s):
        '''Unjoin the speakers that are members of the master speaker'''
        sonos_actions.unjoin()
        self.prompt = f"{sonos_actions.master.player_name()}>"
        self.msg = f"Master speaker {sonos_actions.master.player_name} now has no members"

    def do_what(self, s):
        self.msg = sonos_actions.what_is_playing()

    def do_current(self, s):
        self.msg = sonos_actions.current()

    def do_queue(self, s):
        lst = sonos_actions.list_queue()
        if not lst:
            self.msg = "The queue is empty"
            return

        if s:
            try:
                pos = int(s)
            except ValueError:
                self.msg = "That wasn't a number"
                return

            if 0 < pos <= len(lst):
                sonos_actions.play_from_queue(pos-1)
                self.msg = f"I will play track {pos}: {lst[pos-1]}"
            else:
                self.msg = f"{s} is out of the range of the queue"
        else:
            q = list(enumerate(lst, 1))
            track_info = sonos_actions.current()
            if track_info:
                cur_pos = int(track_info['playlist_position'])
                q[cur_pos-1] = (cur_pos,self.colorize(q[cur_pos-1][1], 'green'))

            pos = self.select(q, "Which track? ")

            if pos:
                sonos_actions.play_from_queue(pos-1)
                self.msg = self.colorize(f"I will play track {pos}: {lst[pos-1]}", 'green')
            else:
                self.msg = self.colorize("OK, I won't play anything.", 'red')

    def do_clear(self, s):
        sonos_actions.clear_queue()
        self.msg = "The queue has been cleared."

    def do_recent(self, s):
        self.msg = sonos_actions.recent_tracks()

    def do_quit(self, s):
        self.quit = True

    def do_select(self, s):
        if 'by' in s:
            title, artist = s.split(' by ')
        else:
            title, artist = s ,''
        if not title:
            self.msg = "You didn't provide a track title."
            return

        s = 'title:' + ' AND title:'.join(title.split())
        if artist:
            s = s + ' artist:' + ' AND artist:'.join(artist.split())

        result = solr.search(s, rows=5) 
        if not len(result):
            self.msg = f"I couldn't find any track with title {title} by {artist}."
            return

        tracks = result.docs
        # list of tuples to select is [(uri, title from album),
        # (uri2, title2 from album2) ...]
        uri = self.select([(t.get('uri'), t.get('title', '')+" from "+t.get('album', '')) for t in tracks], "Which track? ")
        sonos_actions.play(True, [uri])
        self.msg = uri

    def do_station(self, s):
        if s:
            self.msg = sonos_actions.play_station(s)
        else:
            stations = sonos_actions.STATIONS
            lst = [(z[0], z[1][0]) for z in stations.items()]
            #lst.append((0, "Do nothing"))
            station = self.select(lst, "Which station? ")
            if station:
                sonos_actions.play_station(station)
                self.msg = self.colorize(f"I'll play {station} now", 'green')
            else:
                self.msg = self.colorize("OK, I won't play anything.", 'red')

    def do_deb(self, s):
        if s:
            album = s+' (c)'
        else:
            # either below should work
            #result = solr.search('album:(c)', **{'fl':'album', 'rows':20, 'group':'true', 'group.field':'album'})
            result = solr.search(**{'q':'album:(c)', 'fl':'album', 'rows':200, 'group':'true', 'group.field':'album'})
            lst = [z['doclist']['docs'][0]['album'] for z in result.grouped['album']['groups']]
            #lst.append((0, "Do nothing"))
            album = self.select(lst, "Which album? ")

        if album:
            self.do_album(album)
        else:
            self.msg = self.colorize("OK, I won't play anything.", 'red')

    def postcmd(self, stop, s):
        if self.quit:
            return True
        # the below prints the appropriate message after each command
        print(self.msg)

if __name__ == '__main__':
    c = Sonos()
    c.cmdloop()

