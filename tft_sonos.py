import soco
from soco import config

import platform
import os

import pygame
import txtlib # may still use this for weather, lyrics, bio

import time

from time import sleep
import datetime
import random
import xml.etree.ElementTree as ET
import requests
import textwrap
import json
from collections import OrderedDict

#from PIL import Image
from StringIO import StringIO

import wand.image

# google custom search api
from apiclient import discovery

# needed by the google custom search engine module apiclient
import httplib2

#using the musicbrainz db to find the release date and album (if a compilation)
import musicbrainzngs

musicbrainzngs.set_useragent("Sonos", "0.1", contact="slzatz")

try:
  with open('artists.json', 'r') as f:
      artists = json.load(f)
except IOError:
      artists = {}


DISPLAY = OrderedDict([('artist','Artist'), ('album','Album'), ('title','Song'), ('date','Release date')])
# need to add ('service', 'Service) to ordered dict

#last.fm - right now not using this at all - suspect it is providing bios
base_url = "http://ws.audioscrobbler.com/2.0/"
api_key = "1c55c0a239072889fa7c11df73ecd566"

wrapper = textwrap.TextWrapper(width=50, replace_whitespace=False) # may be able to be a little longer than 40

prev_track = ""

if platform.system() == 'Windows':
    os.environ['SDL_VIDEODRIVER'] = 'windib'
else:
    # from https://github.com/adafruit/adafruit-pi-cam/blob/master/cam.py
    os.putenv('SDL_VIDEODRIVER', 'fbcon')
    os.putenv('SDL_FBDEV', '/dev/fb1')

pygame.init()
pygame.mouse.set_visible(0)

screen = pygame.display.set_mode((320, 240))
screen.fill((0,0,0))

#img = wand.image.Image(filename = "test.bmp") #########
#img.transform(resize = '320x240^')#############
#img.save(filename = "test.bmp")
img = pygame.image.load("test.bmp").convert() ################

text = txtlib.Text((320, 240), 'freesans')
text.text = "Sonos-Companion TFT Edition"
text.update()
screen.blit(text.area, (0,0))
pygame.display.flip()
sleep(5)

font = pygame.font.SysFont('Sans', 20)
text = font.render("Welcome to Sonos-Companion", True, (255, 0, 0))
img.blit(text, (0,25)) 
screen.blit(img, (0,0))
pygame.display.flip()

config.CACHE_ENABLED = False

speakers = list(soco.discover())

print speakers ################

# appears that the property coordinator of s.group is not getting set properly and so can't use s.group.coordinator[.player_name]

for s in speakers:
    if s:
        #print "speaker: {} - master: {}".format(s.player_name, s.group)  #s.group.coordinator.player_name)
        print s.player_name
           
for s in speakers:
    if s.is_coordinator:
        master = s
        print "\nNOTE: found coordinator and master =",master.player_name
        break
else:
    master = speakers[0]
    print "\nALERT: id not find coordinator so took speaker[0] =",master.player_name

for s in speakers:
    if s != master:
        s.join(master)
    
print "\n"
#for s in speakers:
#if s:  print "speaker: {} - master: {}".format(s.player_name, s.group.coordinator)

print "program running ..."

# backlight colors
#col = (lcd.RED , lcd.YELLOW, lcd.GREEN, lcd.TEAL, lcd.BLUE, lcd.VIOLET, lcd.ON, lcd.OFF)

#colors
colors = {
'red': (0,0,0),
'yellow': (0,0,0),
'green': (0,0,0),
'teal': (0,0,0),
'blue': (0,0,0),
'violet': (0,0,0),
}

stations = [
#('WNYC', 'aac://204.93.192.135:80/wnycfm-tunein.aac'),
('WNYC-FM', 'x-sonosapi-stream:s21606?sid=254&flags=32', 'SA_RINCON65031_'), # this is from favorites
#('WSHU-FM', 'x-rincon-mp3radio://wshu.streamguys.org/wshu-news'),
('WSHU-FM', 'x-sonosapi-stream:s22803?sid=254&flags=32', 'SA_RINCON65031_'), # this is from favorites
('QuickMix', 'pndrradio:52877953807377986', 'SA_RINCON3_slzatz@gmail.com'),
('R.E.M. Radio', 'pndrradio:637630342339192386', 'SA_RINCON3_slzatz@gmail.com'), 
('Nick Drake Radio', 'pndrradio:409866109213435458', 'SA_RINCON3_slzatz@gmail.com'),
('Dar Williams Radio', 'pndrradio:1823409579416053314', 'SA_RINCON3_slzatz@gmail.com'),
('Patty Griffin Radio', 'pndrradio:52876609482614338', 'SA_RINCON3_slzatz@gmail.com'),
('Lucinda Williams Radio', 'pndrradio:360878777387148866', 'SA_RINCON3_slzatz@gmail.com'),
('Neil Young Radio', 'pndrradio:52876154216080962', 'SA_RINCON3_slzatz@gmail.com'),
('Kris Delmhorst Radio', 'pndrradio:610111769614181954', 'SA_RINCON3_slzatz@gmail.com'),
('Counting Crows Radio', 'pndrradio:1727297518525703746', 'SA_RINCON3_slzatz@gmail.com'), 
('Vienna Teng Radio', 'pndrradio:138764603804051010', 'SA_RINCON3_slzatz@gmail.com')]

#globals
mode = 1
station_index = 0

meta_format_pandora = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="OOOX52876609482614338" parentID="0" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

meta_format_radio = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns=
"urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="-1" parentID="-1" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItem.audioBroadcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

def display_song_info(i):

    zz = get_images(track['artist'])
    url = zz[i]['link']

    try:
        response = requests.get(url)
    except Exception as detail:
        print "response = requests.get(url) generated exception:", detail
        
    try:
        img = wand.image.Image(file=StringIO(response.content))
    except Exception as detail:
        img = wand.image.Image(filename = "test.bmp")
        print "img = wand.image.Image(file=StringIO(response.content)) generated exception:", detail

    img.transform(resize = '320x240^')
    img = img.convert('bmp')
    img.save(filename = "test1.bmp")
    img = pygame.image.load("test1.bmp").convert()
    img.set_alpha(100) # the lower the number the more faded - 75 seems too faded; try 100

    font = pygame.font.SysFont('Sans', 16)
    font.set_bold(True)
    
    track['date'] = get_release_date(track['artist'], track['album'], track['title']) # better in both places
    
    text1 = font.render("Artist: "+track.get('artist'), True, (255, 0, 0))
    text2 = font.render("Album: "+track.get('album'), True, (255, 0, 0))
    text3 = font.render("Song: "+track.get('title'), True, (255, 0, 0))
    text4 = font.render("Release date: "+track.get('date'), True, (255, 0, 0))
    
    screen.fill((0,0,0)) ################################################## added this to alpha
    screen.blit(img, (0,0))      
    screen.blit(text1, (0,0))
    screen.blit(text2, (0,18))
    screen.blit(text3, (0,36))
    screen.blit(text4, (0,54))

    pygame.display.flip()
    
    os.remove("test1.bmp")
    #z = time.time()
        
def get_release_date(artist, album, title):
    print "artist = {}; album = {}, title = {} [in get_release_date]".format(artist, album, title)
    try:
        result = musicbrainzngs.search_releases(artist=artist, release=album, limit=20, strict=True)
    except:
        return "No date exception (search_releases)"
    
    #release_list = result['release-list'] # can be missing
    
    if 'release-list' in result:
            release_list = result['release-list'] # can be missing
            dates = [d['date'][0:4] for d in release_list if 'date' in d and int(d['ext:score']) > 90] 
    
            if dates:
                dates.sort()
                return dates[0]  
        
    # above may not work if it's a collection album with a made up name; the below tries to address that 
    try:
        result = musicbrainzngs.search_recordings(artist=artist, recording=title, limit=20, offset=None, strict=False)
    except:
        return "No date exception (search_recordings)"
    
    #recording_list = result['recording-list']
    recording_list = result.get('recording-list')
    
    if recording_list is None:
        return "No date (no recording_list)"
    
    dates = []
    for d in recording_list:
            if 'release-list' in d:
                #dd = [x['date'][0:4]+': '+x['title'] for x in d['release-list'] if 'date' in x and int(d['ext:score']) > 90]
                dd = [x['date'][0:4] for x in d['release-list'] if 'date' in x and int(d['ext:score']) > 90]     
                dates.extend(dd)
            
               #[item for sublist in l for item in sublist] - this should work but not sure it makes sense to modify above which works
            
    if dates:
        dates.sort()
        return dates[0]   
    else:
        return "?" 
    
def play_uri(uri, meta, title):
    try:
        master.play_uri(uri, meta)
    except:
        print "had a problem switching to {}!".format(title)
    else:
        print "switched to {}".format(title)

def play_pause():
    
    state = master.get_current_transport_info()['current_transport_state']
    if state == 'PLAYING':   #'PAUSED_PLAYBACK'
        master.pause()
    else:
        master.play()
        
    #lcd.clear()
    #lcd.backlight(lcd.YELLOW)
    #lcd.message(state)

def cancel():
    
    global mode
    
    mode = 1
    
    

def next():
    master.next()

def previous():
    
    mode = 0
    #lcd.clear()
    #lcd.backlight(lcd.YELLOW)
    #lcd.message(stations[station_index][0])
    
def dec_volume():
    
    volume = master.volume
    
    new_volume = volume - 10
    
    if new_volume > 75:
        new_volume = 75
        print "volume set to over 75 was reset to 75"
                    
    for s in speakers:
        s.volume = new_volume
    

    #lcd.clear()
    #lcd.message("Volume: {}".format(new_volume))
    #lcd.backlight(lcd.YELLOW)
    
def inc_volume():
    
    volume = master.volume
    
    new_volume = volume + 10
    
    if new_volume > 75:
        new_volume = 75
        print "volume set to over 75 was reset to 75"
                    
    for s in speakers:
        s.volume = new_volume
        
    #lcd.clear()
    #lcd.message("Volume: {}".format(new_volume))
    #lcd.backlight(lcd.YELLOW)
    
def scroll_up():
    
    global station_index
    
    station_index+=1
    station_index = station_index if station_index < 12 else 0
    
    #lcd.clear()
    #lcd.backlight(lcd.YELLOW)
    #lcd.message(stations[station_index][0])

def scroll_down():
       
    global station_index
    
    station_index-=1
    station_index = station_index if station_index > -1 else 0
    
    #lcd.clear()
    #lcd.backlight(lcd.YELLOW)
    #lcd.message(stations[station_index][0])
    
def select():
    
    global mode
    
    if mode:
        mode = 0
        sleep(.5)
    else:
        station = stations[station_index]
        uri = station[1]
        
        if uri.startswith("pndrradio"):
            meta = meta_format_pandora.format(title=station[0], service=station[2])
        else:
            uri = uri.replace('&', '&amp;') # need to escape '&' in radio URIs
            meta = meta_format_radio.format(title=station[0], service=station[2])
        
        print "uri=",uri
        print "meta=",meta
        print "\n"
  
        play_uri(uri, meta, station[0]) # station[0] is the title of the station
            
        mode = 1
        sleep(.5)
        
def list_stations():
    z = ""
    for i,s in enumerate(stations):
        print "{:d} - {}".format(i+1,s[0])
        z+= "{:d} - {}<br>".format(i+1,s[0])
        
    return z
    
def get_images(artist):
    '''
    10 is the max you can bring back on any individual search
    I think you  separate the orterms by a space
    orTerms='picture photo image'
    imgSize = 'large'
    start=1 or 11
    using link, height, width
    '''
    
    #if there is no artist (for example when Sonos isn't playing anything) then show images of sunsets  ;-)
    if not artist:
        artist = 'sunsets'

    if artist not in artists: 
        http = httplib2.Http()
        service = discovery.build('customsearch', 'v1',  developerKey='AIzaSyCe7pbOm0sxYXwMWoMJMmWvqBcvaTftRC0', http=http)
        z = service.cse().list(q=artist, searchType='image', imgSize='large', num=10, cx='007924195092800608279:0o2y8a3v-kw').execute() 

        print 'artist=',artist    #################################################
        image_list = []

        for x in z['items']:
            y = {}
            y['image'] = {k:x['image'][k] for k in ['height','width']}
            y['link'] = x['link']
            image_list.append(y)
      
        artists[artist] = image_list

        print "**************Google Custom Search Engine Request for "+artist+"**************"
          
        try:
            with open('artists.json', 'w') as f:
                json.dump(artists, f)
        except IOError:
            print "Could not write 'artists' json file"

    return artists[artist]
    
def display_weather():
    
    hour = datetime.datetime.now().hour
    if hour != g.prev_hour:
        
        r = requests.get("http://api.wunderground.com/api/9862edd5de2d456c/conditions/q/10011.json")
        m1 = r.json()['current_observation']['temperature_string']
        m2 = r.json()['current_observation']['wind_string']
        
        lcd.clear()
        lcd.backlight(lcd.RED)
        lcd.message([m1,m2])
 
        scroller = Scroller(lines = [m1, m2])
        
        g.prev_hour = hour
    
    else:
         
        pass
        #message = scroller.scroll()
        #lcd.clear()
        #lcd.backlight(lcd.RED)
        #lcd.message(message)

#2 = forward: lcd.RIGHT
#4 = volume lower: lcd.DOWN
#8 = volume higher: lcd.UP
#16 = pause: lcd.LEFT
#1 = change mode: lcd.SELECT
#0 = no button

#btns = {
#           1: ( 'select', 'Change Mode',           lcd.YELLOW,  select,         select),
#           2: ( lcd.RIGHT,    'Next',                         lcd.VIOLET,    next),
#           4: ( lcd.DOWN,    'Decrease\nVolume',    lcd.GREEN,    dec_volume, scroll_down),
#           8: ( lcd.UP,       'Increase\nVolume',        lcd.BLUE,       inc_volume,  scroll_up),
#          16: ( lcd.LEFT,    'Play/Pause',                 lcd.RED,        play_pause,  cancel)
#         } 

if __name__ == '__main__':
    
    prev_title = '' # was '0' for some reason
    prev_hour = -1
    
    while 1:

        #b = btns.get(lcd.buttons())
        b = None
        
        pygame.event.get() # necessary to keep pygame window from going to sleep
    
        if  mode and not b:
                        
            state = master.get_current_transport_info()['current_transport_state']
            
            if state != 'PLAYING':
                
                #begin display_weather() ########################################
                hour = datetime.datetime.now().hour
                if hour != prev_hour:

                    # Tuesday :  Showers and thunderstorms. Lows overnight in the low 70s.
                    # Tuesday Night :  Thunderstorms likely. Low 72F. Winds SSW at 5 to 10 mph. Chance of rain 90%.
                    
                    r = requests.get("http://api.wunderground.com/api/9862edd5de2d456c/forecast/q/10011.json")
                    m1 = r.json()['forecast']['txt_forecast']['forecastday'][0]['title'] + ': ' + r.json()['forecast']['txt_forecast']['forecastday'][0]['fcttext']
                    m2 = r.json()['forecast']['txt_forecast']['forecastday'][1]['title'] + ': ' + r.json()['forecast']['txt_forecast']['forecastday'][1]['fcttext']

                    
                    #lcd.clear()
                    #lcd.backlight(lcd.RED)
                    #lcd.message([m1,m2])
                    
                    text = txtlib.Text((320, 240), 'freesans')
                    text.text = wrapper.fill(m1)+'\n'+wrapper.fill(m2)
                    text.update()
                    screen.blit(text.area, (0, 0))
                    pygame.display.flip() # Update the full display Surface to the screen
                   
                    #weather_scroller.setLines([m1, m2])
                    
                    prev_hour = hour
                    prev_title = ''
                
               #end display_weather() ###################################################
                
            else:
                #print "state = PLAYING"
                #begin display_song_info() ###########################################
                #DISPLAY = OrderedDict([('artist','Artist'), ('album','Album'), ('title','Song'), ('date','Release date')])
                track = master.get_current_track_info()
                #track['date'] = get_release_date(track['artist'], track['album'], track['title']) # not best here since fires every time
                
                title = track['title']
                
                if prev_title != title:
                
                    z = time.time()
                    
                    media_info = master.avTransport.GetMediaInfo([('InstanceID', 0)])
                    #media_uri = media_info['CurrentURI']
                    meta = media_info['CurrentURIMetaData']
                    if meta:
                        root = ET.fromstring(meta)
                        service = root[0][0].text
                    else:
                        service = "No service"
                                      
                    prev_title = title
                    
                    zz = get_images(track['artist'])
                    url = zz[0]['link']
                    response = requests.get(url)
                    
                    try:
                        img = wand.image.Image(file=StringIO(response.content))
                    except Exception as detail:
                        img = wand.image.Image(filename = "test.bmp")
                        print "img = wand.image.Image(file=StringIO(response.content)) generated the following exception:", detail

                    img.transform(resize = '320x240^')
                    img = img.convert('bmp')
                    
                    #f = StringIO() ###################### couldn't get these three lines to work hence why I am saving to disk
                    #img.save(file = f) ####################
                    #img = pygame.image.load(f, "z.bmp")
                    
                    img.save(filename = "test1.bmp") #couldn't get it to save to StringIO object obviating need to save to disk
                    img = pygame.image.load("test1.bmp").convert()
                    #img.set_alpha(100) # the lower the number the more faded - 75 seems too faded; try 100
                    
                    sub_img = img.subsurface((0,0,320,80))    #rect: (x1, y1, width, height)
                    sub_img.set_alpha(100)
                    zzz = pygame.Surface((320,80)) 
                    zzz.fill((0,0,0))
                    #sprite = pygame.sprite.Sprite() #############
                    #sprite.image = img              #############
                    #sprite.rect = img.get_rect()    #############

                    font = pygame.font.SysFont('Sans', 16)
                    font.set_bold(True)
                        
                    track['date'] = get_release_date(track['artist'], track['album'], track['title']) # better here since not done every time
                        
                    text1 = font.render("Artist: "+track.get('artist'), True, (255, 0, 0))
                    text2 = font.render("Album: "+track.get('album'), True, (255, 0, 0))
                    text3 = font.render("Song: "+track.get('title'), True, (255, 0, 0))
                    text4 = font.render("Release date: "+track.get('date'), True, (255, 0, 0))
                    
                    screen.fill((0,0,0)) ################################################## added this to alpha
                    screen.blit(img, (0,0))
                    screen.blit(zzz, (0,0))
                    screen.blit(sub_img, (0,0))                    
                    screen.blit(text1, (0,0)) #sprite.rect)
                    screen.blit(text2, (0,18)) #sprite.rect)
                    screen.blit(text3, (0,36)) #sprite.rect)
                    screen.blit(text4, (0,54)) #sprite.rect)
                      
                    #sprite.image.blit(text1, (0,0)) #sprite.rect)
                    #sprite.image.blit(text2, (0,25)) #sprite.rect)
                    #sprite.image.blit(text3, (0,50)) #sprite.rect)
                    #sprite.image.blit(text4, (0,75)) #sprite.rect)

                    #group = pygame.sprite.Group()
                    #group.add(sprite)
                    #group.draw(screen)

                    pygame.display.flip()
                        
                    os.remove("test1.bmp")
                    
                    i = 0
                    
                    sleep(.05)
                    
                else:
                
                    if time.time() - z > 10:
                        
                        i = i+1 if i < 9 else 0
                        
                        display_song_info(i)
                        
                        if 0:
                            zz = get_images(track['artist'])
                            url = zz[i]['link']
       
                            try:
                                response = requests.get(url)
                            except Exception as detail:
                                print "response = requests.get(url) generated exception:", detail
                                
                            try:
                                img = wand.image.Image(file=StringIO(response.content))
                            except Exception as detail:
                                img = wand.image.Image(filename = "test.bmp")
                                print "img = wand.image.Image(file=StringIO(response.content)) generated exception:", detail

                            img.transform(resize = '320x240^')
                            img = img.convert('bmp')
                            img.save(filename = "test1.bmp")
                            img = pygame.image.load("test1.bmp").convert()
                            img.set_alpha(100) # the lower the number the more faded - 75 seems too faded; try 100
     
                            font = pygame.font.SysFont('Sans', 16)
                            font.set_bold(True)
                            
                            track['date'] = get_release_date(track['artist'], track['album'], track['title']) # better in both places
                            
                            text1 = font.render("Artist: "+track.get('artist'), True, (255, 0, 0))
                            text2 = font.render("Album: "+track.get('album'), True, (255, 0, 0))
                            text3 = font.render("Song: "+track.get('title'), True, (255, 0, 0))
                            text4 = font.render("Release date: "+track.get('date'), True, (255, 0, 0))
                            
                            screen.fill((0,0,0)) ################################################## added this to alpha
                            screen.blit(img, (0,0))                   
                            screen.blit(text1, (0,0)) 
                            screen.blit(text2, (0,18)) 
                            screen.blit(text3, (0,36)) 
                            screen.blit(text4, (0,54)) 

                            pygame.display.flip()
                            
                            os.remove("test1.bmp")
                        
                        z = time.time()
                        
                #end display_song_info() ##########################################
                    
            sleep(0.2)
            continue
        #end if mode and not b:
        
        if mode: 
#            lcd.clear()
#            lcd.message(b[1])
#            lcd.backlight(b[2])
#            b[3]()
#            prev_title = ''
#            
#            sleep(0.2)
            pass
            continue
            
        if b: #if mode would have been caught by above
    
            b[4]()
            sleep(0.2)
       


