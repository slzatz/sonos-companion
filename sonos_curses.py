#!bin/python
'''
0=temp sensors (CT, NYC)
1=news feeds (WSJ, NYT, ArsTechnica, Reddit All, Twitter)
2=stock quote
3=ToDos
4=sonos status (PLAYING, TRANSITIONING, STOPPED) broadcast by sonos_track_info on topic esp_tft and also on sonos/{loc}/status for esp_tft_mqtt_photos(and lyrics) 
5=sales forecast
6=outlook_schedule
7=artist image
8=lyrics
9=track_info broadcast by sonos_track_info.py
10=sonos status (PLAYING, TRANSITIONING, STOPPED
11=sales top opportunities
12=Reminders (alarms) 
13=Ticklers
14=Facts
15=weather/tides
16=Industry
17=temp sensor
'''

import curses
from config import aws_mqtt_uri 
import paho.mqtt.client as mqtt
import json
import textwrap
from datetime import datetime
import time
import re

layout   = { 1:{'y':2,  'h':9},
             2:{'y':12, 'h':5},
             3:{'y':18, 'h':10},
             5:{'y':29, 'h':5},
             6:{'y':35, 'h':11},
            11:{'y':47, 'h':16},
            15:{'y':64, 'h':6}}

# paho stuff
info_topic = "esp_tft" # should be changed to "info"
def on_connect(client, userdata, flags, rc):
    print("(Re)Connected with result code "+str(rc)) 

    # Subscribing in on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    client.subscribe([(info_topic, 0)])

def on_disconnect():
    print("Disconnected from mqtt broker")

screen = curses.initscr()
curses.curs_set(0)
boxes = {}
#curses.newwin(nlines, ncols, begin_y, begin_x)
for b in layout:
    boxes[b] = curses.newwin(layout[b]['h'], 70, layout[b]['y'], 1)

def main(screen):
    screen.clear()

    screen.addstr(20,20, "Hello World", curses.A_BOLD)
    screen.refresh()
    screen.getkey()

#phrases = [(u'{}', u'the holy grail '), (u'{blue}', u' is very nice '), (u'{red}', u' is it?')]
def get_phrases(line, start='{}'):

    if line.find('{') == -1:
        #print("phrases =", [(start, line)])
        return [(start, line)]

    if line[0]!='{':
        line = start+line

    line = line+'{}'

    z = re.finditer(r'{(.*?)}', line)
    s = [[m.group(), m.span()] for m in z]
    #print(s)
    if not s:
        return [('{}', line)]
    phrases = []
    for j in range(len(s)-1):
        phrases.append((s[j][0],line[s[j][1][1]:s[j+1][1][0]]))
    #print("phrases =", phrases)
    return phrases

def on_message(client, userdata, msg):
    # {"pos":7, "uri":"https://s-media-cache-ak0.pinimg.com/originals/cb/e8/9d/cbe89da159842dd218ec722082ab50c5.jpg", "header":"Neil Young"}
    # {"pos":4, "header":"Wall Street Journal", "text":"["The rain in spain falls mainly on the plain", "I am a yankee doodle dandy"]}
    topic = msg.topic
    body = msg.payload
    #print(topic+": "+str(body))

    try:
        z = json.loads(body)
    except Exception as e:
        print("error reading the mqtt message body: ", e)
        return

    #if topic in (info_topic, image_topic):
    k = z.get('pos')
    if not k in layout: ####################
        return

    dest = z.get('dest')

    if topic==info_topic:

        box = boxes[k]
        box.clear()
        box.box()

        header = "{} [{}] {}".format(z.get('header', 'no source'), k, dest if dest else " ") # problem if dest None would like to know what it was
        #screen.clear()
        screen.move(0,0)
        screen.clrtoeol()
        screen.addstr(0,0, header, curses.A_BOLD) #(y,x)
        screen.refresh()
        bullets = z.get('bullets', True)

        n = 1
        for item in z.get('text',['No text']): 
            if not item.strip():
                n+=1
                continue
            #font.set_bold(False)
            max_chars_line = 50        
            indent = 1
            #n+=4 if bullets else 0 # makes multi-line bullets more separated from prev and next bullet

            if n+1 == layout[k]['h']:
                break

            if item[0] == '#':
                item=item[1:]
                #font.set_bold(True)
                max_chars_line = 60

            if item[0] == '*': 
                #foo.blit(star, (2,n+7))
                item=item[1:]
            elif bullets:
                #foo.blit(bullet_surface, (7,n+13)) #(4,n+13)
                pass
            # neither a star in front of item or a bullet
            #else:
            #    max_chars_line+= 1 
            #    indent = 10

            # if line is just whitespace it returns []
            lines = textwrap.wrap(item, max_chars_line)

            for l,line in enumerate(lines):

                if n+1 == layout[k]['h']:
                    break

                if l:
                    phrases = get_phrases(line, phrase[0])
                else:
                    phrases = get_phrases(line)

                xx = 0
                for phrase in phrases:
                    try:
                        box.addstr(n, 1 + xx, phrase[1]) #(y,x)
                    except Exception as e:
                         pass
                    box.refresh()
                    xx+= len(phrase[1])

                n+=1

        # item is the last item and if the last item is white space n gets
        # incremented unnecessarily and this 'un'increments it
        if not item.strip():
            n-=1

        # put time in upper right of box
        t = datetime.now().strftime("%I:%M %p")
        t = t[1:] if t[0] == '0' else t
        t = t[:-2] + t[-2:].lower()

print("about to connect to mqtt broker")
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(aws_mqtt_uri, 1883, 60)
# I think I need a client loop here to connect
time.sleep(10)
screen.clear()
screen.addstr(0,0, "Hello Steve", curses.A_BOLD)
screen.refresh()
while 1:
    client.loop(timeout = 1.0)
    time.sleep(1)
#time.sleep(60)
#curses.wrapper(main)
