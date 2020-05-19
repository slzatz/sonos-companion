#!/home/slzatz/sonos-companion/bin/python

'''
Uses kitty graphics api to display either jpegs or png images from web
search for artist whose music is playing on Sonos.
'''
import time
import os
import sys
from io import BytesIO
from ipaddress import ip_address
import psycopg2
from config import speaker, sonos_image_size, ec_id, ec_pw, ec_host #speaker = "192.168.86.23" -> Office2
from display_image import display_image, display_blended_image, generate_image, show_image, blend_images
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + sys.path
import soco
#from soco import config as soco_config

params = {
  'database': 'artist_images',
  'user': ec_id,
  'password': ec_pw,
  'host': ec_host,
  'port': 5432
}
conn = psycopg2.connect(**params)
cur = conn.cursor()

if __name__ == "__main__":

    try:
        ip_address(speaker)
    except ValueError:
        sys.exit(1)
    else:
        master = soco.SoCo(speaker)

    prev_title = ""
    rows = []
    all_rows = []
    img_current = img_previous = image = None
    alpha = 1.1
    s = ""

    #last_image = None # for blended images - not doing it now

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
                # should erase last artist
                im_current = None
                prev_title = title
                artist = track.get('artist', '')
                if not artist:
                    rows = all_rows = []
                    time.sleep(5)
                    continue

                #sql = "SELECT id,name FROM artists WHERE LOWER(name)=LOWER(%s);"
                sql = "SELECT id FROM artists WHERE LOWER(name)=LOWER(%s);"
                cur.execute(sql, (artist,))
                row = cur.fetchone()
                if row:
                    #artist_id, name = row
                    artist_id = row[0]
                else:
                    print(f"Can't find {artist}!!")

                cur.execute(f"SELECT id,link FROM images WHERE artist_id={artist_id}")
                all_rows = cur.fetchall()
                rows = all_rows[::]
                alpha = 1.1 
                #print(f"\x1b[1m{title} {artist}\x1b[0m\n")

            if rows:
                if alpha > 1.0:
                    # first time through with  new track img_current is None
                    img_previous = img_current
                    while 1:
                        row = rows.pop()
                        #sys.stdout.buffer.write(b"\x1b[2J")
                        cur.execute("SELECT image FROM image_files WHERE image_id=%s", (row[0],))
                        r = cur.fetchone()
                        if r:
                            s = "This image is being stored as BYTES in the database"
                            #print("This image is being stored as BYTES in the database")
                            #show_image(BytesIO(r[0]))
                            img_current = BytesIO(r[0])
                            print()
                        else:
                            s = "This image is being stored as just a URL in the database"
                            #print("This image is being stored as just a URL in the database")
                            img_current = generate_image(row[1], sonos_image_size, sonos_image_size)
                            print()
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
                        alpha += .015 # .025 goes will with time.sleep(.05)
                # I believe this is the path when the title changes
                elif img_current:
                    #alpha = 1.1
                    #display_image(image.link, image_size, image_size)
                    sys.stdout.buffer.write(b"\x1b[H")
                    show_image(img_current)
                    print(f"\n\x1b[1m{title} {artist}\x1b[0m\n{s}")
                    alpha += 0.25

                #print(f"\n{artist}: {title}\n{image.link}")

                
            else:
                rows = all_rows[::]


            time.sleep(.01) 

