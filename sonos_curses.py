#!bin/python
'''
0=temp sensors (CT, NYC)
1=news feeds (WSJ, NYT, ArsTechnica, Reddit All, Twitter)
2=stock quote
3=ToDos
4=sonos status (PLAYING, TRANSITIONING, STOPPED) ...
... broadcast by sonos_track_info on topic esp_tft and also on
... sonos/{loc}/status for esp_tft_mqtt_photos(and lyrics) 
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

layout   = { 1:{'y':1,  'h':10}, #2,9
             2:{'y':11, 'h':6},
             3:{'y':17, 'h':11},
             5:{'y':28, 'h':6},
             6:{'y':34, 'h':12},
            11:{'y':46, 'h':21},
            15:{'y':67, 'h':7}}

# paho stuff
info_topic = "esp_tft" # should be changed to "info"
def on_connect(client, userdata, flags, rc):
    print("(Re)Connected with result code "+str(rc)) 

    # Subscribing in on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    client.subscribe([(info_topic, 0)])

def on_disconnect():
    print("Disconnected from mqtt broker")

screen = curses.initscr()
curses.start_color()
curses.use_default_colors()
curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
#curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)
curses.init_pair(4, 15, -1)
color_map = {'{blue}':3, '{red}':1, '{green}':2,'{white}':4}
curses.curs_set(0)
curses.cbreak() # respond to keys without needing Enter


boxes = {}
#curses.newwin(nlines, ncols, begin_y, begin_x)
for b in layout:
    boxes[b] = curses.newwin(layout[b]['h'], 70, layout[b]['y'], 1)

#screen.getkey()

#phrases = [(u'{}', u'the holy grail '), (u'{blue}', u' is very nice '),...
#...(u'{red}', u' is it?')]
def get_phrases(line, start='{}'):

    if line.find('{') == -1:
        #print("phrases =", [(start, line)])
        return [(start, line)]

    if line[0]!='{':
        line = start+line

    line = line+'{}'

    z = re.finditer(r'{(.*?)}', line)
    s = [[m.group(), m.span()] for m in z]
    if not s:
        return [('{}', line)]
    phrases = []
    for j in range(len(s)-1):
        phrases.append((s[j][0],line[s[j][1][1]:s[j+1][1][0]]))
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
    if not k in layout:
        return

    dest = z.get('dest')

    if topic==info_topic:

        box = boxes[k]
        box.clear()
        box.box()

        header = "{} [{}] {}".format(z.get('header', 'no source'), k, dest if dest else " ")
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
            font = 1 #means font will be normal
            max_chars_line = 65        
            indent = 1

            if n+1 == layout[k]['h']:
                break

            if item[0] == '#':
                item=item[1:]
                font = curses.A_BOLD
                max_chars_line = 60

            if item[0] == '*': 
                item=chr(187)+item[1:]
            elif bullets:
                item = chr(8226)+item

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
                        box.addstr(n, 1 + xx, phrase[1],
                        curses.color_pair(color_map.get(phrase[0], 4))|font) #(y,x)
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
