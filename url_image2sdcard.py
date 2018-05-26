#!bin/python
'''
Image processing for images that are then transferred to sd card of sonos_remote
The images are taken from the artist image db and written to hard drive and
then transferred to sd card
'''
import requests
from io import BytesIO
import wand.image
from artist_images_db import *
import sys
from PIL import Image
from random import shuffle

engine.echo = False

def retrieve_image(x, ext='jpg', size=(640,480)):

    try:
        response = requests.get(x, timeout=5.0)
    except Exception as e:
        print("response = requests.get(url) generated exception: ", e)
        # in some future better world may indicate that the image was bad

        return
    print(f"response.status_code: {response.status_code}")

    if response.status_code != 200:
        return

    f = BytesIO(response.content)
    try:
        gs = is_grey_scale(img_path=f)
    except Exception as e:
        print(f"Grayscale exception: {e}")
        return

    print(f"greyscale = {gs}")

    # m5stack can't display grayscale (is_grey_scale does not seem to be perfect)
    if gs:
        return

    f.seek(0)
    try:
        img = wand.image.Image(file=f)
    except Exception as e:
        print("img = wand.image.Image(file=BytesIO(response.content)) generated exception from url:", x, "Exception:", e)
        # in some future better world may indicate that the image was bad

        return

    try:
        ww = img.width
        hh = img.height
        if ww>=640 and hh>=480:
            print("image > 640 x 480")
            t = ((ww-640)//2,(hh-480)//2,(ww+640)//2,(hh+480)//2) 
            img.crop(*t)
        elif ww>=320 and hh>=240:
            print("image > 320 x 240")
            t = ((ww-320)//2,(hh-240)//2,(ww+320)//2,(hh+240)//2) 
            img.crop(*t)

        img.resize(320,240)
        conv_img = img.convert(ext)
        img.close()
    except Exception as e:
        print("img.transfrom or img.convert error:", e)
        # in some future better world may indicate that the image was bad

        return

    artist_name = artist.name.lower()
    artist_name = artist_name.replace(' ', '_')

    try:
        #f = open('artist_pics/'+artist.name.lower()+'.'+ext, 'wb')
        f = open('artist_pics2/'+artist_name+'.'+ext, 'wb')
    except FileNotFoundError as e:
        print("Problem creating file", e)
        return
    try:
        conv_img.save(f)
        conv_img.close()
    except wand.exceptions.OptionError as e:
        print("Problem saving image:", e)
        # in some future better world may indicate that the image was bad
        f.close()
        return

    f.close()

    return True

# below is hacky way to detect grayscale which m5stack cannot display
def is_grey_scale(img_path=None):
    if not img_path:
        return
    im = Image.open(img_path).convert('RGB')
    w,h = im.size
    for i in range(w):
        for j in range(h):
            r,g,b = im.getpixel((i,j))
            if r != g != b: return False
    return True

artists = session.query(Artist)

for artist in artists:
    images = artist.images
    images = list(artist.images)
    shuffle(images)
    print(f"\n\n{artist.name}: image count:{len(images)}")
    for image in images:
        print(f"Image uri: {image.link}")
        zz = retrieve_image(image.link, ext='jpg')
        if zz:
            break
            
