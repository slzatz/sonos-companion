import requests
import sys

with open('output.mp3', 'wb') as handle:
    response = requests.get('http://translate.google.com/translate_tts?tl=en&q=%22hello%20boys%22', stream=True)

    if not response.ok:
        sys.exit()

    for block in response.iter_content(1024):
        if not block:
            break

        handle.write(block)


#A soco.data_structures.URI item can be passed to add_to_queue which allows playing music
#from arbitrary URIs (#147)
#import soco
#from soco.data_structures import URI
#soc = soco.SoCo(’...ip_address...’)
#uri = URI(’http://www.noiseaddicts.com/samples/17.mp3’)
#soc.add_to_queue(uri)
############################ this will be a local file not an internet file although it could be if I use my google web site ##################################
#from pydub import AudioSegment
#song = AudioSegment.from_mp3("never_gonna_give_you_up.mp3")
#a = song1 + song2

#a.export("good_morning_message.mp3",format="mp3")
