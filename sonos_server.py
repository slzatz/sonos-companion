#!bin/python
'''
python3 script that imports sonos_actions.py and currently support m5sonos_menu5.py
using urequests, the m5 sends json in the form of:{'action':'list_queue'}
'''

from flask import Flask, request #Response
import json
import sonos_actions

sp = list(sonos_actions.get_sonos_players())
text = [f"{s.player_name} <-- {s.group.coordinator.player_name}" for s in sp]

for idx, line in enumerate(text):
    print('  %2d. %s' % (idx + 1, line))

while True:
    response = input("Which speaker do you want to become the master speaker? ")

    try:
        response = int(response)
        master = sonos_actions.master = sp[response - 1]
        break
    except (ValueError, IndexError):
        print(f"{response!r} isn't valid. Pick a number between 1 and {len(text)}")

print("Master speaker is: {}".format(master.player_name))

app = Flask(__name__)

@app.route('/actions', methods=['POST'])
def process_message():
    j = request.json
    print("json loaded =", j)
    action = j['action']
    print("action =", action)

    if action == 'list_queue':
        queue = sonos_actions.list_queue()
        return json.dumps(queue)

    elif action == 'play_pause':
        sonos_actions.play_pause()

    elif action in ('quieter','louder'):
        sonos_actions.turn_volume(action)
        
    elif action == 'next':
        sonos_actions.playback('next')

    elif action.startswith("station"):
        station = action[8:]
        sonos_actions.play_station(station)

    elif action.startswith("shuffle"):
        artist = action[8:]
        sonos_actions.shuffle(artist)

    elif action.startswith("play_queue"):
        pos = action[11:]
        pos = int(pos) if pos else 0
        sonos_actions.play_from_queue(pos)

    else:
        print("I don't recognize that action")

    return "OK"

try:
    app.run(debug=True,
            port=5000,
            threaded=False,
            use_reloader=False,
            use_debugger=True,
            host='0.0.0.0'
            )
finally:
    print("Disconnecting clients")

print("Done")

