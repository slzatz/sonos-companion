#!/home/slzatz/sonos-companion/bin/python

'''
Uses kitty graphics api to display either jpegs or png images from wikimedia search
for artist whose music is playing on Sonos.
'''
import time
import datetime
import random
import sys
import wikipedia
from bs4 import BeautifulSoup
import requests
from config import speaker 
from display_image import generate_image, generate_image_from_file, show_image, blend_images, get_screen_size
from get_lyrics import get_lyrics
from soco.discovery import by_name

# cache for image urls - ? should actually cache the images
artists = {}

WIKI_REQUEST = "https://commons.wikimedia.org/w/index.php?search={search_term}&title=Special:MediaSearch&go=Go&type=image&uselang=en"
WIKI_FILE = "https://commons.wikimedia.org/wiki/File:" #Bob_Dylan_portrait.jpg
NUM_IMAGES = 8

def get_wiki_images(search_term):
    search_term = search_term.lower()
    search_term = search_term.replace(' ', '+')
    try:
        response  = requests.get(WIKI_REQUEST.format(search_term=search_term))
    except Exception as e:
        print(e)
        return []

    html = BeautifulSoup(response.text, 'html.parser')

    #div = html.find('div', class_="wbmi-media-search-results__list wbmi-media-search-results__list--image")
    # this change noted on 06/21/2021
    div = html.find('div', class_="sdms-search-results__list sdms-search-results__list--image")
    zz = div.find_all('a')
    zz = random.sample(zz, NUM_IMAGES if len(zz) >= NUM_IMAGES else len(zz))
    uris = []
    for link in zz:
        try:
            response = requests.get(link.get('href'))
        except Exception as e:
            print(e)
            continue
        html = BeautifulSoup(response.text, 'html.parser')
        div = html.find('div', class_="fullImageLink")
        img = div.a.get('href')
        uris.append(img)

    return uris

def filter_wiki_images(artist, uris):
    a = artist.lower().replace(" ", "_")
    b = artist.lower().replace(" ", "")
    filtered_uris = []
    for uri in uris:
        # match on artist name
        if a in uri.lower(): # sometimes name has a hyphen (like Drive-by Truckers)
            filtered_uris.append(uri) 
        elif a in uri.lower().replace("-", "_"):
            filtered_uris.append(uri) 
        # match on artist name with no spaces (seems rare)
        elif b in uri.lower():
            filtered_uris.append(uri) 
        else:
            # match if description has artist name
            zz = uri.split("/")[-1]
            xx = WIKI_FILE+zz
            response = requests.get(xx)
            html = BeautifulSoup(response.text, 'html.parser')
            td = html.find('td', class_="description")
            if td:
                if artist.lower() in td.get_text().lower().replace("_", " ").replace("-", " ")[:50]:
                    filtered_uris.append(uri) 
    return filtered_uris

if __name__ == "__main__":

    if len(sys.argv) > 1:
        bold_lyrics = sys.argv[1] == 'bold'
    else:
        bold_lyrics = False
        
    num_transport_errors = 0
    num_track_errors = 0

    master = by_name(speaker)

    try:
        #ip_address(speaker)
        master = by_name(speaker)
    except ValueError:
        print("Could not set master speaker by name")
        sys.exit(1)
    #else:
    #    master = soco.SoCo(speaker)

    prev_title = ""
    prev_artist = ""
    lyrics = ""
    line_num = prev_line_num = 0
    rows = []
    all_rows = []
    img_current = img_previous = image = None
    alpha = 1.1
    need_scroll = False

    print("\x1b[?25l") # hide cursor

    while 1:
        x = get_screen_size()
        display_size = x.width//2
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
                print(f"Encountered error in track = master.get_current_track_info(): {e}")
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

                screen_rows = get_screen_size().rows - 3 ###
                need_scroll = False
                duration = track.get('duration', 0)
                artist = track.get('artist', '')
                sys.stdout.write("\x1b[2J") #erase screen, go home
                sys.stdout.write("\x1b[H") #necessary - above doesn't go home
                sys.stdout.flush()
                lyrics = get_lyrics(artist, title)
                if not lyrics:
                    lyrics = f"Couldn't retrieve lyrics for:\n{title} by {artist}"

                zz = []
                prev_line = None
                for line in lyrics.split("\n"):
                    if not(prev_line == "" and line == ""):
                        zz.append(line)
                        prev_line = line
                line_count = len(zz) 

                if screen_rows - 3 > line_count:
                    print(f"\x1b[0;{3 + display_size//x.cell_width}H", end="") 
                    print(f"\x1b[1;31m{title} by {artist}: 1/1\n{ret}\x1b[0m", end="")
                    if bold_lyrics:
                        sys.stdout.write("\x1b[1m") #bold
                    print(ret.join(zz), end="")
                    sys.stdout.write("\x1b[0m")
                else:
                    pages = line_count//screen_rows + 1
                    line_num = screen_rows - 3
                    prev_line_num = line_num
                    n = 2
                    last_position = 0
                    print(f"\x1b[0;{3 + display_size//x.cell_width}H", end="") 
                    print(f"\x1b[1;31m{title} by {artist}: 1/{pages}\n{ret}\x1b[0m", end="")
                    if bold_lyrics:
                        sys.stdout.write("\x1b[1m") #bold
                    print(ret.join(zz[:line_num + 1]), end="")
                    sys.stdout.write("\x1b[0m")
                    need_scroll = True

                    duration_dt = datetime.datetime.strptime(duration, "%H:%M:%S")    
                    duration_sec = duration_dt.minute*60 + duration_dt.second

                sys.stdout.write("\x1b[0m") #bold

                if not artist:
                    rows = all_rows = []
                    time.sleep(5)
                    continue

                if artist in artists:
                    all_rows = artists[artist]
                else:
                    all_rows = get_wiki_images(artist)
                    #print(all_rows)
                    all_rows = filter_wiki_images(artist, all_rows)
                    #print("all_rows", all_rows, "all_rows")
                    artists[artist] = all_rows

                rows = all_rows[::]
                #print("rows", rows, "rows") #debug
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
                        print(f"\x1b[1;31m{title} by {artist}: {n}/{pages}\n{ret}\x1b[0m", end="")
                        last_position = position_sec
                        line_num = prev_line_num + screen_rows - 3

                        if bold_lyrics:
                            sys.stdout.write("\x1b[1m") #bold
                        if n == pages:
                            first_line = len(zz) - (screen_rows - 3)
                            print(ret.join(zz[first_line:]))
                            need_scroll = False
                        else:
                            print(ret.join(zz[prev_line_num:line_num + 1]))
                            prev_line_num = line_num
                            n += 1
                        
                        sys.stdout.write("\x1b[0m") 

            if rows:
                #print("got here")
                if alpha > 1.0:
                    # first time through with new track img_current is None
                    img_previous = img_current
                    while 1:
                        row = rows.pop()
                        #print(row)
                        img_current = generate_image(row, display_size, display_size)
                        #print(img_current)
                        if img_current:
                            break

                        if not rows:
                            rows = all_rows[::]

                        time.sleep(10)

                    if img_previous:
                        alpha = 0

                if img_previous and img_current:
                    #alpha += .015 # .025 goes will with time.sleep(.05)
                    img_blend = blend_images(img_previous, img_current, alpha)
                    if img_blend:
                        sys.stdout.buffer.write(b"\x1b[H")
                        show_image(img_blend)
                        #print(f"\n\x1b[1m{artist}\x1b[0m\n{row}yyyyy{alpha}", end="")
                        #print(f"\n\x1b[1m{artist}\x1b[0m\n{row}", end="")
                        print(f"\n\x1b[1m{artist}\x1b[0m - {len(all_rows)} images: {row}", end="")
                        alpha += .015 
                elif img_current:
                    sys.stdout.buffer.write(b"\x1b[H")
                    show_image(img_current)
                    #print(f"\n\x1b[1m{artist}\x1b[0m\n{row}xxxx{alpha}", end="")
                    #print(f"\n\x1b[1m{artist}\x1b[0m\n{row}", end="")
                    print(f"\n\x1b[1m{artist}\x1b[0m - {len(all_rows)} images: {row}", end="")
                    alpha += 0.25
                
            else:
                rows = all_rows[::]

            time.sleep(.01) 

