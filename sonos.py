#!bin/python

'''Click-based command line script to control sonos.
There are a bunch of aliases in .bashrc'''

import click
import sonos_actions
from get_lyrics import get_lyrics #uses genius.com
from display_image import display_image

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
    if not master:
        sonos_actions.master = sonos_actions.set_master("192.168.86.23")
        master = "Office2"
    else:
        sonos_actions.master = sonos_actions.set_master(master)

    if verbose:
        click.echo(f"Master speaker is {master}: {sonos_actions.master.ip_address}")

@cli.command()
@click.argument('station', default="wnyc", required=False)
def playstation(station):
    """Play a station (currently a pandora station (eg 'Neil Young') or 'wnyc'
    The default is 'wnyc'"""
    sonos_actions.play_station(station)

@cli.command()
@click.argument('title', required=True)
@click.option("-a", "--artist", help="The artist for the track to be played")
def playtrack(title, artist):
    '''Play a track -> sonos playtrack "harvest" -a "neil young"'''
    msg = sonos_actions.play_track(title, artist)
    click.echo(msg)

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
    '''Image, title, artist and album for the currently playing track'''
    track = sonos_actions.current_track_info(False) #False = don't return text; return a dictionary

    if track:
        display_image(track['artist'])

        click.secho("\nartist: ", nl=False, fg='cyan', bold=True)
        click.echo(f"{track['artist']}")
        click.secho("title: ", nl=False, fg='cyan', bold=True)
        click.echo(f"{track['title']}")
        click.secho("album: ", nl=False, fg='cyan', bold=True)
        click.echo(f"{track['album']}\n")
    else:
        click.secho("Nothing appears to be playing! ", nl=False, fg='red', bold=True)

    

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
    title = sonos_actions.current()['title']
    artist = sonos_actions.current()['artist']
    lyrics = get_lyrics(artist, title)
    click.secho(f"\n{title} by {artist}", fg='cyan', bold=True, nl=False)
  
    if not lyrics:
        click.echo("Couldn't retrieve lyrics")
    else:
        click.echo(lyrics)

@cli.command()
@click.argument('artists', type=click.STRING, required=True, nargs=-1)
def shuffle(artists):
    '''Shuffle the songs from one or more artists: sonos shuffle "patty griffin" "neil young" "aimee mann"'''
    msg = sonos_actions.shuffle(artists)
    click.echo(msg)

@cli.command()
@click.argument('album', type=click.STRING, required=True)
@click.option('-a', '--artist', help="Artist to help find album to be played")
def playalbum(album, artist=None):
    '''Play an album -> sonos playalbum "A man needs a maid" -a "neil young"'''
    msg = sonos_actions.play_album(album, artist)
    click.echo(msg)

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
@click.argument('artist', type=click.STRING, required=True)
def image(artist):
    '''Display image of artist -> sonos image "neil young"'''
    display_image(artist)

if __name__ == "__main__":
    play_station()
