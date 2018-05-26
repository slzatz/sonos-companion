#!bin/python
'''
python3 script: displays infoboxes with key determing which box is displayed
See below for mapping from pos (int) to topic of infobox
'''

import curses
from config import aws_mqtt_uri 
import paho.mqtt.client as mqtt
import json
import textwrap
from datetime import datetime
import time
import re

info_boxes = {
0:"temp sensors (CT, NYC)",
1:"news feeds (WSJ, NYT, ArsTechnica, Reddit All, Twitter)",
2:"stock quote",
3:"ToDos",
4:"gmail and google calendar",
5:"sales forecast",
6:"outlook_schedule",
7:"artist image",
8:"lyrics",
9:"track_info broadcast by sonos_track_info.py",
10:"sonos status (PLAYING, TRANSITIONING, STOPPED",
11:"sales top opportunities",
12:"Reminders (alarms) ",
13:"Ticklers",
14:"Facts",
15:"weather/tides",
16:"Industry",
17:"temp sensor"
}

selected_pos = 1
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
for b in info_boxes:
    boxes[b] = curses.newwin(size[0]-2, size[1]-1, 1, 1)
    boxes[b].box()
    boxes[b].addstr(2, 2, f"No content received yet for {b}", 
                    curses.color_pair(3)|curses.A_BOLD) 


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

    global selected_pos
    topic = msg.topic
    body = msg.payload
    #print(topic+": "+str(body))

    try:
        z = json.loads(body)
    except Exception as e:
        print("error reading the mqtt message body: ", e)
        return

    #if topic in (info_topic, image_topic):
    pos = z.get('pos')
    #if not pos in layout:
    if not pos in info_boxes:
        return

    dest = z.get('dest')

    if topic==info_topic:

        box = boxes[pos]
        box.clear()
        box.box()

        header = "{} [{}]".format(z.get('header', 'no info'), pos)
        box.addstr(1, 1, header, curses.A_BOLD)

        bullets = z.get('bullets', True)

        n = 2
        for item in z.get('text',['No text']): 
            if not item.strip():
                n+=1
                continue
            #font = 1 #means font will be normal
            font = curses.A_NORMAL
            max_chars_line = size[1] - 3        
            indent = 1

            if n+2 == size[0]:
                break

            if item[0] == '#':
                item=item[1:]
                font = curses.A_BOLD
                max_chars_line = size[1] - 5

            if item[0] == '*': 
                item=chr(187)+' '+item[1:]
            elif bullets:
                item = chr(8226)+' '+item

            # if line is just whitespace it returns []
            lines = textwrap.wrap(item, max_chars_line)

            for l,line in enumerate(lines):

                if n+2 == size[0]:
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
        box.addstr(1, size[1]-10, t, curses.color_pair(3)|curses.A_BOLD) 
        if pos==selected_pos:
            box.refresh()
        elif pos==8: #switch to lyrics info box if new lyrics show up
            selected_pos = 8
            box.refresh()
            screen.move(0, size[1]-8)
            screen.clrtoeol()
            screen.addstr(0, size[1]-8, "key=8", curses.color_pair(3)|curses.A_BOLD)
            screen.refresh()

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
screen.addstr(6, 2, f"No content received yet for {selected_pos}", 
                curses.color_pair(3)|curses.A_BOLD) 
s = "1:news 2:quote 3:todos 4:gmail 5:sales forecast, 6:outlook schedule, 7:artist image 8:lyrics 9:track info"
if len(s) > size[1]:
    s = s[:size[1]-1]
screen.addstr(size[0]-1, 0, s, curses.color_pair(3)|curses.A_BOLD)
screen.refresh()

while 1:
    #client.loop(timeout = 1.0)
    client.loop(timeout = 0.25) #was 1.0
    redraw = False
    n = screen.getch()
    if n != -1:
        c = chr(n)
        if c.isnumeric():
            selected_pos = int(c)
            redraw = True
        elif c == 'h':
            selected_pos = selected_pos-1 if selected_pos > 0 else 17
            c = selected_pos
            redraw = True
        elif c == 'l':
            selected_pos = selected_pos+1 if selected_pos < 17 else 0
            c = selected_pos
            redraw = True

        if redraw:
            boxes[selected_pos].redrawwin()
            boxes[selected_pos].refresh()

        screen.move(0, size[1]-8)
        screen.clrtoeol()
        screen.addstr(0, size[1]-8, f"key={c}", curses.color_pair(3)|curses.A_BOLD)
        screen.refresh()
        
    size_current = screen.getmaxyx()
    if size != size_current:
        size = size_current
        screen.addstr(0,0, f"Hello Steve. screen size = x:{size[1]},y:{size[0]}", curses.A_BOLD)
    time.sleep(.1)
