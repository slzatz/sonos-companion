'''Program that pulls recent tracks from last.fm'''
import os
import sys
import requests
import config as c
from config import last_fm_api_key
import time
#last.fm 
base_url = "http://ws.audioscrobbler.com/2.0/"

def get_scrobble_info():

    payload = {'method':'user.getRecentTracks', 'user':'slzatz', 'format':'json', 'api_key':last_fm_api_key, 'from':int(time.time())-604800}
    
    try:
        r = requests.get(base_url, params=payload)
        z = r.json()['recenttracks']['track']
        return z

    except Exception as e:
        print("Exception in get_scrobble_info: ", e)
        return []

z = get_scrobble_info()

#print z
#dic = {}
#for d in z:
#    dic[d['album']['#text']+'_'+d['name']] = dic.get(d['album']['#text']+'_'+d['name'],0) + 1
#
#print dic
#a = sorted(dic.items(), key=lambda x:x[1], reverse=True) 
#for t in a:
#    print 'album: ' + ', track: '.join(t[0].split('_')),'-',t[1],'plays' if t[1]>1 else 'play'


if z:
    dic = {}
    for d in z:
        dic[d['album']['#text']+'_'+d['name']] = dic.get(d['album']['#text']+'_'+d['name'],0) + 1

    a = sorted(dic.items(), key=lambda x:(x[1],x[0]), reverse=True) 

    current_album = ''
    output_speech = "During the last week you listened to the following tracks"
    for album_track,count in a: #[:5]:
        album,track = album_track.split('_')
        if current_album == album:
            line = ", {}".format(track)
        else:
            line = ". From {}, {}".format(album,track)
            current_album = album
        
        if count==1:
            count_phrase = ""
        elif count==2:
            count_phrase = " twice"
        else:
            count_phrase = " "+str(count)+" times"

        output_speech += line + count_phrase

    print(output_speech)

