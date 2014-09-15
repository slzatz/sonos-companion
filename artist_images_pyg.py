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

#following not in use    
def get_artist_image(artist,image):

    #image = session.query(Image).join(Artist).filter(Artist.name == artist)[i] #.all()
    url = image.link
    try:
        response = requests.get(url)
    except Exception as e:
        print( "response = requests.get(url) generated exception:", e)
        image.status = False
        print("changed image status to False")
        session.commit()
        img = wand.image.Image(filename = "test.bmp")
    else:

        try:
            img = wand.image.Image(file=StringIO(response.content))
        except Exception as e:
            img = wand.image.Image(filename = "test.bmp")
            print ("img = wand.image.Image(file=StringIO(response.content)) generated exception:", e)
            image.status = False
            session.commit()

    size = str(DISPLAY[0])+'x'+str(DISPLAY[1])+'^'
    img.transform(resize = size)
    img = img.convert('bmp')
    img.save(filename = "test1.bmp")
    img = pygame.image.load("test1.bmp").convert()

    return img

def display_artist_image(artist, image):

    #image = session.query(Image).join(Artist).filter(Artist.name == artist)[i] #.all()
    url = image.link
    try:
        response = requests.get(url)
    except Exception as detail:
        print( "response = requests.get(url) generated exception:", detail)
        image.status = False
        print("changed image status to False")
        session.commit()
        img = wand.image.Image(filename = "test.bmp")
    else:

        try:
            img = wand.image.Image(file=StringIO(response.content))
        except Exception as detail:
            img = wand.image.Image(filename = "test.bmp")
            print ("img = wand.image.Image(file=StringIO(response.content)) generated exception:", detail)
            image.status = False
            session.commit()

    size = str(DISPLAY[0])+'x'+str(DISPLAY[1])+'^'
    img.transform(resize = size)
    img = img.convert('bmp')
    img.save(filename = "test1.bmp")
    img = pygame.image.load("test1.bmp").convert()
    
    screen.fill((0,0,0)) 
    screen.blit(img, (0,0))      
    pygame.display.flip()

    sleep(5)

    img.set_alpha(75) # the lower the number the more faded - 75 seems too faded; try 100

    font = pygame.font.SysFont('Sans', 20)
    font.set_bold(True)
    
    text1 = font.render("Artist: "+artist, True, (255, 0, 0))
    
    screen.fill((0,0,0)) 
    screen.blit(img, (0,0))      
    screen.blit(text1, (0,0))

    font = pygame.font.SysFont('Sans', 16)
 
    text2 = get_artist_info(artist)
    text2 = wrapper.fill(text2)
    lines = text2.split('\n')
    
    z = 30
    for line in lines:
        text = font.render(line, True, (255, 0, 0))
	screen.blit(text, (0,z))
	z+=20

    pygame.display.flip()

    os.remove("test1.bmp") 

def show_artist():
    img.set_alpha(75) #0 - 100 the lower the number the more faded 

    font = pygame.font.SysFont('Sans', 30)
    font.set_bold(True)
    
    text1 = font.render("Artist: "+artist, True, (255, 0, 0))
    
    screen.fill((0,0,0)) 
    screen.blit(img, (0,0))      
    screen.blit(text1, (0,0))

    pygame.display.flip()

    os.remove("test1.bmp") 

if __name__ == '__main__':

    SHOWNEWIMAGE = USEREVENT+1
    artists = session.query(Artist)
    L = artists.count()
    print("Number of artists = {}".format(L))
    
    pygame.time.set_timer(SHOWNEWIMAGE, 20000)

    while 1:

        if pygame.event.get(SHOWNEWIMAGE):
            artist = artists[random.randrange(0,L-1)].name
            N = session.query(Image).join(Artist).filter(and_(Artist.name == artist, Image.status == True)).count()
            image = session.query(Image).join(Artist).filter(and_(Artist.name == artist, Image.status == True))[random.randrange(0,N-1)] 
            display_artist_image(artist, image) 

        sleep(.1)

