from __future__ import division
from __future__ import print_function
#from __future__ import unicode_literals
#from future_builtins import *

import requests
from cStringIO import StringIO
from time import sleep
import platform
import sys
#import json
import pygame
from pygame.locals import USEREVENT
import os
import random
import argparse
import wand.image
import textwrap

parser = argparse.ArgumentParser(description='Command line options ...')
parser.add_argument('image_number', type=int, help="This is the number of images for each id")
args = parser.parse_args()

wrapper = textwrap.TextWrapper(width=100, replace_whitespace=False)  

#instagram
base_url = "https://api.instagram.com/v1/users/{}/media/recent/"
client_id = "8372f43ffb4b4bbbbd054871d6561668"

#https://api.instagram.com/v1/users/search?q=brahmino&access_token=278917377.8372f43.33d3f65330834b9fa6126d30283b660e
#ids = 4616106 Jason Peterson; 17789355 JR; 986542 Tyson Wheatley; 230625139 Nick Schade; 3399664 Zak Shelhamer; 6156112 Scott Rankin; 1607304 Laura Pritchet; janske 24078; 277810 Richard Koci Hernandez; 1918184 Simone Bramante; 197656340 Michael Christoper Brown; 200147864 David Maialetti; 4769265 eelco roos 

#ids = [4616106, 17789355, 986542, 230625139, 3399664, 6156112, 1607304, 24078, 277810, 1918184, 197656340, 200147864, 4769265] 

with open('instagram_ids') as f:
    data = f.read()

ids = list(int(d.split('#')[0]) for d in data.split() if d.split('#')[0])

if platform.system() == 'Windows':
    os.environ['SDL_VIDEODRIVER'] = 'windib'
elif platform.system() == 'Darwin':
    os.putenv('SDL_VIDEODRIVER', 'quartz')
elif platform.machine() == 'armv6l':
    # from https://github.com/adafruit/adafruit-pi-cam/blob/master/cam.py
    os.putenv('SDL_VIDEODRIVER', 'fbcon')
    os.putenv('SDL_FBDEV', '/dev/fb1')
    os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')
    os.putenv('SDL_MOUSEDRV', 'TSLIB')
else:
    os.putenv('SDL_VIDEODRIVER', 'x11')

pygame.init()
pygame.mouse.set_visible(0)
#pygame.mouse.set_cursor(*pygame.cursors.diamond)

w_max, h_max = pygame.display.Info().current_w, pygame.display.Info().current_h
if w_max > 1080:
    w,h = 1080,1080
else:
    w = w_max
    h = h_max

screen = pygame.display.set_mode((w_max,h_max))
screen.fill((0,0,0))

font = pygame.font.SysFont('Sans', 50)

text = font.render("Instagram", True, (255, 0, 0))

screen.blit(text, (0,0)) 
pygame.display.flip()

def get_photos(ids=None, num=args.image_number):

    images = []
    d = divmod(num, 20)
    n = d[0] + 1 if d[1] else d[0]
    payload = {'client_id':client_id}

    for _id in ids:
        max_id = None #need this for payload line which references max_id
        for i in range(n):
            payload = {'client_id':client_id, 'max_id':max_id} if i else {'client_id':client_id}

            try:
                r = requests.get(base_url.format(_id), params=payload)
                z = r.json()['data'] 
                zz = r.json()['pagination']
                max_id = zz['next_max_id'] #"108...."
                print(max_id)
            except Exception as e:
                print("Exception in get_photos - request: {} related to id: {} ".format(e, _id))
            else:
                for d in z: 
                    try:
                        if d['type']=='image': #note they have a caption and the caption has text
                            dd = {}
                            dd['url'] = d['images']['standard_resolution']['url']
                            dd['url'] = dd['url'].replace('s640x640', 's1080x1080')
                            dd['text'] = d['caption']['text']
                            dd['photographer'] = d['caption']['from']['full_name']
                    except Exception as e:
                        print("Exception in get_photos - adding indiviual photo {} related to id: {} ".format(e, _id))
                    else:
                        images.append(dd)

    return images

def display_image(image):

    try:
        response = requests.get(image['url'])
    except Exception as detail:
        print( "response = requests.get(url) generated exception:", detail)
        print("changed image status to False")
        img = wand.image.Image(filename = "test.bmp")
    else:

        try:
            img = wand.image.Image(file=StringIO(response.content))
        except Exception as detail:
            img = wand.image.Image(filename = "test.bmp")
            print ("img = wand.image.Image(file=StringIO(response.content)) generated exception:", detail)

    # I don't think you want to resize these instagram images but just present them at whatever
    # resolution they happen to be at -- hopefully 1080 x 1080 or at least 1080 x something
    #size = str(w)+'x'+str(h)+'^'
    #img.transform(resize = size)

    img = img.convert('bmp')
    f = StringIO()
    img.save(f)
    f.seek(0)
    img = pygame.image.load(f, 'bmp').convert()
    img_rect = img.get_rect()
    center = ((w_max - img_rect.width)/2, 0)
    f.close()
    img.set_alpha(75) # the lower the number the more faded 

    font = pygame.font.SysFont('Sans', 32)
    font.set_bold(True)

    text = font.render("Photographer: "+image.get('photographer', 'No photographer'), True, (255, 0, 0))

    screen.fill((0,0,0)) 
    #screen.blit(img, (0,0))      
    screen.blit(img, center)      
    screen.blit(text, (0,0))

    txt = image.get('text', 'No title')
    txt = wrapper.fill(txt)
    lines = txt.split('\n')
    font = pygame.font.SysFont('Sans', 24)
    z = 36
    for line in lines:
        try:
            text = font.render(line, True, (255, 0, 0))
        except UnicodeError as e:
            print("UnicodeError in text lines: ", e)
        else:
            screen.blit(text, (0,z))
            z+=24

    pygame.display.flip()

    sleep(10)
    screen.fill((0,0,0)) 
    img.set_alpha(255)
    screen.blit(img, (0,0))      
    pygame.display.flip()

def display_image_and_info(image):

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

    size = str(w)+'x'+str(h)+'^'
    img.transform(resize = size)
    img = img.convert('bmp')
    f = StringIO()
    img.save(f)
    f.seek(0)
    img = pygame.image.load(f, 'bmp').convert()
    img_rect = img.get_rect()
    center = ((w_max - img_rect.width)/2, 0)
    f.close()
    
    img.set_alpha(75) # the lower the number the more faded - 75 seems too faded; try 100

    font = pygame.font.SysFont('Sans', 28)
    font.set_bold(True)

    text = font.render("Photographer: "+image['photographer'], True, (255, 0, 0))

    screen.fill((0,0,0)) 
    #screen.blit(img, (0,0))      
    screen.blit(img, center)      
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

    pygame.display.flip()

if __name__ == '__main__':

    SHOWNEWIMAGE = USEREVENT+1
    images = get_photos(ids)
    L = len(images)
    print("Number of images = {}".format(L))
    pygame.time.set_timer(SHOWNEWIMAGE, 20000)
    pause = False
    pygame.event.post(pygame.event.Event(SHOWNEWIMAGE))
    while 1:

        event = pygame.event.poll()

        if event.type == pygame.NOEVENT:
            pass
        
        elif event.type == SHOWNEWIMAGE and not pause:
            image = images[random.randrange(0,L-1)]
            display_image(image)
        
        elif event.type == pygame.QUIT:
            sys.exit()
                
        elif event.type == pygame.MOUSEBUTTONDOWN: #=5 - MOUSEMOTION ==4
            pause = not pause
            #pygame.event.clear()  #trying not to catch stray mousedown events since a little unclear how touch screen generates them
            if pause:
                display_image_and_info(image)
            else:
                pygame.time.set_timer(SHOWNEWIMAGE, 0)
                pygame.time.set_timer(SHOWNEWIMAGE, 20000)
                display_image(image)

        sleep(.1)
