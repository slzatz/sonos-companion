#!/home/slzatz/sonos-companion/bin/python

'''
Uses kitty graphics api to display either jpegs or png images from web
search for artist whose music is playing on Sonos.
'''
import time
import os
import sys
from ipaddress import ip_address
from get_lyrics import get_lyrics #uses genius.com
from config import speaker, image_size #speaker = "192.168.86.23" -> Office2
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + sys.path
import soco
#from soco import config as soco_config

if __name__ == "__main__":

    try:
        ip_address(speaker)
    except ValueError:
        sys.exit(1)
    else:
        master = soco.SoCo(speaker)

    prev_title = ""
    t0 = time.time()
    images = []
    all_images = []

    while 1:
        try:
            state = master.get_current_transport_info()['current_transport_state']
        except Exception as e:
            print(f"Encountered error in state = master.get_current_transport_info(): {e}")
            state = 'ERROR'
            time.sleep(1)
            continue

        if state == 'PLAYING':

            try:
                track = master.get_current_track_info()
            except Exception as e:
                print("Encountered error in track = master.get_current_track_info(): {e}")
                time.sleep(1)
                continue

            title = track.get('title', '')
            
            if prev_title != title:
                artist = track.get('artist', '')
                prev_title = title

                lyrics = get_lyrics(artist, title)
                print(f"\n{title} by {artist}")
      
                if not lyrics:
                    print("Couldn't retrieve lyrics")
                else:
                    print(lyrics)

            time.sleep(.5) # was .1

