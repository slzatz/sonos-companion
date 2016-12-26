'''
No mqtt
Requires three scripts:
echo_flask_sonos.py
echo_check_no_mqtt.py
sonos_echo_app.py

Also need ngrok http 5000
and url will look like 1234.ngrok.io/sonos
it is set on Alexa configuration page
Generic program to use Flask to be the https echo endpoint
'''
from flask import Flask, request
from flask_ask import Ask, statement
import json
from time import time, sleep
import sys
import os
#import random
from operator import itemgetter 
#from decimal import Decimal
import pysolr
#import requests
from multiprocessing.connection import Client 
from config import solr_uri, user_id #,last_fm_api_key, user_id

home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + sys.path
import soco
from soco import config as soco_config
soco_config.CACHE_ENABLED = False

app = Flask(__name__)
app.config['ASK_VERIFY_REQUESTS'] = False
ask = Ask(app, '/sonos')

address = ('localhost', 6000)
conn = Client(address, authkey='secret password')

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

print "\nConnected to Sonos\n"

#last.fm 
base_url = "http://ws.audioscrobbler.com/2.0/"

appVersion = '1.0'

solr = pysolr.Solr(solr_uri+'/solr/sonos_companion/', timeout=10) #port 8983 is incorporated in the ngrok url

meta_format_pandora = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="OOOX52876609482614338" parentID="0" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

meta_format_radio = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="-1" parentID="-1" restricted="true"><dc:title>{title}</dc:title><upnp:class>object.item.audioItem.audioBroadcast</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">{service}</desc></item></DIDL-Lite>'''

#uri = "x-sonos-http:amz%3atr%3a6b5d9c09-7dbe-44bc-89e1-85ac5ed45093.mp3?sid=26&flags=8224&sn=1",
#id_ = "amz%3atr%3a6b5d9c09-7dbe-44bc-89e1-85ac5ed45093
didl_amazon = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="00030020{id_}" parentID="" restricted="true"><dc:title></dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON6663_X_#Svc6663-0-Token</desc></item></DIDL-Lite>'''

#uri = "radea:Tra.2056353.mp3?sn=3",
#id_ = "2056353
didl_rhapsody = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="RDCPI:GLBTRACK:Tra.{id_}" parentID="-1" restricted="true"><dc:title></dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">''' + '''SA_RINCON1_{}</desc></item></DIDL-Lite>'''.format(user_id)

#uri = "x-sonos-http:library%2fartists%2fAmanda%252520Shires%2fCarrying%252520Lightning%2fca20888a-1a68-484a-ac90-058e53b13084%2f.mp4?sid=201&flags=8224&sn=5"
#id_ = "library%2fartists%2fAmanda%252520Shires%2fCarrying%252520Lightning%2fca20888a-1a68-484a-ac90-058e53b13084%2f"
didl_library = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="00032020{id_}" parentID="" restricted="true"><dc:title></dc:title><upnp:class>object.item.audioItem.musicTrack</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON51463_X_#Svc51463-0-Token</desc></item></DIDL-Lite>'''

#uri = "x-rincon-cpcontainer:0006206clibrary%2fplaylists%2f7c7704e9-04b6-431a-afe6-c5db44cb77f1%2f%23library_playlist"
#id_ = "0006206clibrary%2fplaylists%2f7c7704e9-04b6-431a-afe6-c5db44cb77f1%2f%23library_playlist"
#for playlists metadata does not need to include any value for title or parent but unlike tracks, you do need to pass the uri to add_playlist_to_queue
#for the record for An Unarmorial Age, the parentID was "00082064library%2fplaylists%2f%23library_playlists"
didl_library_playlist = '''<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-com:metadata-1-0/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="{id_}" parentID="" restricted="true"><dc:title></dc:title><upnp:class>object.container.playlistContainer</upnp:class><desc id="cdudn" nameSpace="urn:schemas-rinconnetworks-com:metadata-1-0/">SA_RINCON51463_X_#Svc51463-0-Token</desc></item></DIDL-Lite>'''

with open('stations') as f:
    z = f.read()

STATIONS = json.loads(z)

#@ask.intent('HelloIntent')
#def hello(firstname):
#    text = render_template('hello', firstname=firstname)
#    return statement(text).simple_card('Hello', text)

def my_add_to_queue(uri, metadata):
    response = master.avTransport.AddURIToQueue([
            ('InstanceID', 0),
            ('EnqueuedURI', uri), #x-sonos-http:library ...
            ('EnqueuedURIMetaData', metadata),
            ('DesiredFirstTrackNumberEnqueued', 0),
            ('EnqueueAsNext', 1)
            ])
    qnumber = response['FirstTrackNumberEnqueued']
    return int(qnumber)

@ask.intent('PlayAlbum', mapping={'album':'myalbum', 'artist':'myartist'})
def play_album(album, artist):
    # album must be present; artist is optional

    print "album =",album
    print "artist=",artist

    if album:
        s = 'album:' + ' AND album:'.join(album.split())
        if artist:
            s = s + ' artist:' + ' AND artist:'.join(artist.split())

        result = solr.search(s, fl='score,track,uri,album', sort='score desc', rows=25) #**{'rows':25}) #only brings back actual matches but 25 seems like max for most albums
        tracks = result.docs
        if  tracks:
            selected_album = tracks[0]['album']
            try:
                tracks = sorted([t for t in tracks],key=itemgetter('track'))
            except KeyError:
                pass
            # The if t['album']==selected_album only comes into play if we retrieved more than one album
            uris = [t['uri'] for t in tracks if t['album']==selected_album]

            conn.send({'action':'play', 'uris':uris})

            ######################################################################
            #master.stop()
            #master.clear_queue()

            #for uri in uris:
            #    print 'uri: ' + uri
            #    print "---------------------------------------------------------------"
            #    playlist = False
            #    if 'library_playlist' in uri:
            #        i = uri.find(':')
            #        id_ = uri[i+1:]
            #        meta = didl_library_playlist.format(id_=id_)
            #        playlist = True
            #    elif 'library' in uri:
            #        i = uri.find('library')
            #        ii = uri.find('.')
            #        id_ = uri[i:ii]
            #        meta = didl_library.format(id_=id_)
            #    else:
            #        print 'The uri:{}, was not recognized'.format(uri)
            #        continue

            #    print 'meta: ',meta
            #    print '---------------------------------------------------------------'

            #    my_add_to_queue('', meta)

            #master.play_from_queue(0)

            output_speech = "Using Flask Ask, I will play {} songs from {}".format(len(uris), selected_album)
            #end_session = True
        else:
            output_speech = "I couldn't find any songs from album {}. Try again.".format(album)
            #end_session = False

    else:
        output_speech = "I couldn't even find the album. Try again."
        #end_session = False

    #response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':end_session}
    return statement(output_speech)

try:
    app.run(debug=True,
            port=5000,
            threaded=False,
            use_reloader=False,
            use_debugger=True,
            host='0.0.0.0'
            )
finally:
    print "Disconnecting clients"

print "Done"

