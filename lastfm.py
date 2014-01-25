
import requests
import argparse
import json
#import lxml.html

parser = argparse.ArgumentParser()
parser.add_argument("artist")
parser.add_argument("album")
args = parser.parse_args()

#API Key: 1c55c0a239072889fa7c11df73ecd566
#Secret: is e749c8504abe182bb1a174e193f91bf6
#http://ws.audioscrobbler.com/2.0/?method=artist.getSimilar&api_key=xxx...
#format=json : A Last.fm API Key.
#http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key=1c55c0a239072889fa7c11df73ecd566&artist=Cher&album=Believe&format=json

base_url = "http://ws.audioscrobbler.com/2.0/"
api_key = "1c55c0a239072889fa7c11df73ecd566"

#I should also check out the musicbrainz api

def get_album_info(artist, album):
    payload = {'method':'album.getinfo', 'artist': artist, 'album': album, 'format': 'json', 'api_key':api_key}
    r = requests.get(base_url, params=payload)
    return r


if __name__ == '__main__':
    artist = args.artist
    album = args.album
    z = get_album_info(artist,album)

    print z.json()['album']['releasedate']
    #print z.json()['album']['wiki']['summary']
    print z.json()
 


