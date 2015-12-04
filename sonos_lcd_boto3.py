import os
import argparse
from time import sleep
import datetime
import random
import xml.etree.ElementTree as ET
import threading
import sys
import textwrap
from Adafruit_LCD_Plate.Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
import dropbox
import requests
from lcdscroll import Scroller
import config as c

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('scrobble_new')

lcd = Adafruit_CharLCDPlate()

lcd.clear()
lcd.message("Sonos-companion")

# backlight colors
col = (lcd.RED , lcd.YELLOW, lcd.GREEN, lcd.TEAL, lcd.BLUE, lcd.VIOLET, lcd.ON, lcd.OFF)


def display_song_info(track):
        
    title = track.get('title', 'No title')
    artist = track.get('artist', 'No artist')
    album = track.get('album', 'No album')

    message = '{}\n{}'.format(title.encode('ascii', 'ignore'), artist.encode('ascii', 'ignore'))

    lcd.clear()
    lcd.backlight(col[random.randrange(0,6)])
    lcd.message(message)
    
    scroller.setLines(message)

def display_weather():
    
    # Tuesday :  Showers and thunderstorms. Lows overnight in the low 70s.
    # Tuesday Night :  Thunderstorms likely. Low 72F. Winds SSW at 5 to 10 mph. Chance of rain 90%.
            
    r = requests.get("http://api.wunderground.com/api/9862edd5de2d456c/forecast/q/10011.json")
    m1 = r.json()['forecast']['txt_forecast']['forecastday'][0]['title'] + ': ' + r.json()['forecast']['txt_forecast']['forecastday'][0]['fcttext']
    m2 = r.json()['forecast']['txt_forecast']['forecastday'][1]['title'] + ': ' + r.json()['forecast']['txt_forecast']['forecastday'][1]['fcttext']
    
    lcd.clear()
    lcd.backlight(lcd.RED)
    lcd.message([m1,m2])

    scroller.setLines([m1, m2])
            
    return textwrap.wrap(m1+m2,99)

def thread_scroller():

    while 1:
        if scroll:
            message = scroller.scroll()
            lcd.clear()
            lcd.message(message)
        sleep(.5)

if __name__ == '__main__':
    
    #globals that are modified by functions and declared as global
    scroll = True
    prev_title = '0'
    prev_hour = -1
    scroller = Scroller()
    scroller.setLines("Hello Steve")
    t = threading.Thread(target=thread_scroller)
    t.daemon = True # quits when main thread is terminated
    t.start()

    while 1:
        try:

            result = table.query(KeyConditionExpression=Key('location').eq('nyc'), ScanIndexForward=False, Limit=1) #by default the sort order is ascending

            if result['Count']:
                track = result['Items'][0]
                if track['ts'] > Decimal(time.time())-300:
        
                    title = track.get('title', 'No title')
                    if prev_title != title:
                        scroll = False      
                        display_song_info(track)
                        prev_title = title
                        sleep(1) 
                        scroll = True
                    
            sleep(0.1)

        except KeyboardInterrupt:
            raise
        except:
            print "Experienced exception during while loop: ", sys.exc_info()[0]

