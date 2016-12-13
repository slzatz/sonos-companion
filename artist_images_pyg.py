from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future_builtins import *

import requests
from cStringIO import StringIO
from time import sleep
import platform
#import sys
import json
import pygame
from pygame.locals import USEREVENT
import os
import random
import wand.image
import textwrap
#from artist_images_db import *
from artist_images_db import *
import lxml.html

wrapper = textwrap.TextWrapper(width=72, replace_whitespace=False)  

#last.fm
base_url = "http://ws.audioscrobbler.com/2.0/"
api_key = "1c55c0a239072889fa7c11df73ecd566"

if platform.system() == 'Windows':
    os.environ['SDL_VIDEODRIVER'] = 'windib'
elif platform.machine() == 'armv6l':
    # from https://github.com/adafruit/adafruit-pi-cam/blob/master/cam.py
    os.putenv('SDL_VIDEODRIVER', 'fbcon')
    os.putenv('SDL_FBDEV', '/dev/fb1')
else:
    os.putenv('SDL_VIDEODRIVER', 'x11')

pygame.init()
pygame.mouse.set_visible(0)

DISPLAY = (640,480)

screen = pygame.display.set_mode(DISPLAY)
screen.fill((0,0,0))

font = pygame.font.SysFont('Sans', 50)

text = font.render("Artists", True, (255, 0, 0))

screen.blit(text, (0,0)) 
pygame.display.flip()

def get_artist_info(artist, autocorrect=0):
    
    payload = {'method':'artist.getinfo', 'artist':artist, 'autocorrect':autocorrect, 'format':'json', 'api_key':api_key}
    
    try:
        r = requests.get(base_url, params=payload)
        bio = r.json()['artist']['bio']['summary']
        text = lxml.html.fromstring(bio).text_content()
        idx = text.find("Read more")
        if idx != -1:
            text = text[:idx]
        
        return text
        
    except Exception as e:
        print("Exception in get_artist_info: ", e)
        return ''

def get_artist_images(name):

    print("**************Google Custom Search Engine Request for "+name+"**************")
    http = httplib2.Http()
    service = discovery.build('customsearch', 'v1',  developerKey=google_api_key, http=http)
    z = service.cse().list(q=name, searchType='image', imgType='face', imgSize='xlarge', num=10, cx='007924195092800608279:0o2y8a3v-kw').execute() 

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
    session.query(Image).filter_by(artist_id=a.id).delete()
    session.commit()

    # the below works and deletes the images one at a time
    #for image in a.images:
    #    # with change in cascade don on 12-11-2016 may be possible to do a.images = [];session.commit()
    #    print image.link, image.width, image.height,image.ok
    #    session.delete(image)
    #session.commit()    

    images = []

    for data in z['items']:
        
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

#following not in use    
def get_artist_image(artist,image):

    #image = session.query(Image).join(Artist).filter(Artist.name == artist)[i] #.all()
    url = image.link
    try:
        response = requests.get(url)
    except Exception as e:
        print( "response = requests.get(url) generated exception:", e)
        image.ok = False
        print("changed image status to False")
        session.commit()
        img = wand.image.Image(filename = "test.bmp")
    else:

        try:
            img = wand.image.Image(file=StringIO(response.content))
        except Exception as e:
            img = wand.image.Image(filename = "test.bmp")
            print ("img = wand.image.Image(file=StringIO(response.content)) generated exception:", e)
            image.ok = False
            session.commit()

    size = str(DISPLAY[0])+'x'+str(DISPLAY[1])+'^'
    img.transform(resize = size)
    img = img.convert('bmp')
    #img.save(filename = "test1.bmp")
    img = pygame.image.load("test1.bmp").convert()

    return img

def display_artist_image(artist_name, image):

    #image = session.query(Image).join(Artist).filter(Artist.name == artist_name)[i] #.all()
    url = image.link
    try:
        response = requests.get(url)
    except Exception as e:
        print( "response = requests.get(url) generated exception:", e)
        image.ok = False
        print("changed image ok to False")
        session.commit()
        return
        #img = wand.image.Image(filename = "test.bmp")
    else:

        try:
            img = wand.image.Image(file=StringIO(response.content))
        except Exception as e:
            print ("img = wand.image.Image(file=StringIO(response.content)) generated exception:", e)
            print("artist=",artist_name)
            print("image=",image)
            image.ok = False
            session.commit()
            return

    size = str(DISPLAY[0])+'x'+str(DISPLAY[1])+'^'

    try:
        img.transform(resize = size)
        img = img.convert('bmp')
    except Exception as e:
        print("img.transform or img.convert error:", e)
        print("artist=",artist_name)
        print("image=",image)
        image.ok = False
        session.commit()
        return

    f = StringIO()
    try:
        #img.save(filename = "test1.bmp")
        img.save(f)
    except wand.exceptions.OptionError as e:
        print("Problem saving image:", e)
        return

    f.seek(0)
    #img = pygame.image.load("test1.bmp").convert()
    img = pygame.image.load(f, 'bmp').convert()
    f.close()
    
    screen.fill((0,0,0)) 
    screen.blit(img, (0,0))      
    pygame.display.flip()

    sleep(5)

    img.set_alpha(75) # the lower the number the more faded - 75 seems too faded; try 100

    font = pygame.font.SysFont('Sans', 20)
    font.set_bold(True)
    
    text1 = font.render("Artist: "+artist_name, True, (255, 0, 0))
    
    screen.fill((0,0,0)) 
    screen.blit(img, (0,0))      
    screen.blit(text1, (0,0))

    font = pygame.font.SysFont('Sans', 16)
 
    text2 = get_artist_info(artist_name)
    text2 = wrapper.fill(text2)
    lines = text2.split('\n')
    
    z = 30
    for line in lines:
        text = font.render(line, True, (255, 0, 0))
	screen.blit(text, (0,z))
	z+=20

    pygame.display.flip()

    #os.remove("test1.bmp") 

# not in use
def show_artist():
    img.set_alpha(75) #0 - 100 the lower the number the more faded 

    font = pygame.font.SysFont('Sans', 30)
    font.set_bold(True)
    
    text1 = font.render("Artist: "+artist, True, (255, 0, 0))
    
    screen.fill((0,0,0)) 
    screen.blit(img, (0,0))      
    screen.blit(text1, (0,0))

    pygame.display.flip()

    #os.remove("test1.bmp") 

if __name__ == '__main__':

    SHOWNEWIMAGE = USEREVENT+1
    artists = session.query(Artist).all()
    L = len(artists)
    print("Number of artists = {}".format(L))
    
    pygame.time.set_timer(SHOWNEWIMAGE, 2000)

    while 1:

        #if pygame.event.get(SHOWNEWIMAGE):
            #artist_name = artists[random.randrange(0,L-1)].name
            #N = session.query(Image).join(Artist).filter(and_(Artist.name==artist_name, Image.ok == True)).count()
            #if N:
            #    image = session.query(Image).join(Artist).filter(and_(Artist.name == artist, Image.ok == True))[random.randrange(0,N-1)] 
            #    display_artist_image(artist_name, image) 

        if pygame.event.get(SHOWNEWIMAGE):
            #artist = artists[random.randrange(0,L-1)]
            artist = random.choice(artists)
            images = artist.images
            if images:
                #image = images[random.randrange(0,len(images)-1)]
                image = random.choice(images)
                display_artist_image(artist.name, image) 
        sleep(1)

