
import requests
import argparse
import json
import musicbrainzngs

parser = argparse.ArgumentParser()
parser.add_argument("artist")
parser.add_argument("album")
args = parser.parse_args()

#Last FM
#API Key: 1c55c0a239072889fa7c11df73ecd566
#Secret: is e749c8504abe182bb1a174e193f91bf6
#http://ws.audioscrobbler.com/2.0/?method=artist.getSimilar&api_key=xxx...
#format=json : A Last.fm API Key.
#http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key=1c55c0a239072889fa7c11df73ecd566&artist=Cher&album=Believe&format=json

base_url = "http://ws.audioscrobbler.com/2.0/"
api_key = "1c55c0a239072889fa7c11df73ecd566"

#I should also check out the musicbrainz api
# Impossible Dream
#u'mbid': u'227ca39a-b7f0-4460-b792-16f81e97dce5', 

musicbrainzngs.set_useragent("Sonos", "0.1", contact="hello")
#musicbrainzngs.set_hostname("http://musicbrainz.org/ws/2/")

#musicbrainzngs.get_recording_by_id(id, includes=[], release_status=[], release_type=[])

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
    
    mbid = z.json()['album']['mbid']
    print mbid
    
    zz = musicbrainzngs.get_release_by_id(mbid)
    
    zzz = musicbrainzngs.search_releases(artist=artist, release=album, limit=5)
    
    print "musicbrinzngs.get_release_by_id(mbid)=",zz
    
    print "musicbrainzngs.search_releases(artist=artist, release=album, limit=5)=",zzz
    
    ddd = zzz['release-list']
    dates = []
    for n in range(5):
         if 'date' in ddd[n]:
             print ddd[n]['date']
             dates.append(ddd[n]['date'][0:4])
             
    else:
        "print no dates"
        
    print dates
    dates.sort()    
    print dates
         

 


