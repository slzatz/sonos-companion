from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future_builtins import *

import requests
import csv
#import gmail
from cStringIO import StringIO
import time
from time import sleep
import platform
import sys
import time
import json
import pygame
from pygame.locals import USEREVENT
import os
import random
import wand.image

from artist_images_db import *
 
if platform.system() == 'Windows':
    os.environ['SDL_VIDEODRIVER'] = 'windib'
elif platform.machine() == 'armv6l':
    # from https://github.com/adafruit/adafruit-pi-cam/blob/master/cam.py
    os.putenv('SDL_VIDEODRIVER', 'fbcon')
    os.putenv('SDL_FBDEV', '/dev/fb1')
else:
    os.putenv('SDL_VIDEODRIVER', 'x11')

try:
  with open('artists.json', 'r') as f:
      artists = json.load(f)
except IOError:
      artists = {}

pygame.init()
pygame.mouse.set_visible(0)

DISPLAY = (640,480)

screen = pygame.display.set_mode(DISPLAY)
screen.fill((0,0,0))

font = pygame.font.SysFont('Sans', 50)

text = font.render("Sales Force", True, (255, 0, 0))

screen.blit(text, (0,0)) 
pygame.display.flip()

def display_artist_image(artist,i):

    #url = artists[artist][i]['link']
    image = session.query(Image).join(Artist).filter(Artist.name == artist)[i] #.all()
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
    #img.set_alpha(100) # the lower the number the more faded - 75 seems too faded; now not fading for display_images
    
    screen.fill((0,0,0)) 
    screen.blit(img, (0,0))      


    pygame.display.flip()
    
    os.remove("test1.bmp") 



def update_display(f):
    screen.fill((0,0,0))
    text = font.render('$'+'{:,}'.format(int(f)), True, (255,0,0)) 
    screen.blit(text, (20,20))
    pygame.display.flip()

if __name__ == '__main__':

    SHOWNEWIMAGE = USEREVENT+1
    #artist_list = artists.keys()
    #artist_list = session.query(Artist).all()
    artist_list = session.query(Artist)
    print (artist_list)
    #print (len(artist_list))
    #L = len(artist_list)
    L = artist_list.count()
    print("Number of artists = {}".format(L))
    #sys.exit()
    
    pygame.time.set_timer(SHOWNEWIMAGE, 10000)

    while 1:

        if pygame.event.get(SHOWNEWIMAGE):
            artist = artist_list[random.randrange(0,L-1)].name
            display_artist_image(artist,random.randrange(0,9)) 

        sleep(.1)

