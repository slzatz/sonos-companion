import os
import argparse
from time import sleep
import sys
import textwrap
import re
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'Soco')] + [os.path.join(home, 'pydub')] + [os.path.join(home, 'twitter')] + sys.path
import requests
import soco
import config as c
from soco import config
from soco.data_structures import URI
from pydub import AudioSegment
import dropbox
from twitter import *

config.CACHE_ENABLED = False

parser = argparse.ArgumentParser(description='Text to speech through google and sonos')
parser.add_argument('text', help='Text to speak')
args = parser.parse_args()

uri = "x-rincon-mp3radio://translate.google.com/translate_tts?tl=en&q={}"
uri2 = "http://translate.google.com/translate_tts?tl=en&q={}"

meta_format_radio = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="-1" parentID="-1" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItem.audioBroadcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

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

user_id = c.user_id
client = dropbox.client.DropboxClient(c.dropbox_code)
oauth_token = c.twitter_oauth_token 
oauth_token_secret = c.twitter_oauth_token_secret
CONSUMER_KEY = c.twitter_CONSUMER_KEY
CONSUMER_SECRET = c.twitter_CONSUMER_SECRET

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
        m2 = r.json()['forecast']['txt_forecast']['forecastday'][1]['title'] + ': ' + r.json()['forecast']['txt_forecast']['forecastday'][1]['fcttext']
    except requests.exceptions.ConnectionError as e:
        print "ConnectionError in request in display_weather: ", e
    else:
        return m1+m2


def speak(phrases):
    meta = meta_format_radio.format(title='google', service='SA_RINCON65031_')

    s = AudioSegment.silent(duration=10)

    for p in phrases:
        s = s + text2mp3(textwrap.wrap(p, 99), 'output.mp3')

    s.export('output.wav', format='wav')

    f = open('output.wav', 'rb')
    response = client.put_file('/Public/output.wav', f, overwrite=True) # the problem may be FFmpeg or avconv -- pydub can use either

    z = client.media("/Public/output.wav")
    public_streaming_url = z['url']
    print "public_streaming_url =", public_streaming_url.encode('ascii','ignore')
    master.play_uri(public_streaming_url,'')

def text2mp3(text, file_):
    with open('output.mp3', 'wb') as handle:
        for line in text:
            line = line.encode('ascii', 'ignore')
            print line
            response = requests.get(uri2.format(line), stream=True)

            if not response.ok:
                print "response not OK"
                return AudioSegment.silent(duration=10)

            for block in response.iter_content(1024):
                if not block:
                    break

                handle.write(block)

    sleep(1) # seems to make sure file is written and closed
    if os.stat('output.mp3')[6]==0:
        return AudioSegment.silent(duration=10)
    else:
        return AudioSegment.from_mp3('output.mp3')

tw = Twitter(auth=OAuth(oauth_token, oauth_token_secret, CONSUMER_KEY, CONSUMER_SECRET))
x = tw.statuses.home_timeline()

for t in x:
    text = t['text']
    text = text[:text.find('http')] ##
    text = re.split('\.|\?', text) ##
    text.insert(0, t['user']['screen_name']) ##
    #speak([t['user']['screen_name'], text[:text.find('http')]])
    speak(text)
    sleep(10)
