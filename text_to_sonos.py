import os
import argparse
from time import sleep
import sys
import textwrap
home = os.path.split(os.getcwd())[0]
soco_dir = os.path.join(home,'SoCo')
sys.path = [soco_dir] + sys.path
import requests
import soco
from soco import config

config.CACHE_ENABLED = False

parser = argparse.ArgumentParser(description='Text to speech through google and sonos')
parser.add_argument('text', help='Text to speak')
args = parser.parse_args()

uri = "x-rincon-mp3radio://translate.google.com/translate_tts?tl=en&q={}"

n = 0
while 1:
    n+=1
    print "attempt "+str(n)
    try:
        speakers = list(soco.discover())
    except TypeError:
        sleep(1)
    else:
        break
    sleep(0.1)
    
print speakers 

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

# for s in speakers:
    # if s != master:
        # s.join(master)

def get_info():

    info = master.avTransport.GetMediaInfo([('InstanceID', 0)])
    uri = info['CurrentURI']
    meta = info['CurrentURIMetaData']
    print "uri = ", uri
    print "meta = ", meta
    
def my_add_to_queue(uri, metadata):
    response = master.avTransport.AddURIToQueue([
            ('InstanceID', 0),
            ('EnqueuedURI', uri),
            ('EnqueuedURIMetaData', metadata),
            ('DesiredFirstTrackNumberEnqueued', 0),
            ('EnqueueAsNext', 1)
            ])
    qnumber = response['FirstTrackNumberEnqueued']
    print response
    return int(qnumber)
    
def display_weather():
    
    # Tuesday :  Showers and thunderstorms. Lows overnight in the low 70s.
    # Tuesday Night :  Thunderstorms likely. Low 72F. Winds SSW at 5 to 10 mph. Chance of rain 90%.
    
    try:
        r = requests.get("http://api.wunderground.com/api/9862edd5de2d456c/forecast/q/10011.json")
        m1 = r.json()['forecast']['txt_forecast']['forecastday'][0]['title'] + ': ' + r.json()['forecast']['txt_forecast']['forecastday'][0]['fcttext']
#        m2 = r.json()['forecast']['txt_forecast']['forecastday'][1]['title'] + ': ' + r.json()['forecast']['txt_forecast']['forecastday'][1]['fcttext']
    except requests.exceptions.ConnectionError as e:
        print "ConnectionError in request in display_weather: ", e
    else:
        return textwrap.wrap(m1,99)

meta_format_radio = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns=
"urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="-1" parentID="-1" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItem.audioBroadcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

meta = meta_format_radio.format(title='google', service='SA_RINCON65031_')
#master.play_uri(uri.format(args.text), meta)
#sleep(20)
#master.stop()

text = display_weather()
#text = ["The rain in spain falls mainly on the plain", "Neil Young is the greatest rock star ever",  "Sarah is very sleepy", "The brick fireplace should be painted white"]
print text

for line in text:
    print line
    master.play_uri(uri.format(line), meta)
    sleep(.1)
    played = False #= "TRANSITIONING"
    while 1:
        state = master.get_current_transport_info()['current_transport_state']
        print "state = ", state
        if state == 'PLAYING':
            played = True
        elif played == False:
            continue
        else:
            break
        #'PAUSED_PLAYBACK'
        #    break
        sleep(.2)
master.stop()
