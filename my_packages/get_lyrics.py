'''(barely) modified from script by Will Soares'''

import sys
import json
import requests
import cloudscraper #########################
import re
from .config import api_url

scraper = cloudscraper.create_scraper()

def search_db(title, artist):
    search_url = api_url + '/search'

    #remove () or [] which seem to sometimes confuse lyric search
    q = re.sub("[\(\[].*?[\)\]]", "", title + ' ' + artist)
    # slz addition - explicit is fine but maybe some songs have live as a legitimate word
    q = q.replace("Explicit", "").replace("Live", "")
    q = q.strip()

    #print(f"{search_url=}; {q=}")

    try:
        #response = requests.get(search_url, params={'q':q}, headers=headers)
        #response = requests.get(search_url, params={'q':q})
        response = scraper.get(search_url, params={'q':q})
    except Exception as e:
        print(f"Exception searching db for {title} by {artist}")
        return

    return response

def retrieve_lyrics(url):
    try:
        # for reasons I can't fathom this avoids a cf version 2 challenge!
        page = requests.get(url).text
    except Exception as e:
        return f"Exception retrieving page for\n{url}: {e}"

    m = re.search(r'window\.__PRELOADED_STATE__ = JSON\.parse(.*)', page)
    if m is None:
        return f"Could not scrape\n{url}"

    data = m.group(1)
    data = data[2:-3]
    data = data.replace("\\\\\\", "123456789")
    data = data.replace("\\", "")
    data = data.replace("123456789", "\\")
    data = json.loads(data)
    lyrics = data["songPage"]["lyricsData"]["body"]["html"]
    lyrics = lyrics.replace("<br>n", "\n")
    lyrics = re.sub(r"<a href.*\">", "", lyrics)
    lyrics = lyrics.replace("</a>", "")
    lyrics = re.sub(r"</?p>", "", lyrics)
    return lyrics[:-2]

def get_lyrics(artist, title, display=False):

    #print('{} by {}'.format(title, artist))

    # Search for matches in request response
    response = search_db(title, artist)
    if response is None:
        print("No Response")
        return

    z = response.json()
    #print(z)
    match = False

    # a check on whether song is from the artist we were looking for
    for hit in z['response']['hits']:
        if artist.lower().split()[0] in hit['result']['primary_artist']['name'].lower():
            match = True
            break
    #else:
    #    if z['response']['hits']:
    #        hit = z['response']['hits'][0]
    #        match = True

    # Extract lyrics from URL if song was found
    if match:
        url = hit['result']['url']
        lyrics = retrieve_lyrics(url)

        if display:
            print(lyrics)
        return lyrics
    else:
        if display:
            print("could not find lyrics")
        return

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


