#@+leo-ver=5-thin
#@+node:slzatz.20140105160722.1551: * @file C:/home/slzatz/sonos-companion/sonos.py
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

import textwrap
from collections import OrderedDict
DISPLAY = OrderedDict([('artist','Artist'), ('album','Album'), ('title','Song'), ('date','Release date')])

from flask import Flask, render_template, url_for, request, make_response

import soco
from soco.services import zone_group_state_shared_cache

import settings
import pickle

import lxml.html

#using the musicbrainz db to find the release date and album (if a compilation)
import musicbrainzngs

app = Flask(__name__)
# settings.py
#HOST = '0.0.0.0'
#INDEX_HTML = 'index5.html'
#DEBUG = True

app.config.from_pyfile('settings.py')
HOST = app.config['HOST'] 
INDEX_HTML = app.config['INDEX_HTML']
DEBUG = app.config['DEBUG']

speakers = list(soco.discover())

for s in speakers:
    print "speaker: {} - master: {}".format(s.player_name, s.group.coordinator.player_name)
           
for s in speakers:
    if s.is_coordinator:
        master = s
        break
else:
    master = speakers[0]

for s in speakers:
    if s != master:
        s.join(master)
        # note that it appears for some caching reason that the speaker will appear to have previous coordinator/master
        # but it actually will be linked to the correct master
    #print "speaker: {} - master: {}".format(s.player_name, s.group.coordinator.player_name)
    
zone_group_state_shared_cache.clear() #########appear to need both of these lines to update the cache #####################
speakers = list(soco.discover()) ############################

print "\n"
for s in speakers:
    print "speaker: {} - master: {}".format(s.player_name, s.group.coordinator.player_name)

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

wrapper = textwrap.TextWrapper(width=21, replace_whitespace=False)



#@+node:slzatz.20140421213753.2449: ** stations
stations = [
('WNYC', 'aac://204.93.192.135:80/wnycfm-tunein.aac'),
('WSHU', 'x-rincon-mp3radio://wshu.streamguys.org/wshu-news'),
('QuickMix', 'pndrradio:52877953807377986'),
('R.E.M. Radio', 'pndrradio:637630342339192386'), 
('Nick Drake Radio', 'pndrradio:409866109213435458'),
('Dar Williams Radio', 'pndrradio:1823409579416053314'),
('Patty Griffin Radio', 'pndrradio:52876609482614338'),
('Lucinda Williams Radio', 'pndrradio:360878777387148866'),
('Neil Young Radio', 'pndrradio:52876154216080962'),
('Kris Delmhorst Radio', 'pndrradio:610111769614181954'),
('Counting Crows Radio', 'pndrradio:1727297518525703746'), 
('Vienna Teng Radio', 'pndrradio:138764603804051010')]

#for i,s in enumerate(stations):
    #print "{:d} - {}".format(i+1,s[0])

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
    
    #if there is no artist (for example when Sonos isn't playing anything) then show images of sunsets  ;-)
    if not artist:
        artist = 'sunsets'

    if artist not in artists: 
        http = httplib2.Http()
        service = discovery.build('customsearch', 'v1',  developerKey='AIzaSyCe7pbOm0sxYXwMWoMJMmWvqBcvaTftRC0', http=http)
        z = service.cse().list(q=artist, searchType='image', imgSize='large', num=10, cx='007924195092800608279:0o2y8a3v-kw').execute() 

        print 'artist=',artist    #################################################
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
            
    if url is not None:
        return url
            
    try:
        z = musicbrainzngs.search_recordings(artist=artist, recording=title, limit=5, offset=None, strict=False)
    except:
        return None
        
    for d in z['recording-list']:

         if int(d['ext:score'])==100:
             new_artist = d['artist-credit-phrase']
             new_title = d['title']
    
    payload = {'func': 'getSong', 'artist': new_artist, 'song': new_title, 'fmt': 'realjson'}
    
    try:
         r = requests.get("http://lyrics.wikia.com/api.php", params=payload)
    except:
        return None
                
    q = r.json()
        
    url = q['url'] if 'url' in q else None
        
    if url and url.find("action=edit") != -1: 
        url = None 
    else:
        print "got song lyrics by using musicbrainz db to figure out correct artist and title"
        
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
        return "No date exception (search_releases)"
    
    #release_list = result['release-list'] # can be missing
    
    if 'release-list' in result:
            release_list = result['release-list'] # can be missing
            dates = [d['date'][0:4] for d in release_list if 'date' in d and int(d['ext:score']) > 90] 
    
            if dates:
                dates.sort()
                return dates[0]  
        
    # above may not work if it's a collection album with a made up name; the below tries to address that 
    try:
        result = musicbrainzngs.search_recordings(artist=artist, recording=title, limit=20, offset=None, strict=False)
    except:
        return "No date exception (search_recordings)"
    
    #recording_list = result['recording-list']
    recording_list = result.get('recording-list')
    
    if recording_list is None:
        return "No date (no recording_list)"
    
    dates = []
    for d in recording_list:
            if 'release-list' in d:
                #dd = [x['date'][0:4]+': '+x['title'] for x in d['release-list'] if 'date' in x and int(d['ext:score']) > 90]
                dd = [x['date'][0:4] for x in d['release-list'] if 'date' in x and int(d['ext:score']) > 90]     
                dates.extend(dd)
            
               #[item for sublist in l for item in sublist] - this should work but not sure it makes sense to modify above which works
            
    if dates:
        dates.sort()
        return dates[0]   
    else:
        return "?" 
    


#@+node:slzatz.20140421213753.2448: ** play_uri
def play_uri(uri, name):
    try:
        master.play_uri(uri)
    except:
        print "had a problem switching to {}!".format(name)
    else:
        print "switched to {}".format(name)
#@+node:slzatz.20140120090653.1358: ** Sonos controls (not in use)
#@+node:slzatz.20140105160722.1554: *3* play
@app.route("/play")
def play():
    master.play()
    return 'Ok'

#@+node:slzatz.20140105160722.1555: *3* pause
@app.route("/pause")
def pause():
    master.pause()
    return 'Ok'

#@+node:slzatz.20140105160722.1556: *3* next
@app.route("/next")
def next():
    master.next()
    return 'Ok'

#@+node:slzatz.20140105160722.1557: *3* previous
@app.route("/previous")
def previous():
    master.previous()
    return 'Ok'

#@+node:slzatz.20140105160722.1558: ** info_light
@app.route("/info-light")
def info_light():
    track = master.get_current_track_info()
    return json.dumps(track)

#@+node:slzatz.20140105160722.1559: ** info
@app.route("/info")
def info():
    track = master.get_current_track_info()
    
    # get lyrics from lyricwiki
    url = get_url(track['artist'], track['title'])
    lyrics = get_lyrics(url)
    track['lyrics'] = lyrics
    
    # get album date from musicbrainz db
    track['date'] = get_release_date(track['artist'], track['album'], track['title'])
    track['artist_info'] = get_artist_info(track['artist'])
    
    return json.dumps(track)

#@+node:slzatz.20140615215114.2461: ** spark
@app.route("/spark")
def spark():
    print "client headers=\n", request.headers
    track = master.get_current_track_info()
    track['date'] = get_release_date(track['artist'], track['album'], track['title'])
    
    # OLED is 128x64 pixels seems to be about 8 x 21 charactiers = 168 chars
    #print "track=\n", track
    
    #resp = make_response("artist: {}\nalbum: {}\nsong: {}\nrelease date: {}".format(track['artist'], track['album'], track['title'], track['date']), 200)
    
    s = ''
    for x in d:
        s+=wrapper.fill(DISPLAY[x]+": "+track.get(x,''))+"\n\r"
    
    #s = "Artist: {artist}\n\rAlbum: {album}\n\rSong: {title}\n\rRelease date: {date}\n\r".format(**track)

    #wrapper.fill(a)
    resp = make_response(s.ljust(168))
    
    #resp = make_response("Artist: {artist}\n\rAlbum: {album}\n\rSong: {title}\n\rRelease date: {date}\n\r".format(**track), 200)
    resp.headers['Content-Type'] = "text/json"
    resp.headers['Server'] = "sonos"
    
    #for some reason the print below appears to help prevent the server from hicupping.
    #I think the real answer is to introduce some delay(20) between client.print on the spark
    print resp 
    
    return resp
    #return "artist: {}\nalbum: {}\nsong: {}\nrelease date: {}".format(track['artist'], track['album'], track['title'], track['date'])[0:4]
    
#@+node:slzatz.20140105160722.1560: ** images
@app.route("/images")
def images():
    track = master.get_current_track_info()
    return json.dumps(get_images(track['artist']))

#@+node:slzatz.20140105160722.1561: ** index
@app.route("/")
def index():
    track = master.get_current_track_info()
    return render_template(INDEX_HTML)

#@+node:slzatz.20140419192833.2446: ** buttons
@app.route('/b/<int:button>')
def show_button(button):
    print "button: {}".format(button)
    
    #note that using 12 right now to gracefully disconnect cc3000 from WiFi
    if 0 < button < 13:
        n = button-1
        play_uri(stations[n][1], stations[n][0]) 
    
    return "button: {}".format(button)
    

#@+node:slzatz.20140420093643.2447: ** volume
@app.route('/v/<int:volume>')
def show_volume(volume):
    print "volume: {}".format(volume)
    
    set_volume = int(round(volume / 10.24))         # convert (0-1024) trimpot read into 0-100 volume level

    if set_volume > 75:
        set_volume = 75
        print "volume set to over 75 was reset to 75"
                    
    for s in speakers:
        s.volume = set_volume
    
    return "volume: {}".format(volume)
    
    
#@+node:slzatz.20140429195658.2451: ** debugmemory
@app.route('/m/<int:memory>')
def show_memory(memory):
    print "memory: {}".format(memory)
    
    return "memory: {}".format(memory)
    
    
    
    
#@+node:slzatz.20140510101301.2452: ** list_stations
@app.route('/stations')
def list_stations():
    z = ""
    for i,s in enumerate(stations):
        print "{:d} - {}".format(i+1,s[0])
        z+= "{:d} - {}<br>".format(i+1,s[0])
        
    return z
    
    
        
    
    
    
    
#@+node:slzatz.20140131181451.1211: ** main
if __name__ == '__main__':
    app.run(host=HOST, debug=DEBUG)
#@-others


#@-leo
