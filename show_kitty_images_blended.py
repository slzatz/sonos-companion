#!/home/slzatz/sonos-companion/bin/python

'''
Uses kitty graphics api to display either jpegs or png images from web
search for artist whose music is playing on Sonos.
'''
import time
import os
import sys
from apiclient import discovery #google custom search api
import httplib2 #needed by the google custom search engine module apiclient
from ipaddress import ip_address
from config import google_api_key, speaker, image_size #speaker = "192.168.86.23" -> Office2
from artist_images_db import *
from display_image import display_image, display_blended_image, generate_image, show_image, blend_images
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + sys.path
import soco
#from soco import config as soco_config

def get_artist_images(name):
    '''Function if an artist is playing who has under 5 images'''

    print(f"**************Google Custom Search Engine Request for {name} **************")
    http = httplib2.Http()
    service = discovery.build('customsearch', 'v1',
                              developerKey=google_api_key, http=http)
    z = service.cse().list(q=name, searchType='image', imgType='face', #alternative type is photo
                           imgSize='xxlarge', num=10, 
                           cx='007924195092800608279:0o2y8a3v-kw').execute() 

    try:
        a = session.query(Artist).filter(func.lower(Artist.name)==name.lower()).one()
    except NoResultFound:
        print("Don't have that name in db so created it")
        a = Artist()
        a.name = name
        session.add(a)
        session.commit()
    except Exception as e:
        print("a = session.query(Artist).filter(func.lower.. error:", e) 
        return []

    # must delete images before you can add new whole new set of images
    # but could just add to existing without deleting
    session.query(Image).filter_by(artist_id=a.id).delete()
    session.commit()

    images = []

    for data in z.get('items', []): 
        image=Image()
        image.link = data['link']
        image.width = data['image']['width']
        image.height = data['image']['height']
        image.ok = True
        images.append(image)

    a.images = images
    session.commit()
            
    print("images = ", images)
    return images 


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
    img_current = img_previous = image = None
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
                prev_title = title
                artist = track.get('artist', '')
                if not artist:
                    images = all_images = []
                    time.sleep(5)
                    continue

                try:
                    a = session.query(Artist).filter(func.lower(Artist.name)==artist.lower()).one()
                except NoResultFound:
                    # must be new artist so get images
                    all_images = get_artist_images(artist)
                    if not images:
                        print("Could not find images for {}".format(artist))
                except Exception as e:
                    print("error trying to find artist:", e)
                    all_images = []
                else:
                    all_images = [im for im in a.images if im.ok]
                    if len(all_images) < 5:
                        print("fewer than 5 images so getting new set of images for artist")
                        all_images = get_artist_images(artist)
                        if not all_images:
                            print(f"Could not find images for {artist}")

                images = all_images[::]

           # for blended I think we actually hold the PIL image
           # I think we continuously blend images like once every second
           # everything is a blend potentially that runs from 0 to 1
           # I think you would have:
           #     img_previous  and img_next and at some point img_next becomes img_previous


            if images:
                if time.time() > t0 + 25:
                    img_previous = img_current
                    while 1:
                        image = images.pop()
                        #sys.stdout.buffer.write(b"\x1b[2J")
                        img_current = generate_image(image.link, image_size, image_size)
                        if img_current:
                            break
                        if not images:
                            images = all_images[::]
                    t0 = time.time()
                    alpha = 0

                if img_previous and img_current:
                    alpha += .025
                    img_blend = blend_images(img_previous, img_current, alpha)
                    if img_blend:
                        sys.stdout.buffer.write(b"\x1b[H")
                        show_image(img_blend)
                elif img_current:
                    #display_image(image.link, image_size, image_size)
                    sys.stdout.buffer.write(b"\x1b[H")
                    show_image(img_current)

                # time.sleep(1)
                #print(f"\n{artist}: {title}\n{image.link}")

                
            else:
                images = all_images[::]


            time.sleep(.1) # was .1

