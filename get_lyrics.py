'''(barely) modified from script by Will Soares'''

import sys
import json
import requests
import re
from bs4 import BeautifulSoup
from config import genius_token

api_url = "https://api.genius.com"

def search_db(title, artist):
    headers = {'Authorization': 'Bearer ' + genius_token}
    search_url = api_url + '/search'

    #remove () or [] which seem to sometimes confuse lyric search
    q = re.sub("[\(\[].*?[\)\]]", "", title + ' ' + artist)
    # slz addition - explicit is fine but maybe some songs have live as a legitimate word
    q = q.replace("Explicit", "").replace("Live", "")
    q = q.strip()

    print(f"{search_url=}; {q=}")

    try:
        response = requests.get(search_url, data={'q':q}, headers=headers)
    except Exception as e:
        print(f"Exception searching genius db for {title} by {artist}")
        return

    return response

def retrieve_lyrics_old(url): #09232021
    try:
        page = requests.get(url)
    except Exception as e:
        print(f"Exception retrieving page for {title} by {artist}")
        return

    # 2 lines below taken from https://github.com/johnwmillr/LyricsGenius/
    html = BeautifulSoup(page.text.replace('<br/>', '\n'), 'html.parser')
    div = html.find('div', class_=re.compile("^lyrics$|Lyrics__Root")) #changed 05112021

    if div is None:
        return 

    lyrics = div.get_text()
    lyrics = re.sub("[\(\[].*?[\)\]]", "", lyrics) # genius has verse and chorus in brackets

    return lyrics.lstrip()

def retrieve_lyrics(url):
    try:
        page = requests.get(url).text
    except Exception as e:
        print(f"Exception retrieving page for {title} by {artist}")
        return

    m = re.search(r'window\.__PRELOADED_STATE__ = JSON\.parse(.*)', page)
    if m is None:
        print(m)
        return

    data = m.group(1)
    data = data[2:-3]
    data = data.replace("\\", "")
    print(data)
    data = json.loads(data)
    lyrics = data["songPage"]["lyricsData"]["body"]["html"]
    lyrics = lyrics.replace("<br>n", "\n")
    return lyrics[3:]

def get_lyrics2(artist, title, display=False):

    #print('{} by {}'.format(title, artist))

    # Search for matches in request response
    response = search_db(title, artist)
    if response is None:
        print("No Response")
        return

    z = response.json()
    print(z)
    match = False

    for hit in z['response']['hits']:
        if artist.lower() in hit['result']['primary_artist']['name'].lower():
            match = True
            break

    # Extract lyrics from URL if song was found
    if match:
        url = hit['result']['url']
        lyrics = retrieve_lyrics(url)

        # started showing up in lyrics 07092021
        lyrics = lyrics.replace("EmbedShare", "")
        lyrics = lyrics.replace("URLCopyEmbedCopy", "")

        #write_lyrics_to_file(lyrics, song_title, artist_name)

        if display:
            print(lyrics)
        return lyrics
    else:
        if display:
            print("could not find (genius) lyrics")
        return

def get_lyrics(artist, title, display=False):
    url = "https://genius.com/"+artist+"-"+title+"-"+"lyrics"
    lyrics = retrieve_lyrics(url)
    print(lyrics)

# not in use
def write_lyrics_to_file (lyrics, song, artist):
    f = open('lyric-view.txt', 'w')
    f.write('{} by {}'.format(song, artist))
    f.write(lyrics)
    f.close()

if __name__ == '__main__':

    # Use input as song title and artist name
     title = sys.argv[1]
     artist = sys.argv[2]
     print(f"{title=}; {artist=}")
     get_lyrics(artist, title, True)


