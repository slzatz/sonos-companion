#@+leo-ver=5-thin
#@+node:slzatz.20140105160722.1551: * @file C:/home/slzatz/webapp/index4.py
#@@language python
#@@tabwidth -4
#@+others
#@+node:slzatz.20140105160722.1552: ** imports etc
# needed by the google custom search engine module apiclient
import httplib2

# google custom search api
from apiclient import discovery

import requests
import json

from flask import Flask, render_template, url_for

from soco import SoCo

import settings
import pickle

import lxml.html

#using the musicbrainz db to find the release date and album (if a compilation)
import musicbrainzngs

app = Flask(__name__)

app.config.from_pyfile('settings.py')
HOST = app.config['HOST']
INDEX_HTML = app.config['INDEX_HTML']

sonos = SoCo(app.config['SPEAKER_IP'])

# artists.json is the file that caches previous image searches
try:
  with open('artists.json', 'r') as f:
      artists = json.load(f)
except IOError:
      artists = {}
      
musicbrainzngs.set_useragent("Sonos", "0.1", contact="slzatz")

#last.fm
base_url = "http://ws.audioscrobbler.com/2.0/"
api_key = "1c55c0a239072889fa7c11df73ecd566"

#@+node:slzatz.20140105160722.1553: ** get_images (Google Custom Search Engine)
def get_images(artist):
    '''
    10 is the max you can bring back on any individual search
    I think you  separate the orterms by a space
    orTerms='picture photo image'
    imgSize = 'large'
    start=1 or 11
    using link, height, width
    '''

    if artist not in artists: 
        http = httplib2.Http()
        service = discovery.build('customsearch', 'v1',  developerKey='AIzaSyCe7pbOm0sxYXwMWoMJMmWvqBcvaTftRC0', http=http)
        z = service.cse().list(q=artist, searchType='image', imgSize='large', num=10, cx='007924195092800608279:0o2y8a3v-kw').execute() 

        #print 'z=',z    
        image_list = []

        for x in z['items']:
            y = {}
            y['image'] = {k:x['image'][k] for k in ['height','width']}
            y['link'] = x['link']
            image_list.append(y)
      
        artists[artist] = image_list

        print "**************Google Custom Search Engine Request for "+artist+"**************"
          
        try:
            with open('artists.json', 'w') as f:
                json.dump(artists, f)
        except IOError:
            print "Could not write 'artists' json file"

    return artists[artist]
    
#@+node:slzatz.20140126104203.1211: ** get_artist_info (last.fm)
def get_artist_info(artist, autocorrect=0):
    
    payload = {'method':'artist.getinfo', 'artist':artist, 'autocorrect':autocorrect, 'format':'json', 'api_key':api_key}
    
    try:
        r = requests.get(base_url, params=payload)
        bio = r.json()['artist']['bio']['summary']
        text = lxml.html.fromstring(bio).text_content()
        idx = text.find("Read more")
        if idx != -1:
            text = text[:idx]
        
        return text
        
    except:
        return ''
#@+node:slzatz.20140118074141.1566: ** get_url
def get_url(artist, title):
    payload = {'func': 'getSong', 'artist': artist, 'song': title, 'fmt': 'realjson'}
    
    try:
         r = requests.get("http://lyrics.wikia.com/api.php", params=payload)
    except:
        url = None
         
    else:        
        q = r.json()
        
        url = q['url'] if 'url' in q else None
        
        if url and url.find("action=edit") != -1: 
            url = None 
    
    return url
    
#@+node:slzatz.20140118074141.1565: ** get_lyrics
def get_lyrics(url):

    if not url:
        return "Can't find lyrics - url couldn't be found or had 'edit'  "
    
    try:
        doc = lxml.html.parse(url)
    except IOError:
        return "Can't find lyrics - couldn't parse url - may be a cover"

    try:
        lyricbox = doc.getroot().cssselect(".lyricbox")[0]        
    except IndexError:
        return "Can't find lyrics - couldn't find lyrics in page"

    # look for a sign that it's instrumental
    if len(doc.getroot().cssselect(".lyricbox a[title=\"Instrumental\"]")):
        return "No lyrics - appears to be instrumental"

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
#@+node:slzatz.20140119112538.1357: ** get_release_date
def get_release_date(artist, album, title):

    try:
        result = musicbrainzngs.search_releases(artist=artist, release=album, limit=20, strict=True)  
    except:
        return "No date cxception (search_releases)"
    
    release_list = result['release-list']
             
    dates = [d['date'][0:4] for d in release_list if 'date' in d and int(d['ext:score']) > 90] 
    
    if dates:
        dates.sort()
        return dates[0]  
        
    # above may not work if it's a collection album with a made up name; the below tries to address that 
    try:
        result = musicbrainzngs.search_recordings(artist=artist, recording=title, limit=20, offset=None, strict=False)
    except:
        return "No date exception (search_recordings)"
    
    recording_list = result['recording-list']
    
    dates = []
    for d in recording_list:
            dd = [x['date'][0:4]+': '+x['title'] for x in d['release-list'] if 'date' in x and int(d['ext:score']) > 90]     
            dates.extend(dd)
            
            #[item for sublist in l for item in sublist] - this should work but not sure it makes sense to modify above which works
            
    if dates:
        dates.sort()
        return dates[0]   
    else:
        return "No date" 
    


#@+node:slzatz.20140120090653.1358: ** Sonos controls (not in use)
#@+node:slzatz.20140105160722.1554: *3* play
@app.route("/play")
def play():
    sonos.play()
    return 'Ok'

#@+node:slzatz.20140105160722.1555: *3* pause
@app.route("/pause")
def pause():
    sonos.pause()
    return 'Ok'

#@+node:slzatz.20140105160722.1556: *3* next
@app.route("/next")
def next():
    sonos.next()
    return 'Ok'

#@+node:slzatz.20140105160722.1557: *3* previous
@app.route("/previous")
def previous():
    sonos.previous()
    return 'Ok'

#@+node:slzatz.20140105160722.1558: ** info_light
@app.route("/info-light")
def info_light():
    track = sonos.get_current_track_info()
    return json.dumps(track)

#@+node:slzatz.20140105160722.1559: ** info
@app.route("/info")
def info():
    track = sonos.get_current_track_info()
    
    # get lyrics from lyricwiki
    url = get_url(track['artist'], track['title'])
    lyrics = get_lyrics(url)
    track['lyrics'] = lyrics
    
    # get album date from musicbrainz db
    track['date'] = get_release_date(track['artist'], track['album'], track['title'])
    track['artist_info'] = get_artist_info(track['artist'])
    
    return json.dumps(track)

#@+node:slzatz.20140105160722.1560: ** images
@app.route("/images")
def images():
    track = sonos.get_current_track_info()
    return json.dumps(get_images(track['artist']))

#@+node:slzatz.20140105160722.1561: ** index
@app.route("/")
def index():
    track = sonos.get_current_track_info()
    return render_template(INDEX_HTML)

#@+node:slzatz.20140131181451.1211: ** main
if __name__ == '__main__':
    app.run(host=HOST, debug=True)
#@-others


#@-leo
