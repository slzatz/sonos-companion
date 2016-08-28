'''
This is a python 2.7 program that is usually run  on a raspberry pi
Intended to respond to commands issued by the esp8266
'''
import os
from time import sleep
import json
import sys
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + sys.path
import soco
from soco import config as soco_config
import paho.mqtt.client as mqtt
from config import user_id, local_mqtt_uri, location

soco_config.CACHE_ENABLED = False

n = 0
while 1:
    n+=1
    print "attempt "+str(n) 
    try:
        sp = soco.discover(timeout=2)
        speakers = {s.player_name:s for s in sp}
    except TypeError as e:    
        print e 
        sleep(1)       
    else:
        break 
    
for s in sp:
    print "{} -- coordinator:{}".format(s.player_name, s.group.coordinator.player_name) 

master_name = raw_input("Which speaker do you want to be master? ")
master = speakers.get(master_name)
if master:
    print "Master speaker is: {}".format(master.player_name) 
    sp = [s for s in sp if s.group.coordinator is master]
    print "Master group:"
    for s in sp:
        print "{} -- coordinator:{}".format(s.player_name, s.group.coordinator.player_name) 

else:
    print "Somehow you didn't pick a master or spell it correctly (case matters)" 
    sys.exit(1)

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    # client.subscribe("$SYS/#")
    client.subscribe('sonos/'+location)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))
    body = msg.payload
    print "mqtt messge body =", body

    try:
        task = json.loads(body)
    except Exception as e:
        print "error reading the mqtt message body: ", e
        return

    action = task.get('action', '')

    if action == 'play_pause':
    
        try:
            state = master.get_current_transport_info()['current_transport_state']
        except Exception as e:
            print "Encountered error in state = master.get_current_transport_info(): ", e
            state = 'ERROR'

        # check if sonos is playing music
        if state == 'PLAYING':
            master.pause()
        elif state!='ERROR':
            master.play()

    elif action in ('quieter','louder'):
        
        for s in sp:
            s.volume = s.volume - 10 if action=='quieter' else s.volume + 10

        print "I tried to make the volume "+action

    elif action == "volume": #{"action":"volume", "level":70}

        level = task.get("level", 500)
        level = int(round(level/10, -1))

        if level < 70:

            for s in sp:
                s.volume = level

            print "I changed the volume to:", level
        else:
            print "Volume was too high:", level

    elif action == "wnyc":
        
        meta_format_radio = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="-1" parentID="-1" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItem.audioBroadcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

        station = ["WNYC-FM", "x-sonosapi-stream:s21606?sid=254&flags=32", "SA_RINCON65031_"] 
        uri = station[1]
        uri = uri.replace('&', '&amp;') # need to escape '&' in radio URIs
        meta = meta_format_radio.format(title=station[0], service=station[2])
        master.play_uri(uri, meta, station[0]) # station[0] is the title of the station

    else:
        print "I have no idea what you said"

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(local_mqtt_uri, 1883, 60)
client.loop_forever()
# could also call while 1: client.loop() sleep(1) so could do other things in loop. Not sure what timeout should be set to if we call loop "manually"
