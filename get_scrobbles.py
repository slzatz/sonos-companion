import os
import sys
import requests
import config as c
from time import sleep
#last.fm - using for scrobble information, can also be used for artist bios 
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'twitter')] + sys.path
from twitter import *
base_url = "http://ws.audioscrobbler.com/2.0/"
api_key = c.last_fm_api_key 

# twitter
oauth_token = c.twitter_oauth_token 
oauth_token_secret = c.twitter_oauth_token_secret
CONSUMER_KEY = c.twitter_CONSUMER_KEY
CONSUMER_SECRET = c.twitter_CONSUMER_SECRET
tw = Twitter(auth=OAuth(oauth_token, oauth_token_secret, CONSUMER_KEY, CONSUMER_SECRET))

def get_scrobble_info():
    
    payload = {'method':'user.getRecentTracks', 'user':'slzatz2', 'format':'json', 'api_key':api_key}
    
    try:
        r = requests.get(base_url, params=payload)
        
        z = r.json()['recenttracks']['track']
        return z

    except Exception as e:
        print "Exception in get_scrobble_info: ", e
        return [{'name':None}]

prev_name = ''

while 1:
    z = get_scrobble_info()
    d = z[0]
    if d['name'] != prev_name and d['name'] is not None:
        try:
            print d['album']['#text']
        except:
            print "No album"
        print d['name']
        print d['artist']['#text']
        print "\n\n"
        prev_name = d['name']

        tw.direct_messages.new(user='slzatz', text=d['artist']['#text']+'\n'+d['name'])
    sleep(10)


    
