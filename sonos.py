#!bin/python

'''Click-based command line script to control sonos.
There are a bunch of aliases in .bashrc'''

import random
from operator import itemgetter 
import click
from soco import SoCo
import sonos_actions
from get_lyrics import get_lyrics #uses genius.com
import pysolr
from config import solr_uri

def bold(text):
    return "\033[1m" + text + "\033[0m"

def colorize(text, color):
    if color == "red":
        return "\033[31m" + text + "\033[0m"
    elif color == "green":
        return "\033[32m" + text + "\033[0m"
    elif color == "magenta":
        return "\033[35m" + text + "\033[0m"
    else:
        return text

class Config():
    def __init__(self):
        #self.master = "Office2"
        #self.master = ""
        pass

pass_config = click.make_pass_decorator(Config, ensure=True)

@click.group()
@click.option("-m", "--master", help="The name of the master speaker")
@click.option("-v", "--verbose", is_flag=True, help="Display additional information")
@pass_config
def cli(config, master, verbose):
    '''Sonos command line app; master defaults to "Office2"; verbose defaults to False '''
    config.verbose = verbose
    solr = pysolr.Solr(solr_uri+'/solr/sonos_companion/', timeout=10) 
    config.solr = solr

    if not master:
        sp = SoCo("192.168.86.23")
        if sp._player_name: # in case Office2 ip address changes
            sonos_actions.master = sp
            if verbose:
                click.echo(f"Master speaker is {sp._player_name: sp.ip_address}")
            return
        else:
            master = "Office2"

    #master = master if master else "Office2"

    sps = sonos_actions.get_sonos_players()
    if not sps:
        click.echo("Could not find Sonos speakers")
        return
    sp_names = {s.player_name:s for s in sps}
    sonos_actions.master = sp_names.get(master)

    #sonos_actions.master = SoCo("192.168.86.23")

    if verbose:
        click.echo(f"Master speaker is {master}: {sonos_actions.master.ip_address}")

@cli.command()
@click.argument('station', default="wnyc", required=False)
def playstation(station):
    """Play a station (currently a pandora station (eg 'Neil Young') or 'wnyc'
    The default is 'wnyc'"""
    sonos_actions.play_station(station)

@cli.command()
@click.argument('track_artist', required=True)
@pass_config
def playtrack(config, track_artist):
    '''Play a track: sonos playtrack "harvest by neil young"'''
    if 'by' in track_artist:
        title, artist = track_artist.split(' by ')
    else:
        title, artist = track_artist, ''

    s = 'title:' + ' AND title:'.join(title.split())
    if artist:
        s = s + ' artist:' + ' AND artist:'.join(artist.split())

    result = config.solr.search(s, rows=1) 
    if not len(result):
        #return f"I couldn't find the track {title}{' by'+artist if artist else ''}."
        click.echo(f"Couldn't find track {title}{' by'+artist if artist else ''}")
        return

    track = result.docs[0]
    uri = track['uri']
    sonos_actions.play(True, [uri]) # add
    click.echo(f"{track.get('title', '')} by {track.get('artist', '')} " \
            f"from album {track.get('album', '')}")

@cli.command()
def louder():
    '''Turn the volume higher'''
    sonos_actions.turn_volume("louder")

@cli.command()
def quieter():
    '''Turn the volume lower'''
    sonos_actions.turn_volume("quieter")

@cli.command()
def pause():
    '''Pause playback'''
    sonos_actions.playback('pause')

@cli.command()
def resume():
    '''Resume playback'''
    sonos_actions.playback('play')

@cli.command()
def next():
    '''Next track'''
    sonos_actions.playback('next')

@cli.command()
def trackinfo():
    '''Detailed info for the currently playing track'''
    track_info = sonos_actions.current()
    if track_info:
        msg = "\n"+"\n\n".join([f"{bold(colorize(x, 'magenta'))}: {colorize(y, 'bold')}" for x,y in track_info.items()])+"\n"
    else:
        msg = "Nothing appears to be playing"

    click.echo(msg)

@cli.command()
def what():
    '''Track, artist and album for the currently playing track'''
    response = sonos_actions.current_track_info()
    if response:
        click.echo(colorize(response, 'green'))
    else:
        click.echo(colorize("Nothing appears to be playing", 'red'))

@cli.command()
def showqueue():
    '''Show the queue and the currently playing track'''
    lst = sonos_actions.list_queue()
    if not lst:
        click.echo("The queue is empty")
        return
    else:
        q = list(enumerate(lst, 1))
        track_info = sonos_actions.current()

        if track_info:
            cur_pos = int(track_info['playlist_position'])
            q[cur_pos-1] = (cur_pos, colorize(q[cur_pos-1][1], 'green'))

        for num,track in q:
            click.echo(f"{num}. {track}")

@cli.command()
def clearqueue():
    '''Clear the queue'''
    sonos_actions.clear_queue()

@cli.command()
def lyrics():
    '''Retrieve lyrics for the current track'''
    track = sonos_actions.current()['title']
    artist = sonos_actions.current()['artist']
    lyrics = get_lyrics(artist, track)
  
    if not lyrics:
        click.echo("Couldn't retrieve lyrics")
    else:
        click.echo(lyrics)

@cli.command()
@click.argument('artist', type=click.STRING, required=True)
def shuffle(artist):
    '''Shuffle the songs from an artist'''
    msg = sonos_actions.shuffle(artist)
    click.echo(msg)

@cli.command()
@click.argument('album_artist', type=click.STRING, required=True)
@pass_config
def playalbum(config, album_artist):
    '''Play an album: playalbum "harvest by neil young"'''
    if 'by' in album_artist:
         album, artist = album_artist.split(' by ')
    else:
         album, artist = album_artist, ''

    s = 'album:' + ' AND album:'.join(album.split())
    if artist:
        s = s + ' artist:' + ' AND artist:'.join(artist.split())

    #only brings back actual matches but 25 seems like max for most albums
    result = config.solr.search(s, fl='score,track,uri,artist,title,album',
                         sort='score desc', rows=25) 

    tracks = result.docs
    if  not tracks:
        click.echo(f"I couldn't find {album_artist}")
        return
        
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
    #return f"I will play {len(uris)} tracks from {selected_album}:\n{title_list}."
    click.echo(f"{len(uris)} tracks from {selected_album}:\n{title_list}")

@cli.command()
@click.argument('pos', type=click.INT, required=True)
@pass_config
def playfromqueue(config, pos):
    '''Play track from queue position - top of list is position #1'''
    lst = sonos_actions.list_queue()
    if 0 < pos <= len(lst):
        sonos_actions.play_from_queue(pos-1)
        if config.verbose:
            click.echo(f"Playing track {pos}: {lst[pos-1]}")
    else:
        click.echo(f"{s} is out of the range of the queue")

@cli.command()
@click.argument('artists', type=click.STRING, required=True, nargs=-1)
@pass_config
def mix(config, artists):
    '''Mix as many artists as you'd like:  sonos mix "Neil Young" "Jason Isbell" "Patty Griffin"'''
    tracklist = []
    for artist in artists:
        s = 'artist:' + ' AND artist:'.join(artist.split())
        result = config.solr.search(s, fl='artist,title,uri', rows=500) 
        count = len(result)
        if count:
            print(f"Total track count for {artist} was {count}")
            tracks = result.docs
            k = 5 if count >= 5 else count
            random_tracks = random.sample(tracks, k)
            tracklist.extend(random_tracks)
        else:
            click.echo(f"I couldn't find any tracks for {artist}")
            return

    random.shuffle(tracklist)
    uris = [t.get('uri') for t in tracklist]
    sonos_actions.play(False, uris)
    
    #random.shuffle(tracks)
    titles = [t.get('title', '')+'-'+t.get('artist', '') for t in tracklist]
    title_list = "\n".join([f"{t[0]}. {t[1]}" for t in enumerate(titles, start=1)])
    click.echo(f"The mix for {' and '.join(artists)}:\n{title_list}")

if __name__ == "__main__":
    play_station()
