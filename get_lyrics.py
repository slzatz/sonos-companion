'''(barely) modified from script by Will Soares'''

import sys
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

    try:
        response = requests.get(search_url, data={'q':q}, headers=headers)
    except Exception as e:
        print(f"Exception searching genius db for {title} by {artist}")
        return

    return response

def retrieve_lyrics(url):
    try:
        page = requests.get(url)
    except Exception as e:
        print(f"Exception retrieving page for {title} by {artist}")
        return
    html = BeautifulSoup(page.text, 'html.parser')
    [h.extract() for h in html('script')]
    lyrics = html.find('div', class_='lyrics').get_text()

    return lyrics

def get_lyrics(artist, title):

    #print('{} by {}'.format(title, artist))

    # Search for matches in request response
    response = search_db(title, artist)
    if response is None:
        return

    z = response.json()
    match = False

    for hit in z['response']['hits']:
        if artist.lower() in hit['result']['primary_artist']['name'].lower():
            match = True
            break

    # Extract lyrics from URL if song was found
    if match:
        url = hit['result']['url']
        lyrics = retrieve_lyrics(url)

        #write_lyrics_to_file(lyrics, song_title, artist_name)

        print(lyrics)
        return lyrics
    else:
        print("could not find (genius) lyrics")
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
     get_lyrics_genius(artist, title)


