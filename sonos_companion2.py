#!/home/slzatz/sonos-companion/bin/python

'''
Uses kitty graphics api to display either jpegs or png images from web
or display pngs stored in the database
search for artist whose music is playing on Sonos.
'''
import time
import datetime
import os
import sys
from io import BytesIO
import wikipedia
from ipaddress import ip_address
from config import speaker, sonos_image_size #, ec_id, ec_pw, ec_host #speaker = "192.168.86.23" -> Office2
from display_image import generate_image, show_image, blend_images, get_screen_size
from get_lyrics import get_lyrics #uses genius.com
from pathlib import Path
home = str(Path.home())
sys.path = [os.path.join(home, 'SoCo')] + sys.path
import soco
#from soco import config as soco_config - needed this in early days


display_size = sonos_image_size

def get_page(topic):
    try:
        #if nothing comes back could repeat with auto_suggest = True
        page = wikipedia.page(topic, auto_suggest=False) # I changed auto_suggest = False to the default (I changed page function in wikipedia.py
    except Exception as e:
        print(f"Couldn't find {topic} wikipedia: {e}")
        return
    return page

def get_all_wikipedia_image_uris(page):
    if page is None:
        return []
    uri_list = list()
    for uri in page.images:        
        pos = uri.rfind('.')
        if uri[pos:].lower() in [".jpg", ".jpeg"]:
            uri_list.append(uri)

    return uri_list

if __name__ == "__main__":

    num_transport_errors = 0
    num_track_errors = 0

    try:
        ip_address(speaker)
    except ValueError:
        sys.exit(1)
    else:
        master = soco.SoCo(speaker)

    prev_title = ""
    prev_artist = ""
    lyrics = ""
    line_num = prev_line_num = 0
    rows = []
    all_rows = []
    img_current = img_previous = image = None
    alpha = 1.1
    need_scroll = False
    s = ""

    print("\x1b[?25l") # hide cursor

    while 1:
        x = get_screen_size()
        ret = f"\n\x1b[{(display_size//x.cell_width) + 2}C"

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
                prev_title = title
                # should erase last artist

                screen_rows = get_screen_size().rows
                need_scroll = False
                duration = track.get('duration', 0)
                artist = track.get('artist', '')
                sys.stdout.write("\x1b[2J") #erase screen, go home
                sys.stdout.write("\x1b[H") #necessary - above doesn't go home
                sys.stdout.flush()
                lyrics = get_lyrics(artist, title)
                if not lyrics:
                    lyrics = f"Couldn't retrieve lyrics for {title} by {artist}"

                line_count = lyrics.count('\n') 
                zz = lyrics.split("\n")

                if screen_rows - 3 > line_count:
                    print(f"\x1b[0;{3 + display_size//x.cell_width}H", end="") 
                    print(f"\x1b[0;31m{title} by {artist}: 1/1\n{ret}\x1b[0m", end="")
                    print(ret.join(zz), end="")
                else:
                    pages = line_count//screen_rows + 1
                    line_num = screen_rows - 3
                    prev_line_num = line_num
                    n = 2
                    last_position = 0
                    print(f"\x1b[0;{3 + display_size//x.cell_width}H", end="") 
                    print(f"\x1b[0;31m{title} by {artist}: 1/{pages}\n{ret}\x1b[0m", end="")
                    print(ret.join(zz[:line_num + 1]), end="")
                    need_scroll = True

                    duration_dt = datetime.datetime.strptime(duration, "%H:%M:%S")    
                    duration_sec = duration_dt.minute*60 + duration_dt.second

                if not artist:
                    rows = all_rows = []
                    time.sleep(5)
                    continue

                wiki_page = get_page(artist)
                all_rows = get_all_wikipedia_image_uris(wiki_page)
                #all_rows = cur.fetchall()
                rows = all_rows[::]
                alpha = 1.1 
                if artist != prev_artist:
                    img_current = None
                    prev_artist = artist
            else:
                if need_scroll:
                    position_dt = datetime.datetime.strptime(position, "%H:%M:%S")
                    position_sec = position_dt.minute*60 + position_dt.second - last_position
                    if position_sec > duration_sec/pages:
                        sys.stdout.write("\x1b[2J") #erase screen, go home
                        sys.stdout.write("\x1b[H") #necessary - above doesn't go home
                        sys.stdout.flush()
                        print(f"\x1b[0;{3 + display_size//x.cell_width}H", end="") 
                        print(f"\x1b[0;31m{title} by {artist}: {n}/{pages}\n{ret}\x1b[0m", end="")
                        last_position = position_sec
                        line_num = prev_line_num + screen_rows - 3

                        if n == pages:
                            first_line = len(zz) - (screen_rows - 3)
                            print(ret.join(zz[first_line:]))
                            need_scroll = False
                        else:
                            print(ret.join(zz[prev_line_num:line_num + 1]))
                            prev_line_num = line_num
                            n += 1
                        



            if rows:
                if alpha > 1.0:
                    # first time through with  new track img_current is None
                    img_previous = img_current
                    while 1:
                        row = rows.pop()
                        img_current = generate_image(row, sonos_image_size, sonos_image_size)
                        if img_current:
                            break
                        if not rows:
                            rows = all_rows[::]
                    alpha = 0

                if img_previous and img_current:
                    #alpha += .015 # .025 goes will with time.sleep(.05)
                    img_blend = blend_images(img_previous, img_current, alpha)
                    if img_blend:
                        sys.stdout.buffer.write(b"\x1b[H")
                        show_image(img_blend)
                        print(f"\n\x1b[1m{title} {artist}\x1b[0m\n{s}")
                        alpha += .015 
                elif img_current:
                    sys.stdout.buffer.write(b"\x1b[H")
                    show_image(img_current)
                    print(f"\n\x1b[1m{title} {artist}\x1b[0m\n{s}")
                    alpha += 0.25
                
            else:
                rows = all_rows[::]

            time.sleep(.01) 

