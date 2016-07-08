'''
uses mqtt - idea which may be wrong is that it produces a response faster because
not waiting for echo_check_no_mqtt.sonos_action to return before providing response to echo 

Requires three scripts:
echo_flask_sonos.py
echo_check_mqtt.py - needs to be running - right now checking ec2 mqtt broker
sonos_echo_app_mqtt.py

Also need ngrok http 5000
and url will look like 1234.ngrok.io/sonos
it is set on Alexa configuration page
Requires pysolr.py, config.py, requests - note pysolr.py needs requests
Below are the Alexa intents
PlayStation play {mystation} radio
PlayStation play {mystation} pandora
PlayStation play {mystation} station
PlayTrack play {mytitle} by {myartist}
PlayTrack play {mytitle}
AddTrack add {mytitle} by {myartist}
AddTrack add {mytitle}
AddTrack add {mytitle} to the queue
AddTrack add {mytitle} by {myartist} to the queue
Shuffle shuffle {myartist}
Shuffle play some {myartist}
Shuffle play some music from {myartist}
SetShuffleNumber Set shuffle number to {mynumber}
GetShuffleNumber What is the shuffle number
WhatIsPlaying what is playing
WhatIsPlaying what song is playing
Skip skip
Skip next
Skip skip song
Skip next song
PlayAlbum play album {myalbum}
PlayAlbum play the album {myalbum}
AddAlbum add album {myalbum}
AddAlbum add the album {myalbum}
PauseResume {pauseorresume} the music
PauseResume {pauseorresume} the radio
PauseResume {pauseorresume} sonos
TurnTheVolume Turn the volume {volume}
TurnTheVolume Turn {volume} the volume
SetLocation Set location to {location}
SetLocation I am in {location}
GetLocation Where am I
GetLocation What is the location
'''
import json
import random
from operator import itemgetter 
from decimal import Decimal
import time
import pysolr
import requests
import paho.mqtt.publish as mqtt_publish
#import paho.mqtt.client as mqtt #################################
from config import ec_uri, last_fm_api_key, location

#last.fm 
base_url = "http://ws.audioscrobbler.com/2.0/"

appVersion = '1.0'

solr = pysolr.Solr(ec_uri+':8983/solr/sonos_companion/', timeout=10)
hostname=ec_uri[7:]

def lambda_handler(event, context=None):
    session = event['session']
    request = event['request']
    requestType = request['type']
	
    if requestType == "LaunchRequest":
        response = launch_request(session, request)
    elif requestType == "IntentRequest":
        response = intent_request(session, request)
    else:
        output_speech = "I couldn't tell which type of request that was.  Try again."
        response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':False}

    print json.dumps(response) 

    return {"version":appVersion,"response":response}

def launch_request(session, request):
    output_speech = "Welcome to Sonos. Some things you can do are: Select Neil Young radio or Shuffle Neil Young or Play After the Gold Rush or ask what is playing or skip, louder, quieter"
    response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':False}
    return response

def intent_request(session, request):

    intent = request['intent']['name']
    print "intent_request: {}".format(intent)

    if intent ==  "PlayStation":

        station = request['intent']['slots']['mystation']['value']
        #send_sqs(action='radio', station=station)
        mqtt_publish.single('sonos/'+location, json.dumps(dict(action='radio', station=station)), hostname=hostname, retain=False, port=1883, keepalive=60)

        output_speech = station + " radio will start playing soon"
        response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':True}
        return response

    elif intent ==  "PlayAlbum" or intent == "AddAlbum":

        album = request['intent']['slots']['myalbum'].get('value', '')
        print "album =",album
        if album:
            s = 'album:' + ' AND album:'.join(album.split())
            result = solr.search(s, fl='score,track,uri,album', sort='score desc', rows=25) #**{'rows':25}) #only brings back actual matches but 25 seems like max for most albums
            if  result.docs:
                selected_album = result.docs[0]['album']
                tracks = sorted([t for t in result.docs],key=itemgetter('track'))
                # The if t['album']==selected_album only comes into play if we retrieved more than one album
                uris = [t['uri'] for t in tracks if t['album']==selected_album]
                action = 'play' if intent=="PlayAlbum" else 'add'
                #send_sqs(action=action, uris=uris)
                mqtt_publish.single('sonos/'+location, json.dumps(dict(action=action, uris=uris)), hostname=hostname, retain=False, port=1883, keepalive=60)
                output_speech = "I will play {} songs from {}".format(len(uris), selected_album)
                end_session = True
            else:
                output_speech = "I couldn't find {}. Try again.".format(album)
                end_session = False

        else:
            output_speech = "I couldn't find the album. Try again."
            end_session = False

        response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':end_session}
        return response

    elif intent == "PlayTrack" or intent == "AddTrack":
        # title must be present; artist is optional

        artist = request['intent']['slots']['myartist'].get('value', '')
        title = request['intent']['slots']['mytitle'].get('value', '')
        print "artist =",artist
        print "title =",title

        if title:
            s = 'title:' + ' AND title:'.join(title.split())
            if artist:
                s = s + ' artist:' + ' AND artist:'.join(artist.split())

            result = solr.search(s, rows=1) #**{'rows':1})
            if len(result):
                track = result.docs[0]
                action = 'play' if intent=="PlayTrack" else 'add'
                #send_sqs(action=action, uris=[track['uri']])
                mqtt_publish.single('sonos/'+location, json.dumps(dict(action=action, uris=[track['uri']])), hostname=hostname, retain=False, port=1883, keepalive=60)

                output_speech = "I will play {} by {} from album {}".format(track['title'], track['artist'], track['album'])
                end_session = True
            else:
                output_speech = "I couldn't find the song {} by {}. Try again.".format(title,artist)
                end_session = False
        else:
            output_speech = "I couldn't find the song. Try again."
            end_session = False

        response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':end_session}
        return response

    elif intent ==  "Shuffle":

        shuffle_number = 10

        artist = request['intent']['slots']['myartist'].get('value')
        if artist:
            s = 'artist:' + ' AND artist:'.join(artist.split())
            result = solr.search(s, fl='uri', rows=500) 
            count = len(result)
            if count:
                print "Total track count for {} was {}".format(artist, count)
                tracks = result.docs
                k = shuffle_number if shuffle_number <= count else count
                uris = []
                for j in range(k):
                    while 1:
                        n = random.randint(0, count-1) if count > shuffle_number else j
                        uri = tracks[n]['uri']
                        if not uri in uris:
                            uris.append(uri)
                            break

                #send_sqs(action='play', uris=uris)
                mqtt_publish.single('sonos/'+location, json.dumps(dict(action='play', uris=uris)), hostname=hostname, retain=False, port=1883, keepalive=60)
                output_speech = "I will play {} songs by {}.".format(shuffle_number, artist)
                end_session = True
            else:
                output_speech = "The artist {} didn't have any songs.".format(artist)
                end_session = False
        else:
            output_speech = "I couldn't find the artist you were looking for. Try again."
            end_session = False

        response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':end_session}
        return response

    elif intent ==  "Deborah": # not in use

        number = request['intent']['slots']['number']['value']
        #send_sqs(action='deborah', number=number)
        mqtt_publish.single('sonos/'+location, json.dumps(dict(action='deborah', number=number)), hostname=hostname, retain=False, port=1883, keepalive=60)

        output_speech = "I will play " + str(number) + " of Deborah's albums"
        response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':True}
        return response

    #elif intent == "WhatIsPlaying":

    #    s3 = boto3.client('s3')
    #    response = s3.get_object(Bucket='sonos-scrobble', Key='location')
    #    body = response['Body']
    #    location = body.read()
    #    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    #    table = dynamodb.Table('scrobble_new')
    #    result = table.query(KeyConditionExpression=Key('location').eq(location), ScanIndexForward=False, Limit=1) #by default the sort order is ascending

    #    if result['Count']:
    #        track = result['Items'][0]
    #        if track['ts'] > Decimal(time.time())-300:
    #            output_speech = "The song is {}. The artist is {} and the album is {}.".format(track.get('title','No title'), track.get('artist', 'No artist'), track.get('album', 'No album'))
    #        else:
    #            output_speech = "Nothing appears to be playing right now, Steve"
    #    else:
    #        output_speech = "It appears that nothing has ever been scrobbled"

    #    response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':True}
    #    return response

    elif intent == "RecentTracks":
        # right now look back is one week; note can't limit because you need all the tracks since we're doing the frequency count
        payload = {'method':'user.getRecentTracks', 'user':'slzatz', 'format':'json', 'api_key':last_fm_api_key, 'from':int(time.time())-604800} #, 'limit':10}
        
        try:
            r = requests.get(base_url, params=payload)
            z = r.json()['recenttracks']['track']
        except Exception as e:
            print "Exception in get_scrobble_info: ", e
            z = []

        if z:
            dic = {}
            for d in z:
                dic[d['album']['#text']+'_'+d['name']] = dic.get(d['album']['#text']+'_'+d['name'],0) + 1

            a = sorted(dic.items(), key=lambda x:(x[1],x[0]), reverse=True) 

            current_album = ''
            output_speech = "During the last week you listened to the following tracks"
            # if you wanted to limit the number of tracks that were reported on, could do it here
            for album_track,count in a: #[:10]
                album,track = album_track.split('_')
                if current_album == album:
                    line = ", {} ".format(track)
                else:
                    line = ". From {}, {} ".format(album,track)
                    current_album = album
                
                if count==1:
                    count_phrase = ""
                elif count==2:
                    count_phrase = "twice"
                else:
                    count_phrase = str(count)+" times"

                output_speech += line + count_phrase

        else:
            output_speech = "I could  not retrieve recently played tracks or there aren't any."

        response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':True}
        return response

    elif intent == "AMAZON.NextIntent":
        #send_sqs(action='skip')
        mqtt_publish.single('sonos/'+location, json.dumps(dict(action='skip')), hostname=hostname, retain=False, port=1883, keepalive=60)
        response = {'outputSpeech': {'type':'PlainText','text':'skipped'},'shouldEndSession':True}
        return response

    elif intent == "AMAZON.PreviousIntent":
        #send_sqs(action='previous')
        mqtt_publish.single('sonos/'+location, json.dumps(dict(action='previous')), hostname=hostname, retain=False, port=1883, keepalive=60)
        response = {'outputSpeech': {'type':'PlainText','text':'previous'},'shouldEndSession':True}
        return response

    elif intent == "AMAZON.PauseIntent":
        #send_sqs(action='pause')
        mqtt_publish.single('sonos/'+location, json.dumps(dict(action='pause')), hostname=hostname, retain=False, port=1883, keepalive=60)
        response = {'outputSpeech': {'type':'PlainText','text':'I will pause'},'shouldEndSession':True}
        return response

    elif intent == "AMAZON.ResumeIntent":
        #send_sqs(action='resume')
        mqtt_publish.single('sonos/'+location, json.dumps(dict(action='resume')), hostname=hostname, retain=False, port=1883, keepalive=60)
        response = {'outputSpeech': {'type':'PlainText','text':'I will resume'},'shouldEndSession':True}
        return response

    #elif intent == "PauseResume":

    #    pauseorresume = request['intent']['slots']['pauseorresume']['value']

    #    if pauseorresume in ('pause','stop'):
    #        action = 'pause'
    #    elif pauseorresume in ('unpause','resume'):
    #        action = 'resume'
    #    else:
    #        action = None

    #    if action:

    #        send_sqs(action=action)

    #        output_speech = "The music will {}".format(pauseorresume)

    #    else:
    #        output_speech = "I have no idea what you said."

    #    response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':True}
    #    return response

    elif intent == "TurnTheVolume":

        volume = request['intent']['slots']['volume']['value']

        if volume in ('increase','louder','higher','up'):
            action = 'louder'
        elif volume in ('decrease', 'down','quieter','lower'):
            action = 'quieter'
        else:
            action = None

        if action:

            #send_sqs(action=action)
            mqtt_publish.single('sonos/'+location, json.dumps(dict(action=action)), hostname=hostname, retain=False, port=1883, keepalive=60)

            output_speech = "I will make the volume {}".format(action)

        else:
            output_speech = "I have no idea what you said."

        response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':True}
        return response

    else:
        output_speech = "I couldn't tell which type of intent request that was.  Try again."
        response = {'outputSpeech': {'type':'PlainText','text':output_speech},'shouldEndSession':False}
        return response
