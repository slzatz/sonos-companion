#!/home/slzatz/sonos-companion/bin/python

'''
Uses kitty graphics api to display either jpegs or png images from web
search for artist whose music is playing on Sonos.
'''
import time
import datetime
import os
import sys
from ipaddress import ip_address
from get_lyrics import get_lyrics #uses genius.com
from config import speaker, image_size #speaker = "192.168.86.23" -> Office2
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + sys.path
import soco
#from soco import config as soco_config
from display_image import get_screen_size

def findnth(haystack, needle, n):
    parts= haystack.split(needle, n+1)
    if len(parts)<=n+1:
        return -1
    return len(haystack)-len(parts[-1])-len(needle)

if __name__ == "__main__":

    num_transport_errors = 0
    num_track_errors = 0

    screen_rows = get_screen_size()[0]

    try:
        ip_address(speaker)
    except ValueError:
        sys.exit(1)
    else:
        master = soco.SoCo(speaker)

    prev_title = ""
    lyrics = ""
    t0 = time.time()
    images = []
    all_images = []

    while 1:
        try:
            state = master.get_current_transport_info()['current_transport_state']
        except Exception as e:
            print(f"Encountered error in state = master.get_current_transport_info(): {e}")
            state = 'ERROR'
            num_transport_errors += 1
            if num_transport_errors < 3:
                time.sleep(1)
                continue
            else:
                sys.exit(1)

        if state == 'PLAYING':

            try:
                track = master.get_current_track_info()
            except Exception as e:
                print("Encountered error in track = master.get_current_track_info(): {e}")
                num_track_errors += 1
                if num_track_errors < 3:
                    time.sleep(1)
                    continue
                else:
                    sys.exit(1)

            title = track.get('title', '')

            position = track.get('position', 0)
            
            if prev_title != title:
                need_scroll = False
                duration = track.get('duration', 0)

                artist = track.get('artist', '')
                prev_title = title

                sys.stdout.write("\x1b[2J") #erase screen, go home
                sys.stdout.write("\x1b[H")
                sys.stdout.flush()
      
                lyrics = get_lyrics(artist, title)
                if not lyrics:
                    print("Couldn't retrieve lyrics")
                    continue

                line_count = lyrics.count('\n') 
                if screen_rows -3 > line_count:
                    print(f"\n\x1b[0;31m{title} by {artist} page: 1/1\x1b[0m", end="")
                    print(lyrics)
                else:
                    pages = int(line_count/screen_rows) + 1
                    char = findnth(lyrics, '\n', screen_rows - 3)
                    prev_char = char
                    n = 2
                    last_position = 0
                    print(f"\n\x1b[0;31m{title} by {artist} page: 1/{pages}\x1b[0m", end="")
                    print(lyrics[:char])
                    need_scroll = True

                    duration_dt = datetime.datetime.strptime(duration, "%H:%M:%S")    
                    duration_sec = duration_dt.minute*60 + duration_dt.second
            else:
                if need_scroll:
                    position_dt = datetime.datetime.strptime(position, "%H:%M:%S")
                    #position_sec = (position_dt - datetime.datetime(1900, 1, 1).total_seconds()
                    position_sec = position_dt.minute*60 + position_dt.second - last_position
                    if position_sec > duration_sec/pages:
                        print(f"\n\x1b[0;31m{title} by {artist} page: {n}/{pages} \x1b[0;32m(cont.)\x1b[0m") #, end="")
                        char = findnth(lyrics, '\n', n*(screen_rows - 3))
                        print(lyrics[prev_char:char])
                        last_position = position_sec
                        prev_char = char
                        n += 1
                        if n > pages:
                            need_scroll = False

        time.sleep(.5) 

