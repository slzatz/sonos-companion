import os
import argparse
from time import sleep
import sys
import textwrap
home = os.path.split(os.getcwd())[0]
#soco_dir = os.path.join(home,'SoCo')
#sys.path = [soco_dir] + sys.path
sys.path = [os.path.join(home, 'Soco')] + [os.path.join(home, 'pydub')] + sys.path
import requests
import soco
from soco import config
from soco.data_structures import URI
from pydub import AudioSegment

config.CACHE_ENABLED = False

parser = argparse.ArgumentParser(description='Text to speech through google and sonos')
parser.add_argument('text', help='Text to speak')
args = parser.parse_args()

uri = "x-rincon-mp3radio://translate.google.com/translate_tts?tl=en&q={}"
uri2 = "http://translate.google.com/translate_tts?tl=en&q={}"

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
#s = AudioSegment.from_mp3('good_morning.mp3')

def text2mp3(text, file_):
    for line in text:
        print line
        with open('output.mp3', 'wb') as handle:
            response = requests.get(uri2.format(line), stream=True)

            if not response.ok:
                sys.exit()

            for block in response.iter_content(1024):
                if not block:
                    break

                handle.write(block)
        output = AudioSegment.from_mp3('output.mp3')
        return output

s0 = text2mp3(["Good Morning, Steve"], 'good_morning.mp3')
s1 = text2mp3(display_weather(), 'weather.mp3')
s2 = s0 + s1
s2.export('greeting.mp3', format='mp3')

cn = os.environ['COMPUTERNAME']
uri = '''x-file-cifs://'''+cn+'''/home/slzatz/greeting.mp3'''
#uri = 'x-file-cifs://my_Mac/my_iTunes_folder/any_old.mp3'
#uri = URI('C:\home\slzatz\greeting.mp3')
print uri
master.add_uri_to_queue(uri)
#uri = 'file:///C:home/slzatz/greeting.mp3'

meta_format_radio = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns=
"urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="-1" parentID="-1" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItem.audioBroadcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

meta = meta_format_radio.format(title='google', service='SA_RINCON65031_')
#master.play_uri(uri, meta)
#master.play_uri(uri)

#with open('output.mp3', 'wb') as handle:
#    response = requests.get('http://translate.google.com/translate_tts?tl=en&q=%22hello%20boys%22', stream=True)
#
#    if not response.ok:
#        sys.exit()
#
#    for block in response.iter_content(1024):
#        if not block:
#            break
#
#        handle.write(block)
#from soco.data_structures import URI
#uri = URI('http://www.a.com/a.mp3')
