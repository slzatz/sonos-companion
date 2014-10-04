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

wrapper = textwrap.TextWrapper(width=72, replace_whitespace=False)  

#instagram
base_url = "https://api.instagram.com/v1/users/{}/media/recent/"
client_id = "8372f43ffb4b4bbbbd054871d6561668"
ids = [4616106, 17789355, 986542, 230625139]

if platform.system() == 'Windows':
    os.environ['SDL_VIDEODRIVER'] = 'windib'
elif platform.system() == 'Darwin':
    os.putenv('SDL_VIDEODRIVER', 'quartz')
elif platform.machine() == 'armv6l':
    # from https://github.com/adafruit/adafruit-pi-cam/blob/master/cam.py
    os.putenv('SDL_VIDEODRIVER', 'fbcon')
    os.putenv('SDL_FBDEV', '/dev/fb1')
else:
    os.putenv('SDL_VIDEODRIVER', 'x11')

pygame.init()
#pygame.mouse.set_visible(0)
pygame.mouse.set_cursor(*pygame.cursors.diamond)

DISPLAY = (640,640)

screen = pygame.display.set_mode(DISPLAY)
screen.fill((0,0,0))

font = pygame.font.SysFont('Sans', 50)

text = font.render("Instagram", True, (255, 0, 0))

screen.blit(text, (0,0)) 
pygame.display.flip()

def get_photos(ids=None):
    
    payload = {'client_id':client_id}
    images = []
    for _id in ids:
        try:
            r = requests.get(base_url.format(_id), params=payload)
            z = r.json()['data'] 
        except Exception as e:
            print("Exception in get_photos - request: {} related to id: {} ".format(e, _id))
        else:
            for d in z: 
                try:
                    if d['type']=='image': #note they have a caption and the caption has text
                        dd = {}
                        dd['url'] = d['images']['standard_resolution']['url']
                        dd['text'] = d['caption']['text']
                        dd['photographer'] = d['caption']['from']['full_name']
                except Exception as e:
                    print("Exception in get_photos - adding indiviual photo {} related to id: {} ".format(e, _id))
                else:
                    images.append(dd)

    return images

def display_image(image):

    #image = session.query(Image).join(Artist).filter(Artist.name == artist)[i] #.all()
    try:
        response = requests.get(image['url'])
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

    size = str(DISPLAY[0])+'x'+str(DISPLAY[1])+'^'
    img.transform(resize = size)
    img = img.convert('bmp')
    img.save(filename = "test1.bmp")
    img = pygame.image.load("test1.bmp").convert()
    
    img.set_alpha(75) # the lower the number the more faded - 75 seems too faded; try 100

    font = pygame.font.SysFont('Sans', 28)
    font.set_bold(True)

    text = font.render("Photographer: "+image['photographer'], True, (255, 0, 0))

    screen.fill((0,0,0)) 
    screen.blit(img, (0,0))      
    screen.blit(text, (0,0))
    
    txt = image.get('text', 'No title')
    txt = wrapper.fill(txt)
    lines = txt.split('\n')
    font = pygame.font.SysFont('Sans', 16)
    z = 36
    for line in lines:
        try:
            text = font.render(line, True, (255, 0, 0))
        except UnicodeError as e:
            print("UnicodeError in text lines: ", e)
        else:
            screen.blit(text, (0,z))
            z+=24


    #text = font.render(image.get('text', 'No title'), True, (255, 0, 0))
    #screen.blit(text, (0,40))

    pygame.display.flip()

    sleep(3)
    screen.fill((0,0,0)) 
    img.set_alpha(255)
    screen.blit(img, (0,0))      
    pygame.display.flip()
    os.remove("test1.bmp") 

if __name__ == '__main__':

    SHOWNEWIMAGE = USEREVENT+1
    images = get_photos(ids)
    L = len(images)
    print("Number of images = {}".format(L))
    pygame.time.set_timer(SHOWNEWIMAGE, 20000)
    pause = False
    while 1:

        event = pygame.event.poll()

        if event.type == pygame.NOEVENT:
            pass
        
        elif event.type == SHOWNEWIMAGE and not pause:
            image = images[random.randrange(0,L-1)]
            display_image(image)
        
        #elif event.type == pygame.QUIT:
         #   sys.exit()
                
        elif event.type == pygame.MOUSEBUTTONDOWN: #=5 - MOUSEMOTION ==4
            pause = not pause
            #pygame.event.clear()  #trying not to catch stray mousedown events since a little unclear how touch screen generates them

            font = pygame.font.SysFont('Sans', 14)
            zzz = pygame.Surface((640,20)) 
            zzz.fill((0,0,0))
            text = font.render("Pause" if pause else "Play", True, (255, 0, 0))
            screen.blit(zzz, (0,620))                 
            screen.blit(text, (0,620)) 
            pygame.display.flip()    

        sleep(.1)
