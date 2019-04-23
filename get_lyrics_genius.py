'''(barely) modified from script by Will Soares'''

import sys, requests
from bs4 import BeautifulSoup
from config import genius_token

api_url = "https://api.genius.com"

def request_song_info(song_title, artist_name):
    headers = {'Authorization': 'Bearer ' + genius_token}
    search_url = api_url + '/search'
    print(search_url)
    data = {'q': song_title + ' ' + artist_name}
    print(data)
    response = requests.get(search_url, data=data, headers=headers)

    return response

def scrape_song_url(url):
    page = requests.get(url)
    html = BeautifulSoup(page.text, 'html.parser')
    [h.extract() for h in html('script')]
    lyrics = html.find('div', class_='lyrics').get_text()

    return lyrics

def get_lyrics_genius(artist, title):

    #print('{} by {}'.format(title, artist))

    # Search for matches in request response
    response = request_song_info(title, artist)
    z = response.json()
    remote_song_info = None

    #print(z['response']['hits'])

    for hit in z['response']['hits']:
        if artist.lower() in hit['result']['primary_artist']['name'].lower():
            remote_song_info = hit
            break

    # Extract lyrics from URL if song was found
    if remote_song_info:
        song_url = remote_song_info['result']['url']
        lyrics = scrape_song_url(song_url)

        #write_lyrics_to_file(lyrics, song_title, artist_name)

        print(lyrics)
        return [lyrics]
    else:
        print("could not find (genius) lyrics")
        return None

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


