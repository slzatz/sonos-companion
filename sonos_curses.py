#!bin/python
'''
0=temp sensors (CT, NYC)
1=news feeds (WSJ, NYT, ArsTechnica, Reddit All, Twitter)
2=stock quote
3=ToDos
4=gmail and google calendar
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

layout   = {
             1:{'y':1,  'h':12}, #2,10
             2:{'y':13, 'h':6},
             3:{'y':19, 'h':13},
             5:{'y':32, 'h':6},
             6:{'y':38, 'h':14},
            11:{'y':52, 'h':20},
            15:{'y':1, 'x':75, 'h':7},
            10:{'y':8, 'x':75, 'h':7},
             9:{'y':15, 'x':75, 'h':7},
             8:{'y':22, 'x':75, 'h':50},
             }

# paho stuff
info_topic = "esp_tft" # should be changed to "info"
def on_connect(client, userdata, flags, rc):
    print("(Re)Connected with result code "+str(rc)) 

    # Subscribing in on_connect() means that if we lose the 
    # connection and reconnect then subscriptions will be renewed.
    client.subscribe([(info_topic, 0)])

def on_disconnect():
    print("Disconnected from mqtt broker")

screen = curses.initscr()
curses.start_color()
curses.use_default_colors()
curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_WHITE)
#curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)
curses.init_pair(4, 15, -1)
color_map = {'{blue}':3, '{red}':1, '{green}':2,'{white}':4}
curses.curs_set(0)
curses.cbreak() # respond to keys without needing Enter
curses.noecho()
size = screen.getmaxyx()
screen.nodelay(True)

boxes = {}
#curses.newwin(nlines, ncols, begin_y, begin_x)
for b in layout:
    boxes[b] = curses.newwin(layout[b]['h'], 70, layout[b]['y'], layout[b].get('x', 1))

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
        box.addstr(1, 1, header, curses.A_BOLD)
        # below was putting this information on first line instead of where now in box
        #screen.move(0,0)
        #screen.clrtoeol()
        #screen.addstr(0,0, header, curses.A_BOLD) #(y,x)
        #screen.refresh()

        bullets = z.get('bullets', True)

        n = 2
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
                item = chr(8226)+' '+item

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
                        box.addstr(n, 1 + xx, phrase[1],  #(y,x)
                          curses.color_pair(color_map.get(phrase[0], 4))|font) 
                    except Exception as e:
                         pass
                    #box.refresh()
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
        box.addstr(1, 61, t, curses.color_pair(3)|curses.A_BOLD) 
        box.refresh()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(aws_mqtt_uri, 1883, 60)
# brief loop below lets the mqtt client connect to the broker
t0 = time.time()
while time.time() < t0 + 10:
    client.loop(timeout = 1.0)
    time.sleep(1)
screen.clear()
screen.addstr(0,0, f"Hello Steve. screen size = x:{size[1]},y:{size[0]}", curses.A_BOLD)
screen.addstr(size[0]-1, 0, f"Goodbye Steve", curses.color_pair(3)|curses.A_BOLD)
screen.refresh()
while 1:
    client.loop(timeout = 1.0)
    c = screen.getch()
    if c == -1:
        pass
    else:
        screen.addstr(size[0]-1, 0, f"key={c}", curses.color_pair(3)|curses.A_BOLD)
        
    time.sleep(.1)
