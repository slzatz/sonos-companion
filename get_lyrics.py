'''(barely) modified from script by Will Soares'''

import sys
import json
import requests
import re
#from bs4 import BeautifulSoup
#from config import genius_token

#api_url = "https://api.genius.com"
api_url = "https://genius.com/api"

# as of 09232021 doesn't work
def search_db(title, artist):
    #headers = {'Authorization': 'Bearer ' + genius_token}
    search_url = api_url + '/search'

    #remove () or [] which seem to sometimes confuse lyric search
    q = re.sub("[\(\[].*?[\)\]]", "", title + ' ' + artist)
    # slz addition - explicit is fine but maybe some songs have live as a legitimate word
    q = q.replace("Explicit", "").replace("Live", "")
    q = q.strip()

    #print(f"{search_url=}; {q=}")

    try:
        #response = requests.get(search_url, params={'q':q}, headers=headers)
        response = requests.get(search_url, params={'q':q})
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
        return f"Exception retrieving page for\n{url}"

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

# as of 09232021 not in use
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
            print("could not find (genius) lyrics")
        return

def get_lyrics_too_new(artist, title, display=False):
    artist = artist.capitalize().replace(" ", "-")
    title = title.lower().replace(" ", "-")
    url = f"https://genius.com/{artist}-{title}"
    idx = url.find("live")
    if idx != -1:
        url = url[:idx]
    url = url.strip()
    url = url.replace("'", "")
    url = url.replace(".", "")
    url = url.replace(",", "")
    url = re.sub(r"\([^)]*\)", "", url)
    url = url.replace("--", "-")
    url = url.replace("&", "and")
    url = url.rstrip("-")
    url = url + "-lyrics"

    lyrics = retrieve_lyrics(url)
    if lyrics is None:
        lyrics = f"could not find (genius) lyrics\n{url}"

    if display:
        print(lyrics)

    return lyrics

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


