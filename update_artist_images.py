'''
This allows you to replace smaller pictures of artists with bigger ones
'''

#google custom search api
from apiclient import discovery
import config as c
# needed by the google custom search engine module apiclient
import httplib2
from amazon_music_db import *
import sys

g_api_key = c.google_api_key

engine.echo = True

#name = "Patty Griffin"
name = raw_input("Which artist?")

artist = session.query(Artist).filter_by(name=name).one()
print "Image count = ", len(artist.images)

for image in artist.images:
    print image.link, image.width, image.height,image.ok
    session.delete(image)

# images will not actually be deleted without session.commit()
yes_no = raw_input("Do you want to delete these images?")
if yes_no[0].lower()=='y':
    session.commit()

yes_no = raw_input("Do you want to look for new images?")
if yes_no[0].lower()=='n':
    sys.exit()
        
print "**************Google Custom Search Engine Request for **************"
http = httplib2.Http()
service = discovery.build('customsearch', 'v1',  developerKey=g_api_key, http=http)

images = []

for n in range(2):

    start = 1 + n*10
    z = service.cse().list(q=name, start=start, imgType='face', searchType='image', imgSize='xlarge', num=10, cx='007924195092800608279:0o2y8a3v-kw').execute() 

    for i in z['items']:
        image = Image(link=i['link'], width=i['image']['width'],height=i['image']['height'])
        images.append(image)
        print i['link'], i['image']['width'], i['image']['height']


yes_no = raw_input("Do you want to replace the images?")
if yes_no[0].lower()=='y':
    artist.images = images
    session.commit()
