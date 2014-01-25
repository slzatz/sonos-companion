
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
  with open('artists.pickle') as f:
      artists = pickle.load(f)
except IOError:
      artists = {}

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

      artists[artist] = [a['link'] for a in z['items']]

      #artist[artist] = a['link'],a['height'],a['width'] {'neil young':[['http://..., 400,200],['http://..., 500,400],

      print "Google Custom Search Engine Request"

      try:
          with open('artists.pickle', 'w') as f:
              pickle.dump(artists, f)
      except IOError:
          print "Could not write 'artists' file"

  return artists[artist]
    
@app.route("/play")
def play():
    sonos.play()
    return 'Ok'

@app.route("/pause")
def pause():
    sonos.pause()
    return 'Ok'

@app.route("/next")
def next():
    sonos.next()
    return 'Ok'

@app.route("/previous")
def previous():
    sonos.previous()
    return 'Ok'

@app.route("/info-light")
def info_light():
    track = sonos.get_current_track_info()
    return json.dumps(track)

@app.route("/info")
def info():
    track = sonos.get_current_track_info()
    return json.dumps(track)

@app.route("/images")
def images():
    track = sonos.get_current_track_info()
    return json.dumps(get_images(track['artist']))

@app.route("/")
def index():
    track = sonos.get_current_track_info()
    return render_template('index.html', track=track)

if __name__ == '__main__':
    app.run(debug=True)
