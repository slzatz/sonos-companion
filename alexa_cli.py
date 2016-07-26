import requests
import sys
from config import ngrok_urls

location = input("Where are you? (ct or nyc) ?")
url = ngrok_urls.get(location)
if not url:
    sys.exit()

intents = {'shuffle':'Shuffle', 'track':"PlayTrack", 'album':'PlayAlbum', 'radio':'PlayStation', 'pause':'AMAZON.PauseIntent', 'resume':'AMAZON.ResumeIntent'}
slots = {'shuffle':'myartist', 'radio':'mystation', 'album':'myalbum', 'track':'mytitle'}

while 1:
    try:
        ask = input("What do you want Sonos to do now? ")
        words = ask.lower().split()

        if 'play' in words:
            words.remove('play')

        if 'pause' in words:
            intent = 'pause'
            value = ''
        elif 'resume' in words:
            intent = 'resume'
            value = ''
        elif 'shuffle' in words:
            words.remove('shuffle')
            value = " ".join(words)
            intent = 'shuffle'
        elif 'radio' in words:
            words.remove('radio')
            value = " ".join(words)
            intent = 'radio'
        elif 'album' in words:
            words.remove('album')
            value = " ".join(words)
            intent = 'album'
        else:
            if 'by' in words:
                indx = words.index('by')
                value = " ".join(words[:indx])
                value1 = " ".join(words[indx+1:])
            else:
                value = " ".join(words)
                value1 = ''

            intent = 'track'

        print("intent = {}".format(intent).encode('cp1252', errors='ignore'))
        print("value = {}".format(value).encode('cp1252', errors='ignore'))
        
        if value:
            slot_name = slots[intent]
            slot_dict = {slot_name:{'name':slot_name, 'value':value}}
            if intent == 'track':
                slot_dict.update({'myartist':{'name':'myartist', 'value':value1}})
        else:
            slot_dict = {}

        intent_name = intents[intent]
        data = {'session':{}, 'request':{'type':'IntentRequest', 'intent':{'slots':slot_dict, 'name':intent_name}}}
        print("data= {}".format(data).encode('cp1252', errors='ignore'))
        r = requests.post(url, json=data)
        print(r.text)
    except KeyboardInterrupt:
        sys.exit()
