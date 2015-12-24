import platform
import os
import pygame
import txtlib # may still use this for weather, lyrics, bio
import time
from time import sleep
from decimal import Decimal
import datetime
import random
import requests
import textwrap
#import json
from collections import OrderedDict
import argparse
import sys
from operator import itemgetter
import lxml.html
from cStringIO import StringIO
import wand.image
import config as c
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + sys.path
import soco
from soco import config
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
scrobble_table = dynamodb.Table('scrobble_new')
image_table = dynamodb.Table('artist_images')

s3 = boto3.resource('s3')
object = s3.Object('sonos-scrobble','location')
location = object.get()['Body'].read()

parser = argparse.ArgumentParser(description='Command line options ...')
#default for display is args.display == False (opposite of action); on windows don't need that parameter
parser.add_argument('-d', '--display', action='store_true', help="Use raspberry pi HDMI display and not LCD") 
args = parser.parse_args()

#################instagram
instagram_base_url = c.instagram_base_url
client_id = c.client_id

#https://api.instagram.com/v1/users/search?q=brahmino&access_token=278917377.8372f43.33d3f65330834b9fa6126d30283b660e
#ids = 4616106 Jason Peterson; 17789355 JR; 986542 Tyson Wheatley; 230625139 Nick Schade; 3399664 Zak Shelhamer; 6156112 Scott Rankin; 1607304 Laura Pritchet; janske 24078; 277810 Richard Koci Hernandez; 1918184 Simone Bramante; 197656340 Michael Christoper Brown; 200147864 David Maialetti; 4769265 eelco roos 

with open('instagram_ids') as f:
    data = f.read()

ids = list(int(d.split('#')[0]) for d in data.split() if d.split('#')[0])
#ids = [4616106, 17789355, 986542, 230625139, 3399664, 6156112, 1607304, 24078, 277810, 1918184, 197656340, 200147864, 4769265] 
#willie is 265048195
#################instagram

#google custom search api
from apiclient import discovery

# needed by the google custom search engine module apiclient
import httplib2

#using the musicbrainz db to find the release date and album (if a compilation)
import musicbrainzngs

from amazon_music_db import *
#from sqlalchemy.sql.expression import func

g_api_key = c.google_api_key

musicbrainzngs.set_useragent("Sonos", "0.1", contact="slzatz")

DISPLAY = OrderedDict([('artist','Artist'), ('album','Album'), ('title','Song'), ('date','Date'), ('service','Service'), ('scrobble','Scrobble'), ('uri','Uri')])
MINI_DISPLAY = OrderedDict([('artist','Artist'), ('album','Album'), ('title','Song')])

#last.fm - using for scrobble information, can also be used for artist bios 
scrobbler_base_url = "http://ws.audioscrobbler.com/2.0/"
api_key = c.last_fm_api_key 

wrapper = textwrap.TextWrapper(width=42, replace_whitespace=False) # may be able to be a little longer than 40
wrapper = textwrap.TextWrapper(width=72, replace_whitespace=False)  #instagram

# Environment varialbes for pygame
if platform.machine() == 'armv6l' and not args.display:
    os.putenv('SDL_VIDEODRIVER', 'fbcon')
    os.putenv('SDL_FBDEV', '/dev/fb1')
    os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')
    os.putenv('SDL_MOUSEDRV', 'TSLIB')
elif platform.system() == 'Windows':
    os.environ['SDL_VIDEODRIVER'] = 'windib'
elif platform.system() == "Linux":
    os.environ['SDL_VIDEODRIVER'] = 'x11' #note: this works if you launch x (startx) and run terminal requires keyboard/mouse
    os.environ['SDL_VIDEO_CENTERED'] = '1'
else:
    sys.exit("Currently unsupported hardware/OS")

# Should be (6,0) if pygame inits correctly
r = pygame.init()
print "pygame init",r

if platform.machine() == 'armv6l': # and not args.display:
    pygame.mouse.set_visible(False)

if platform.system() == 'Windows':
    w,h = 1000,700
else:
    w, h = pygame.display.Info().current_w, pygame.display.Info().current_h

screen = pygame.display.set_mode((w, h))
screen.fill((0,0,0))

text = txtlib.Text((w, h), 'freesans', font_size=30)
text.text = "Sonos-Companion TFT Edition"
text.update()
screen.blit(text.area, (0,0))
pygame.display.flip()

# Early use of Soco had some funny things happening if the cache was on -- no idea if this is still necessary but solved problem at the time
config.CACHE_ENABLED = False

print "\n"

print "program running ..."

def display_artist_info(artist):

    artist_image_list = get_images2(artist)
    r = random.randint(0,9)
    url = artist_image_list[r]

    try:
        response = requests.get(url)

    except Exception as e:
        print "response = requests.get(url) generated exception: ", e
        img = None
        r = image_table.update_item(
            Key={'artist':artist, 'link':url},
            UpdateExpression="set ok = :o",
            ExpressionAttributeValues={':o':False},
            ReturnValues="UPDATED_NEW")
        print "Set ok to False",r
    else:
        try:
            img = wand.image.Image(file=StringIO(response.content))
        except Exception as e:
            print "img = wand.image.Image(file=StringIO(response.content)) generated exception from url:", url, "Exception:", e
            img = None
            r = image_table.update_item(
                Key={'artist':artist, 'link':url},
                UpdateExpression="set ok = :o",
                ExpressionAttributeValues={':o':False},
                ReturnValues="UPDATED_NEW")
            print "Set ok to False",r

    if img is None:
        return
    
    img.transform(resize = "{}x{}".format(w,h))
    img = img.convert('bmp')
    f = StringIO()
    img.save(f)
    f.seek(0)
    img = pygame.image.load(f, 'bmp').convert()
    f.close()
    img_rect = img.get_rect()
    center = ((w-img_rect.width)/2, 0)
    #f.close() moved on 12072015
    img.set_alpha(75) # the lower the number the more faded - 75 seems too faded; try 100

    font = pygame.font.SysFont('Sans', 28)
    font.set_bold(True)
    
    screen.fill((0,0,0))
    screen.blit(img, center)      

    text = font.render(u"{}".format(artist), True, (255, 0, 0))
    screen.blit(text, (5,5))

    bio = get_artist_info(artist, autocorrect=0)
    bio = textwrap.wrap(bio, 70)
    font = pygame.font.SysFont('Sans', 18)
    font.set_bold(False)
    n=40
    for line in bio:
        text = font.render(u"{}".format(line), True, (255, 0, 0))
        screen.blit(text, (5,n))
        n+=18

    pygame.display.flip()

def display_song_info(artist, i):

    url = artist_image_list[i]

    try:
        response = requests.get(url)
    except Exception as e:
        print "response = requests.get(url) generated exception: ", e
        img = None
        r = image_table.update_item(
            Key={'artist':artist,'link':url},
            UpdateExpression="set ok = :o",
            ExpressionAttributeValues={':o':False},
            ReturnValues="UPDATED_NEW")
        print "Set ok to False",r
    else:     
        try:
            img = wand.image.Image(file=StringIO(response.content))
        except Exception as e:
            print "img = wand.image.Image(file=StringIO(response.content)) generated exception from url:", url, "Exception:", e
            img = None
            r = image_table.update_item(
                Key={'artist':artist,'link':url},
                UpdateExpression="set ok = :o",
                ExpressionAttributeValues={':o':False},
                ReturnValues="UPDATED_NEW")
            print "Set ok to False",r

    if img is None:
         return

    img.transform(resize = "{}x{}".format(w,h))
    img = img.convert('bmp')
    f = StringIO()
    img.save(f)
    f.seek(0)
    img = pygame.image.load(f, 'bmp').convert()
    f.close()
    img_rect = img.get_rect()
    center = ((w-img_rect.width)/2, 0)
    #f.close() moved on 12072015
    img.set_alpha(75) # the lower the number the more faded - 75 seems too faded; try 100

    font = pygame.font.SysFont('Sans', 16)
    font.set_bold(True)
    
    screen.fill((0,0,0))
    screen.blit(img, center)      
    n=0
    for s in track_strings:
        text = font.render(u"{}".format(s), True, (255, 0, 0))
        screen.blit(text, (5,n))
        n+=18
    pygame.display.flip()

def display_song_info2(artist, i):

    url = artist_image_list[i]

    try:
        response = requests.get(url)
    except Exception as e:
        print "response = requests.get(url) generated exception: ", e
        img = None
        r = image_table.update_item(
            Key={'artist':artist, 'link':url},
            UpdateExpression="set ok = :o",
            ExpressionAttributeValues={':o':False},
            ReturnValues="UPDATED_NEW")
        print "Set ok to False",r
    else:
        try:
            img = wand.image.Image(file=StringIO(response.content))
        except Exception as e:
            print "img = wand.image.Image(file=StringIO(response.content)) generated exception from url:", url, "Exception:", e
            img = None
            r = image_table.update_item(
                Key={'artist':artist, 'link':url},
                UpdateExpression="set ok = :o",
                ExpressionAttributeValues={':o':False},
                ReturnValues="UPDATED_NEW")
            print "Set ok to False",r

    if img is None:
        return

    try:
        img.transform(resize = "{}x{}".format(w,h))
        img = img.convert('bmp')
        f = StringIO()
        img.save(f)
        f.seek(0)
        img = pygame.image.load(f, 'bmp').convert()
        f.close()
        img_rect = img.get_rect()
        center = ((w-img_rect.width)/2, 0)
        #f.close() # moved on 12072015
        
        screen.fill((0,0,0)) 
        screen.blit(img, center)      

        pygame.display.flip()
        
    except Exception as e:
        print "Problem with img: ", e

def get_scrobble_info(artist, track, username='slzatz', autocorrect=True):
    
    payload = {'method':'track.getinfo', 'artist':artist, 'track':track, 'autocorrect':autocorrect, 'format':'json', 'api_key':api_key, 'username':username}
    
    try:
        r = requests.get(scrobbler_base_url, params=payload)
        
        z = r.json()['track']['userplaycount']
        return z # will need to be converted to integer when sent to SQS
    except Exception as e:
        print "Exception in get_scrobble_info: ", e
        return '-1' # will need to be converted to integer when sent to SQS

def get_artist_info(artist, autocorrect=0):
    
    payload = {'method':'artist.getinfo', 'artist':artist, 'autocorrect':autocorrect, 'format':'json', 'api_key':api_key}
    
    try:
        r = requests.get(scrobbler_base_url, params=payload)
        bio = r.json()['artist']['bio']['summary']
        text = lxml.html.fromstring(bio).text_content()
        idx = text.find("Read more")
        if idx != -1:
            text = text[:idx]
        
        return text
        
    except:
        return ''

def get_release_date(artist, album, title):
    print "in get release date"
    t = "artist = {}; album = {} [used in search], title = {} [in get_release_date]".format(artist, album, title)
    print t.encode('ascii', 'ignore')

    # commented this out because I think in most circumstances where there is a legit album, there is an accompanying date
    # (like for a ripped CD, a Rhapsody song, Pandora
    # In addition, this allows you to display the first album where the song appeared 
    try:
        result = musicbrainzngs.search_releases(artist=artist, release=album, limit=20, strict=True)
    except:
        return "No date exception (search_releases)"
    
    release_list = result['release-list'] # can be missing
    
    if 'release-list' in result:
        release_list = result['release-list'] # can be missing
        dates = [d['date'][0:4] for d in release_list if 'date' in d and int(d['ext:score']) > 90] 
    
        if dates:
            dates.sort()
            return "{}".format(dates[0])  
    print "Leaving get release date"
    return ''
       
    ## Generally if there was no date provided it's because there is also a bogus album (because it's a collection
    ## and so decided to comment out the above.  We'll see how that works over time.

def get_recording_date(artist, album, title):

    t = "artist = {}; album = {} [not used in search], title = {} [in get_recording_date]".format(artist, album, title)
    print t.encode('ascii', 'ignore')
    
    try:
        result = musicbrainzngs.search_recordings(artist=artist, recording=title, limit=40, offset=None, strict=False)
    except:
        return "No date exception (search_recordings)"
    
    recording_list = result.get('recording-list')
    
    if recording_list is None:
        return "No date (search of musicbrainzngs did not produce a recording_list)"
    
    dates = []
    for d in recording_list:
        if int(d['ext:score']) > 98 and 'release-list' in d:
            rel_dict = d['release-list'][0] # it's a list but seems to have one element and that's a dictionary
            date = rel_dict.get('date', '9999')[0:4]
            title = rel_dict.get('title','No title')

            if rel_dict.get('artist-credit-phrase') == 'Various Artists':  #possibly could also use status:promotion
                dates.append((date,title,'z'))
            else:
                dates.append((date,title,'a'))
                
    if dates:
        dates.sort(key=itemgetter(0,2)) # idea is to put albums by the artist ahead of albums by various artists
        return u"{} - {}".format(dates[0][0], dates[0][1])   
    else:
        return '' 
    
def display_action(text):
    
    font = pygame.font.SysFont('Sans', 14)
    zzz = pygame.Surface((w,20)) 
    zzz.fill((0,0,0))
    text = font.render(text, True, (255, 0, 0))
    screen.blit(zzz, (0,h-16))                 
    screen.blit(text, (0,h-16)) 
    pygame.display.flip()

def get_images2(name):
    '''
    10 is the max you can bring back on any individual search
    I think you  separate the orterms by a space
    orTerms='picture photo image'
    imgSize = 'large'
    start=1 or 11
    using link, height, width
    '''
    print "getting images: {}".format(time.time())
    try:
        result = image_table.query(KeyConditionExpression=Key('artist').eq(name))
        items = result['Items']
        images = [x['link'] for x in items if x.get('ok', True)]
    except Exception as e:
        print "Couldn't find artist", name

    print "got images: {}".format(time.time())

    if not images: #this should only be true for new artists but you never know
        print "**************Google Custom Search Engine Request for "+name+"**************"
        http = httplib2.Http()
        service = discovery.build('customsearch', 'v1',  developerKey=g_api_key, http=http)
        z = service.cse().list(q=name, searchType='image', imgType='face', imgSize='xlarge', num=10, cx='007924195092800608279:0o2y8a3v-kw').execute() 

        for i in z['items']:
            
            data = {
                'artist':name,
                'link':i['link'],
                'width':i['image']['width'],
                'height':i['image']['height']}

            data = {k:v for k,v in data.items() if v} 
            images.append(i['link'])

            try:
                image_table.put_item(Item=data)
            except Exception as e:
                print("Exception trying to write dynamodb artist_image table:", e)
                
    # for image in artist.images: what if not OK
    print "images = ", images
    return images 
    
def get_url(artist, title):

    if artist is None or title is None:
        return None

    payload = {'func': 'getSong', 'artist': artist, 'song': title, 'fmt': 'realjson'}
    
    try:
         r = requests.get("http://lyrics.wikia.com/api.php", params=payload)
    except:
        url = None
         
    else:        
        q = r.json()
        
        url = q['url'] if 'url' in q else None
        
        if url and url.find("action=edit") != -1: 
            url = None 
            
    if url is not None:
        return url
            
    try:
        z = musicbrainzngs.search_recordings(artist=artist, recording=title, limit=5, offset=None, strict=False)
    except:
        return None
        
    for d in z['recording-list']:

         if int(d['ext:score'])==100:
             new_artist = d['artist-credit-phrase']
             new_title = d['title']
    
    payload = {'func': 'getSong', 'artist': new_artist, 'song': new_title, 'fmt': 'realjson'}
    
    try:
         r = requests.get("http://lyrics.wikia.com/api.php", params=payload)
    except:
        return None
                
    q = r.json()
        
    url = q['url'] if 'url' in q else None
        
    if url and url.find("action=edit") != -1: 
        url = None 
    else:
        print "got song lyrics by using musicbrainz db to figure out correct artist and title"
        
    return url

def get_photos(ids=None):
    
    payload = {'client_id':client_id}
    images = []
    for _id in ids:
        try:
            r = requests.get(instagram_base_url.format(_id), params=payload)
            z = r.json()['data'] 
        except Exception as e:
            print "Exception in get_photos - request: {} related to id: {} ".format(e, _id)
        else:
            for d in z: 
                try:
                    dd = {}
                    if d['type']=='image': #note they have a caption and the caption has text
                        dd['url'] = d['images']['standard_resolution']['url']
                        dd['text'] = d['caption']['text']
                        dd['photographer'] = d['caption']['from']['full_name']
                except Exception as e:
                    print "Exception in get_photos - adding indiviual photo {} related to id: {} ".format(e, _id)
                else:
                    if dd:
                        images.append(dd)

    return images

def display_image(image):

    try:
        response = requests.get(image['url'])
    except Exception as detail:
        print "response = requests.get(url) generated exception:", detail
        print "changed image status to False"
        img = wand.image.Image(filename = "test.bmp")
    else:

        try:
            img = wand.image.Image(file=StringIO(response.content))
        except Exception as detail:
            img = wand.image.Image(filename = "test.bmp")
            print ("img = wand.image.Image(file=StringIO(response.content)) generated exception:", detail)

    size = "{}x{}".format(w,h)
    img.transform(resize = size)
    img = img.convert('bmp')
    f = StringIO()
    img.save(f)
    f.seek(0)
    img = pygame.image.load(f).convert()
    f.close()
    img_rect = img.get_rect()
    center = ((w-img_rect.width)/2, 0)
    #f.close() 12072015
    img.set_alpha(75) # the lower the number the more faded - 75 seems too faded; try 100

    font = pygame.font.SysFont('Sans', 28)
    font.set_bold(True)

    text = font.render("Photographer: "+image.get('photographer', 'No photographer'), True, (255, 0, 0))

    screen.fill((0,0,0)) 
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
            print "UnicodeError in text lines: ", e
        else:
            screen.blit(text, (0,z))
            z+=24

    pygame.display.flip()

    sleep(3)
    screen.fill((0,0,0)) 
    img.set_alpha(255)
    screen.blit(img, center)      
    pygame.display.flip()

def display_image_and_info(image):

    try:
        response = requests.get(image['url'])
    except Exception as detail:
        print "response = requests.get(url) generated exception:", detail
        image.status = False
        print "changed image status to False"
        session.commit()
        img = wand.image.Image(filename = "test.bmp")
    else:

        try:
            img = wand.image.Image(file=StringIO(response.content))
        except Exception as detail:
            img = wand.image.Image(filename = "test.bmp")
            print ("img = wand.image.Image(file=StringIO(response.content)) generated exception:", detail)

    size = "{}x{}".format(w,h)
    img.transform(resize = size)
    img = img.convert('bmp')
    f = StringIO()
    img.save(f)
    f.seek(0)
    img = pygame.image.load(f, 'bmp').convert()
    f.close()
    img_rect = img.get_rect()
    center = ((w-img_rect.width)/2, 0)
    #f.close() 12072015
    img.set_alpha(75) # the lower the number the more faded - 75 seems too faded; try 100

    font = pygame.font.SysFont('Sans', 28)
    font.set_bold(True)

    text = font.render("Photographer: "+image['photographer'], True, (255, 0, 0))

    screen.fill((0,0,0)) 
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
            print "UnicodeError in text lines: ", e
        else:
            screen.blit(text, (0,z))
            z+=24

    pygame.display.flip()

if __name__ == '__main__':
    
    images = get_photos(ids)
    L = len(images)
    print "Number of images = {}".format(L)
    image = images[random.randrange(0,L-1)]
    display_image(image)
    t0 = t1 = t2 = t3 = time.time()
    prev_title = title = "No title"  #this is None so if the song title is the empty string, it's not equal
    new_song = False
    image_num = 0
    artist = None
    track_strings = []
    track = {}

    while 1:
       # pygame.event.get() or .poll() -- necessary to keep pygame window from going to sleep
        event = pygame.event.poll()
        
        if event.type == pygame.NOEVENT:
            pass # want pass and not continue because want this to fall through to the non pygame event stuff
            
        elif event.type == pygame.QUIT:
            sys.exit(0)
        
        # No need to ping dynamodb and incur costs if no one listening

        cur_time = time.time()
        ts = datetime.datetime.fromtimestamp(cur_time).strftime('%Y-%m-%d %H:%M:%S')
        now = datetime.datetime.now()
        hour = now.hour
        isoweekday = now.isoweekday()
        if hour < 5 or (hour > 8 and hour < 16) and isoweekday in range(1,6):
            print "Not checking for tracks because of time: day of week: {} and time: {}".format(isoweekday,hour)

            # Below is code to flip instagram pictures when tracks not playing
            ##################################################################
            if cur_time - t1 > 30:
                image = images[random.randrange(0,L-1)]
                display_image(image)
                t1 = time.time()
            ##################################################################

            sleep(5)
            continue

        try:
            result = scrobble_table.query(KeyConditionExpression=Key('location').eq(location), ScanIndexForward=False, Limit=1) #by default the sort order is ascending
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print "Experienced exception during while loop: ", sys.exc_info()[0], e
            sleep(5)
            continue

        if result['Count']:
            current_track = result['Items'][0]
            if current_track['ts'] > Decimal(time.time())-300:
                title = current_track.get('title', 'No title')
            else:
                print "{} There were songs but nothing new".format(ts)
                ##################################################################
                if cur_time - t1 > 30:
                    print "Changing images"
                    image = images[random.randrange(0,L-1)]
                    display_image(image)
                    t1 = time.time()
                ##################################################################
                sleep(5)
                continue
        else:
            print "{} There were no songs at all".format(ts)
            ##################################################################
            if cur_time - t1 > 30:
                print "Changing images"
                image = images[random.randrange(0,L-1)]
                display_image(image)
                t1 = time.time()
            ##################################################################
            sleep(5)
            continue

        # checking every two seconds if the track has changed - could do it as a subscription too
        if cur_time - t0 > 2:
            
            ts = datetime.datetime.fromtimestamp(cur_time).strftime('%Y-%m-%d %H:%M:%S')
            print str(ts), "checking to see if track title '{}' has changed".format(title)

            if prev_title != title: 
                
                track = dict(current_track)

                # there will be no date if from one of our compilations
                if not 'date' in track and track.get('artist') and track.get('title') and track.get('album'):
                    if track['album'].find('(c)') == -1:
                        track['date'] = get_release_date(track['artist'], track['album'], track['title'])
                    else:
                        track['date'] = get_recording_date(track['artist'], track['album'], track['title'])
                         
                else:
                    track['date'] = ''
                
                if not 'scrobble' in track and track.get('artist') and track.get('title'):
                    track['scrobble'] = get_scrobble_info(track['artist'], track['title'])
                else:
                    track['scrobble'] = '-100'

                track_strings = [DISPLAY[x]+': '+track[x].encode('ascii', 'ignore') for x in DISPLAY if track.get(x)] # str is for scrobble integer 
            
                #if there is no artist (for example when Sonos isn't playing anything or for some radio) then show images of sunsets  ;-)
                artist_image_list = get_images2(track['artist'] if track.get('artist') else "sunsets")
                num_images = len(artist_image_list)
                print "I have found", num_images, "images for ", track.get('artist', '') 
                print "displaying initial image of", track.get('artist', '')
                display_song_info(track['artist'], 0)
                t3 = cur_time #time.time()
                                  
                prev_title = title
                image_num = 0
                new_song = True

            elif not new_song:
                # show the next track_string if not the image and text from a new song
                    
                if not track_strings:
                    track_strings.extend([DISPLAY[x]+': '+track[x].encode('ascii', 'ignore') for x in DISPLAY if track.get(x)])
                         
                line = track_strings.pop(0) if track_strings else "No info found"

                font = pygame.font.SysFont('Sans', 14)
                font.set_bold(True)
                
                text = font.render(line, True, (255,0,0))
                zzz = pygame.Surface((w,20)) 
                zzz.fill((0,0,0))
                 
                screen.blit(zzz, (0,h-16))
                screen.blit(text, (0,h-16))
                pygame.display.flip()
                
            t0 = time.time()

        if cur_time - t3 > 10:

            new_song = False
            
            image_num = image_num+1 if image_num < num_images-1 else 0
            try:
                print time.time(),"displaying image", image_num, "of ", track['artist']
                display_song_info2(track['artist'], image_num) 
            except Exception as e:
               print "Exception:", e
            
            t3 = time.time()
        
        sleep(0.5)

