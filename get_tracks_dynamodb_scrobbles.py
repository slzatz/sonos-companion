'''
uses boto3
This program was used to test whether when you scrobble songs to dynamodb that they
could be picked up by using boto3 to check on them

rrr = table.scan(Limit=10, FilterExpression=Attr("ts").gt(Decimal(z)-1000000))
rrr
{u'Count': 1, u'Items': [{u'album': u'I Carry Your Heart With Me (c)', u'artist': u'Hem', u'title': u'The Part Where You Let Go', 
u'ts': Decimal('1445364875'), u'date': u'2007 - Home
 Again, Home Again', u'scrobble': u'27'}], u'LastEvaluatedKey': {u'ts': Decimal('1442178047'), u'artist': u'Leo Kottke'}, 
u'ScannedCount': 10, 'ResponseMetadata': {'HTTPStatusCode':
200, 'RequestId': 'P3U632LF4NKTGP6MEJ228MLRDBVV4KQNSO5AEMVJF66Q9ASUAAJG'}}

if there are not results:
{u'Count': 0, u'Items': [], u'LastEvaluatedKey': {u'ts': Decimal('1442178047'), u'artist': u'Leo Kottke'}, u'ScannedCount': 10, 
'ResponseMetadata': {'HTTPStatusCode': 200, 'RequestId
': '2UVLSDD8147256OV6P0T03IBV7VV4KQNSO5AEMVJF66Q9ASUAAJG'}}
'scrobble_new
'''

import json
import boto3
from boto3.dynamodb.conditions import Attr, Key
from decimal import Decimal
from time import time
from datetime import datetime, timedelta
import requests
import config as c

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('amazon_music')

#lastfm scrobbles
scrobbler_base_url = "http://ws.audioscrobbler.com/2.0/"
lastfm_api_key = c.last_fm_api_key 

def get_scrobble_info(artist, track, username='slzatz', autocorrect=True):
    
    payload = {'method':'track.getinfo',
               'artist':artist, 'track':track,
               'autocorrect':autocorrect,
               'format':'json', 'api_key':lastfm_api_key,
               'username':username}
    
    try:
        r = requests.get(scrobbler_base_url, params=payload)
        z = r.json()['track']['userplaycount']
        return z # will need to be converted to integer when sent to SQS
    except Exception as e:
        print("Exception in get_scrobble_info: ", e)
        return '-1' # will need to be converted to integer when sent to SQS

z = time()
result = table.scan()

if result['Count']:

    #artists = {}
    #for track in result['Items']:
    #    artists[track.get('artist', 'Missing')] = 1
    #for artist in sorted(artists.keys()):
    #    try:
    #        print("{}".format(artist)) 
    #    except (UnicodeDecodeError, UnicodeEncodeError):
    #        print("Unicode error")
    #
    #titles = {}
    #for track in result['Items']:
    #    titles[track.get('title', 'Missing')] = 1

    #for title in sorted(titles.keys()):
    #    try:
    #        print("{}".format(title)) 
    #    except (UnicodeDecodeError, UnicodeEncodeError):
    #        print("Unicode error")
    

    #d = {}
    #for track in result['Items']:
    #    artist = track.get('artist', '')
    #    title = track.get('title', '')
    #    if artist and title:
    #        scrobble = int(get_scrobble_info(artist, title))
    #    else:
    #        scrobble = -1
    #    #d[artist + "'s " + title] = scrobble
    #    d[title] = scrobble

    #f =  open('titles', 'w')
    #for w in sorted(d, key=d.get, reverse=True):
    #    try:
    #        #s = "{}    {}\n".format(w, d[w])
    #        #s = "Track play {{{}|tracktitle}}\n".format(w)
    #        s = "{}\n".format(w)
    #        f.write(s)
    #        #print("{}    {}".format(w, d[w]))
    #        print(s)
    #    except Exception:
    #        print("Unicode error")

    #f.close()

    if 1: # albums in scrobble order
        d = {}
        for track in result['Items']:
            artist = track.get('artist', '')
            title = track.get('title', '')
            album = track.get('album','')
            if artist and title:
                scrobble = int(get_scrobble_info(artist, title))
            else:
                scrobble = -1
            if album not in d:
                d[album] = scrobble
            else:
                if scrobble > 0:
                    d[album] = d[album] + scrobble

        f =  open('album2', 'w')
        for w in sorted(d, key=d.get, reverse=True):
            try:
                s = "{}\n".format(w)
                f.write(s)
                print(s)
            except Exception:
                print("Unicode error")

        f.close()

    if 0: # artists in scrobble order
        d = {}
        for track in result['Items']:
            artist = track.get('artist', '')
            title = track.get('title', '')
            if artist and title:
                scrobble = int(get_scrobble_info(artist, title))
            else:
                scrobble = -1
            if artist not in d:
                d[artist] = scrobble
            else:
                if scrobble > 0:
                    d[artist] = d[artist] + scrobble

        f =  open('artist', 'w')
        for w in sorted(d, key=d.get, reverse=True):
            try:
                s = "{}\n".format(w)
                f.write(s)
                print(s)
            except Exception:
                print("Unicode error")

        f.close()

