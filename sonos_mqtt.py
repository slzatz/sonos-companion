#!bin/python
'''
Currently uses linode instance as mqtt server
Receives mqtt messages that initiate sonos actions
like shuffling an artist or playing a track or album
Uses the music services capabilities of SoCo
'''
import json
import soco
import paho.mqtt.client as mqtt
from config import linode_uri, music_service
from soco.music_services import MusicService
from soco.discovery import by_name
import random

#soco_config.CACHE_ENABLED = False
topic = "trellis"
ms = MusicService(music_service)

master = by_name("Office2")

##sp = list(sonos_actions.get_sonos_players())
##text = [f"{s.player_name} <-- {s.group.coordinator.player_name}" for s in sp]
##
##for idx, line in enumerate(text):
##    print('  %2d. %s' % (idx + 1, line))
##
##while True:
##    response = input("Which speaker do you want to become the master speaker? ")
##
##    try:
##        response = int(response)
##        master = sonos_actions.master = sonos_actions2.master = sp[response - 1]
##        break
##    except (ValueError, IndexError):
##        print("{!r} isn't a valid choice. Pick a number between 1 and {}:\n".format(response,
##      len(z)))

print("Master speaker is: {}".format(master.player_name))

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    # client.subscribe("$SYS/#")
    client.subscribe(topic)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))
    body = msg.payload
    print("mqtt messge body =", body)

    try:
        task = json.loads(body)
    except Exception as e:
        print("error reading the mqtt message body: ", e)
        return

    action = task.get('action', '')

    if action == 'play_pause':
    
        try:
            state = master.get_current_transport_info()['current_transport_state']
        except Exception as e:
            print("Encountered error in state = master.get_current_transport_info(): ", e)
            state = 'ERROR'

        # check if sonos is playing music
        if state == 'PLAYING':
            master.pause()
        elif state!='ERROR':
            master.play()

    elif action in ('quieter','louder'):
        
        for s in sp:
            s.volume = s.volume - 10 if action=='quieter' else s.volume + 10

        print("I tried to make the volume "+action)

    elif action == "volume": #{"action":"volume", "level":70}

        level = task.get("level", 500)
        level = int(round(level/10, -1))

        if level < 70:

            for s in sp:
                s.volume = level

            print("I changed the volume to:", level)
        else:
            print("Volume was too high:", level)

    #elif action == "play_wnyc":
    #    sonos_actions.play_station('wnyc')

    elif action == 'next':
        sonos_actions.playback('next')

    elif action.startswith("station"):
        station = action[8:]
        sonos_actions.play_station(station)

    elif action.startswith("shuffle"):
        master.clear_queue()
        artist = action[8:]
        results = ms.search("tracks", artist)
        random.shuffle(results)
        for track in results:
            master.add_to_queue(track)
        master.play()    

    elif action.startswith("album"):
        master.clear_queue()
        album = action[6:]
        results = ms.search("albums", album)
        random.shuffle(results)
        for track in results:
            master.add_to_queue(track)
        master.play()    
##    elif action.startswith("shuffle"):
##        artist = action[8:]
##        print(artist)
##        m = sonos_actions2.shuffle([artist])
##        print(m)

    elif action == "play_queue":
        queue = master.get_queue()
        if len(queue) != 0:
            master.stop()
            master.play_from_queue(0)

    else:
        print("I have no idea what you said")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(linode_uri, 1883, 60)
client.loop_forever()
