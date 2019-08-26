"""
python 3.x
This script gets artists images and lyrics when sonos is playing
Relies on sonos_track_info.py for artist and track

"""
import json
import requests
import lxml.html


def get_url(artist, title):

    if artist is None or title is None:
        return None
    # realjson doesn't seem to be documented but json doesn't work
    payload = {"func": "getSong", "artist": artist, "song": title, "fmt": "realjson"}
    # payload = {'func': 'getSong', 'artist': artist, 'song': title, 'fmt': 'json'}

    try:
        r = requests.get("http://lyrics.wikia.com/api.php", params=payload)
    except:
        print("Problem retrieving lyrics")
        url = None

    else:
        q = r.json()
        url = q["url"] if "url" in q else None

        if url and url.find("action=edit") != -1:
            url = None

    return url


def get_lyrics(artist, title):

    if artist is None or title is None:
        print("No artist or title")
        return None

    # print(artist, title)

    url = get_url(artist, title)
    if not url:
        return None

    try:
        doc = lxml.html.parse(url)
    except IOError as e:
        print(e)
        return None

    try:
        lyricbox = doc.getroot().cssselect(".lyricbox")[0]
    except IndexError as e:
        print(e)
        return None

    # look for a sign that it's instrumental
    if len(doc.getroot().cssselect('.lyricbox a[title="Instrumental"]')):
        print("appears to be instrumental")
        return None

    lyrics = []
    if lyricbox.text is not None:
        lyrics.append(lyricbox.text)
    for node in lyricbox:
        if node.tail is not None:
            lyrics.append(node.tail)

    # for line in lyrics:
    #    print line

    return lyrics
