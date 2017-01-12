'''
This script can be run from anywhere.  It gets to the local sonos network via ngrok URLs.  So, for example,
you can see what is playing at any given moment in either NYC or CT by just typing "what."

Below are the keywords that can be entered at the command line that are mapped to Amazon Intents 
in flask_ask_sonos.py, which in turn calls flask_ask_zmq.py via zmq.

louder,quieter->TurnTheVolume
album->PlayAlbum 
pause->AMAZON.PauseIntent 
resume->AMAZON.ResumeIntent
next->AMAZON.NextIntent
shuffle->Shuffle
radio->PlayStation
what->WhatIsPlaying
list or show->ListQueue
clear->ClearQueue
mix {a} and {b}->Mix
add {a}->AddTrack
recent->RecentTracks
everything else assumed to be the title of a track -> PlayTrack
'''
import requests
import sys
from config import ngrok_urls

location = input("Where are you(ct or nyc)? ")
url = ngrok_urls.get(location)
if not url:
    sys.exit()

slots = {'Mix':['myartista','myartistb'], 'Shuffle':['myartist'], 'PlayStation':['mystation'], 'PlayAlbum':['myalbum', 'myartist'], 'PlayTrack':['mytitle', 'myartist'], 'AddTrack':['mytitle', 'myartist'], 'TurnTheVolume':['volume'], 'AMAZON.ResumeIntent':[], 'AMAZON.PauseIntent':[], 'AMAZON.NextIntent':[], 'ListQueue':[],'ClearQueue':[], 'WhatIsPlaying':[], 'RecentTracks':[], 'Mute':[], 'UnMute':[]}

while 1:
    try:
        ask = input("What do you want Sonos to do now? ")
        words = ask.lower().split()

        if 'play' in words:
            words.remove('play')

        if 'louder' in words:
            intent = 'TurnTheVolume'
            values = ['up']
        elif 'quieter' in words:
            intent = 'TurnTheVolume'
            values = ['down']
        elif 'pause' in words:
            intent = 'AMAZON.PauseIntent'
        elif 'resume' in words:
            intent = 'AMAZON.ResumeIntent'
        elif 'next' in words or 'skip' in words:
            intent = 'AMAZON.NextIntent'
        elif 'show' in words or 'list' in words:
            intent = 'ListQueue'
        elif 'clear' in words:
            intent = 'ClearQueue'
        elif 'what' in words:
            intent = 'WhatIsPlaying'
        elif 'recent' in words:
            intent = 'RecentTracks'
        elif 'mute' in words:
            intent = 'Mute'
        elif 'un mute' in words or 'un-mute' in words or 'unmute' in words:
            intent = 'UnMute'
        elif 'shuffle' in words:
            intent = 'Shuffle'
            words.remove('shuffle')
            values = [" ".join(words)]
        elif 'mix' in words:
            intent = 'Mix'
            words.remove('mix')
            if 'and' in words:
                words = " ".join(words)
            if ' and ' in words:
                values = words.split(' and ')
            else:
                values = [words,"neil young"]
        elif 'radio' in words or 'station' in words:
            intent = 'PlayStation'
            if 'radio' in words:
                words.remove('radio')
            if 'station' in words:
                words.remove('station')
            values = [" ".join(words)]
        elif 'album' in words:
            intent = 'PlayAlbum'
            words.remove('album')
            if 'by' in words:
                words = " ".join(words)
                values = words.split(' by ')
                #indx = words.index('by')
                #value0 = " ".join(words[:indx])
                #value1 = " ".join(words[indx+1:])
            else:
                value = " ".join(words)
                values = [value,'']
            #values = [" ".join(words)]
        else:
            if 'add' in words:
                intent = 'AddTrack'
                words.remove('add')
            else:
                intent = 'PlayTrack'

            if 'by' in words:
                words = " ".join(words)
                values = words.split(' by ')
                #indx = words.index('by')
                #value0 = " ".join(words[:indx])
                #value1 = " ".join(words[indx+1:])
            else:
                value = " ".join(words)
                values = [value,'']

        #print("intent = {}".format(intent).encode('cp1252', errors='ignore'))

        slot_dict = {}
        for i,slot in enumerate(slots[intent]):
            s = {slot:{'name':slot, 'value':values[i]}}
            slot_dict.update(s)
            #print("value = {}".format(values[i]).encode('cp1252', errors='ignore'))

        data = {'session':{}, 'request':{'type':'IntentRequest', 'intent':{'slots':slot_dict, 'name':intent}}}
        #print("data= {}".format(data).encode('cp1252', errors='ignore'))
        r = requests.post(url, json=data)
        #print(r.text)
        print("-->", r.json()['response']['outputSpeech']['text'])
    except KeyboardInterrupt:
        sys.exit()
