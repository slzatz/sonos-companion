'''
Program that pulls recent tracks from last.fm
Problem is that it counts the scrobbles from all time not for whatever period you are looking at
'''
import os
#import sys
import requests
import config as c
from time import sleep
#last.fm 
base_url = "http://ws.audioscrobbler.com/2.0/"
api_key = c.last_fm_api_key 

def get_top_tracks():
    payload = {'method':'user.getTopTracks', 'user':'slzatz', 'period':'1month', 'limit':5, 'format':'json', 'api_key':api_key}
    
    try:
        r = requests.get(base_url, params=payload)
        z = r.json()['toptracks']['track']
        return z

    except Exception as e:
        print("Exception in get_top_tracks: ", e)
        return []

z = get_top_tracks()
#could get the track number in the period with user.getArtistTracks but probably not worth it
tracks = sorted([t for t in z],key=lambda t:int(t['@attr']['rank']))
#print z
for d in tracks:
    print(d['name'])
    print(d['artist']['name'])
    print(d['playcount'])
    #print "\n"

