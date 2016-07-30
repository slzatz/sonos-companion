'''
Below is the relationship between words entered at the command line and Amazon Intents (similar to Alexa mapping)
louder,quieter->TurnTheVolume
album->PlayAlbum, 
pause->AMAZON.PauseIntent, 
resume->AMAZON.ResumeIntent, 
shuffle->Shuffle,
radio->PlayStation
everything else assumed to be the title of a track -> PlayTrack
'''
import requests
import sys
from config import ngrok_urls

location = input("Where are you? (ct or nyc) ?")
url = ngrok_urls.get(location)
if not url:
    sys.exit()

slots = {'Shuffle':['myartist'], 'PlayStation':['mystation'], 'PlayAlbum':['myalbum'], 'PlayTrack':['mytitle', 'myartist'], 'TurnTheVolume':['volume'], 'AMAZON.ResumeIntent':[], 'AMAZON.PauseIntent':[]}

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
        elif 'shuffle' in words:
            intent = 'Shuffle'
            words.remove('shuffle')
            values = [" ".join(words)]
        elif 'radio' in words:
            intent = 'PlayStation'
            words.remove('radio')
            values = [" ".join(words)]
        elif 'album' in words:
            intent = 'PlayAlbum'
            words.remove('album')
            values = [" ".join(words)]
        else:
            if 'by' in words:
                indx = words.index('by')
                value0 = " ".join(words[:indx])
                value1 = " ".join(words[indx+1:])
            else:
                value0 = " ".join(words)
                value1 = ''

            values = [value0,value1]
            intent = 'PlayTrack'

        #print("intent = {}".format(intent).encode('cp1252', errors='ignore'))

        slot_dict = {}
        for i,slot in enumerate(slots[intent]):
            s = {slot:{'name':slot, 'value':values[i]}}
            slot_dict.update(s)
            #print("value = {}".format(values[i]).encode('cp1252', errors='ignore'))

        data = {'session':{}, 'request':{'type':'IntentRequest', 'intent':{'slots':slot_dict, 'name':intent}}}
        print("data= {}".format(data).encode('cp1252', errors='ignore'))
        r = requests.post(url, json=data)
        print(r.text)
    except KeyboardInterrupt:
        sys.exit()
