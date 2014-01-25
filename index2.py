#@+leo-ver=5-thin
#@+node:slzatz.20140105160722.1551: * @file C:/home/slzatz/webapp/index2.py
#@@language python
#@@tabwidth -4
#@+others
#@+node:slzatz.20140105160722.1552: ** index declarations

# needed by the google custom search engine module apiclient
import httplib2

from apiclient import discovery

import requests
import json

from flask import Flask, render_template, url_for

from soco import SoCo

import settings
import pickle

app = Flask(__name__)

app.config.from_pyfile('settings.py')

sonos = SoCo(app.config['SPEAKER_IP'])

try:
  with open('artists.json', 'r') as f:
      artists = json.load(f)
except IOError:
      artists = {}
      
print artists

#@+node:slzatz.20140105160722.1553: ** get_images
def get_images(artist):

  if artist not in artists:

      # 10 is the max you can bring back
      # I think you just separate the orterms by a space
      # imgSize = 'large'
      # orTerms='picture photo image'
      # start=1 or 11
      # link
      # height
      # width
      http = httplib2.Http()
      service = discovery.build('customsearch', 'v1',  developerKey='AIzaSyCe7pbOm0sxYXwMWoMJMmWvqBcvaTftRC0', http=http)
      z = service.cse().list(q=artist, searchType='image', imgSize='large', num=10, cx='007924195092800608279:0o2y8a3v-kw').execute() 

      #artists[artist] = [a['link'] for a in z['items']]
      
      #d = [{k: a[k] for k in ['link','image'] } for a in z['items']]
      
      
      q = []

      for x in z['items']:
          y = {}
          y['image'] = {k:x['image'][k] for k in ['height','width']}
          y['link'] = x['link']
          q.append(y)
      
      artists[artist] = q

      print "**************Google Custom Search Engine Request for "+artist+"**************"
          
      try:
          with open('artists.json', 'w') as f:
              json.dump(artists, f)
      except IOError:
          print "Could not write 'artists' json file"

  return artists[artist]
    
#@+node:slzatz.20140105160722.1554: ** play
@app.route("/play")
def play():
    sonos.play()
    return 'Ok'

#@+node:slzatz.20140105160722.1555: ** pause
@app.route("/pause")
def pause():
    sonos.pause()
    return 'Ok'

#@+node:slzatz.20140105160722.1556: ** next
@app.route("/next")
def next():
    sonos.next()
    return 'Ok'

#@+node:slzatz.20140105160722.1557: ** previous
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
    return render_template('index2.html', track=track)

#@-others
if __name__ == '__main__':
    app.run(debug=True)
#@-leo
