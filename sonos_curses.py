#!bin/python
import curses
from config import aws_mqtt_uri 
import paho.mqtt.client as mqtt
import json
import textwrap
from datetime import datetime
import time
import re

MAX_HEIGHT = 20 
MAX_WIDTH = 50
MIN_WIDTH = 30

info_sources = [1,2,3,5,6,11,15]
location = {1:1, 2:30, 3:36, 5:50, 6:60, 11:72, 15:80}

# paho stuff
info_topic = "esp_tft" # should be changed to "info"
def on_connect(client, userdata, flags, rc):
    print("(Re)Connected with result code "+str(rc)) 

    # Subscribing in on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    client.subscribe([(info_topic, 0)])

def on_disconnect():
    print("Disconnected from mqtt broker")

screen = curses.initscr()

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
    if not k in info_sources: ####################
        return

    dest = z.get('dest')

    if topic==info_topic:

        header = "{} [{}] {}".format(z.get('header', 'no source'), k, dest if dest else " ") # problem if dest None would like to know what it was
        #screen.addstr(20,20, "Hello World", curses.A_BOLD)
        screen.clear()
        screen.refresh() #not necessary I don't think
        line_height = 1
        line_widths = [0] # for situation when text = [''] otherwise line_widths = [] and can't do max
        bullets = z.get('bullets', True)

        #n = line_height #20
        n = location.get(k, 1)
        for item in z.get('text',['No text']): 
            if not item.strip():
                n+=line_height
                continue
            #font.set_bold(False)
            max_chars_line = 66        
            indent = 1
            #n+=4 if bullets else 0 # makes multi-line bullets more separated from prev and next bullet

            if n+line_height > location.get(k,1) + MAX_HEIGHT:
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

            lines = textwrap.wrap(item, max_chars_line) # if line is just whitespace it returns []

            for l,line in enumerate(lines):

                if n+line_height > location.get(k,1) + MAX_HEIGHT: #20
                    break

                if l:
                    phrases = get_phrases(line, phrase[0])
                else:
                    phrases = get_phrases(line)

                xx = 0
                for phrase in phrases:
                    #screen.addstr(indent + xx, n, phrase[1], curses.A_BOLD)
                    screen.addstr(n, indent + xx, phrase[1], curses.A_BOLD) #(y,x)
                    screen.refresh()
                    xx+= len(phrase[1])

                line_widths.append(xx)
                n+=line_height

        # determine the size of the rectangle for foo and its line border
        max_line = max(line_widths)
        if max_line > MAX_WIDTH:
            max_line = MAX_WIDTH
        elif max_line < MIN_WIDTH:
            max_line = MIN_WIDTH

        # item is the last item and if the last item is white space n gets incremented unnecessarily and this 'un'increments it
        if not item.strip():
            n-=line_height
        #height = min(n+12, MAX_HEIGHT)
        #screen.border(0)
        box1 = curses.newwin(n-location.get(k,1)+2, max_line+20, location.get(k, 1)-1, 0)
        box1.box()
        box1.overlay(screen)
        screen.refresh()
        #box1.refresh()

        # put time in upper right of box
        t = datetime.now().strftime("%I:%M %p")
        t = t[1:] if t[0] == '0' else t
        t = t[:-2] + t[-2:].lower()
        #screen.addstr(20,20, "Hello World", curses.A_BOLD)
        #screen.refresh()

print("about to connect to mqtt broker")
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(aws_mqtt_uri, 1883, 60)
while 1:
    client.loop(timeout = 1.0)
    time.sleep(1)
#time.sleep(60)
#curses.wrapper(main)
