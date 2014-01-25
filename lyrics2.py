
import requests
import argparse
import json
import lxml.html

parser = argparse.ArgumentParser()
parser.add_argument("artist")
parser.add_argument("title")
args = parser.parse_args()


def get_lyrics(artist, title):
    payload = {'func': 'getSong', 'artist': artist, 'song': title, 'fmt': 'realjson'}
    r = requests.get("http://lyrics.wikia.com/api.php", params=payload)
    return r

def get_album_year(artist, album):
    payload = {'func': 'getAlbum', 'artist': artist, 'album': album, 'fmt': 'realjson'}
    r = requests.get("http://lyrics.wikia.com/api.php", params=payload)
    return r

def get_full_lyrics(url):
    """Get and return the lyrics for the given song.
    Raises an IOError if the lyrics couldn't be found.
    Raises an IndexError if there is no lyrics tag.
    Returns False if there are no lyrics (it's instrumental)."""

    try:
        #doc = lxml.html.parse(lyricwikiurl(artist, title, fuzzy=fuzzy))
        doc = lxml.html.parse(url)
    except IOError:
        raise

    try:
        lyricbox = doc.getroot().cssselect(".lyricbox")[0]
        
    except IndexError:
        raise

    # look for a sign that it's instrumental
    if len(doc.getroot().cssselect(".lyricbox a[title=\"Instrumental\"]")):
        return False

    # prepare output
    lyrics = []
    if lyricbox.text is not None:
        lyrics.append(lyricbox.text)
    for node in lyricbox:
        if str(node.tag).lower() == "br":
            lyrics.append("\n")
        if node.tail is not None:
            lyrics.append(node.tail)
    return "".join(lyrics).strip()


if __name__ == '__main__':
    artist = args.artist
    title = args.title
    z = get_lyrics(artist,title)	
    #print z
    #print z.url
    print z.json()
    #print z.text
    #print z.json()
    #q = json.loads(z.text)
    #q = json.loads(z.text[7:])
    #q = eval(z.text[7:])
    #print q
    #print type(q)
    #print "url=",q['url']
	
    #zz = get_full_lyrics(q['url'])
    #print zz

    #zzz = get_album_year(artist,title)
    #print zzz.json()
#http://lyrics.wikia.com/api.php?func=getSong&artist=Tool&song=Schism&fmt=xml


