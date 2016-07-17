import requests
import sys
from config import ngrok_url as url

intents = {'shuffle':'Shuffle', 'track':"PlayTrack", 'album':'PlayAlbum', 'radio':'PlayStation'}
slots = {'shuffle':'myartist', 'radio':'mystation', 'album':'myalbum', 'track':'mytitle'}

while 1:
    try:
        ask = input("What do you want Sonos to do now? ")
        words = ask.lower().split()
        if 'play' in words:
            words.remove('play')
        if 'shuffle' in words:
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

        print("intent = ", intent)
        print("value = ", value)
        slot_name = slots[intent]
        intent_name = intents[intent]

        slot_dict = ({slot_name:{'name':slot_name, 'value':value}})
        if intent == 'track':
            slot_dict.update({'myartist':{'name':'myartist', 'value':value1}})

        data = {'session':{}, 'request':{'type':'IntentRequest', 'intent':{'slots':slot_dict, 'name':intent_name}}}
        print("data =", data)
        r = requests.post(url, json=data)
        print(r.text)
    except KeyboardInterrupt:
        sys.exit()
