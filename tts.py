'''Use on the command line and put whatever text you want to speak through 
sonos in quotes
python tts "hello, how are you - I am fine"
'''
import os
import argparse
from time import sleep
import sys
import textwrap
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'Soco')] + [os.path.join(home, 'pydub')] + sys.path
import requests
import soco
import config as c
from soco import config
from soco.data_structures import URI
from pydub import AudioSegment
import dropbox

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
    
def speak(phrase):
    meta = meta_format_radio.format(title='google', service='SA_RINCON65031_')

    s0 = AudioSegment.silent(duration=10)
    s = s0 + text2mp3(textwrap.wrap(phrase, 99), 'output.mp3')
    s.export('output.wav', format='wav')
    # some problem on raspberry pi with creating mp3s
    f = open('output.wav', 'rb')
    response = client.put_file('/Public/output.wav', f, overwrite=True) # the problem may be FFmpeg or avconv -- pydub can use either

    z = client.media("/Public/output.wav")
    public_streaming_url = z['url']
    print "public_streaming_url =", public_streaming_url
    master.play_uri(public_streaming_url,'')
    sleep(10)

def text2mp3(text, file_):
    for line in text:
        print line
        with open('output.mp3', 'wb') as handle:
            try:
                response = requests.get(uri2.format(line), stream=True)
            except UnicodeEncodeError as e:
                print e
                continue
            if not response.ok:
               continue 

            for block in response.iter_content(1024):
                if not block:
                    break

                handle.write(block)
        output = AudioSegment.from_mp3('output.mp3')
        return output

speak(args.text) 
