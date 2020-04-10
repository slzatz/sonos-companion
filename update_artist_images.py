'''
This allows you to replace smaller pictures of artists with bigger ones
'''

#google custom search api
from apiclient import discovery
import config as c
# needed by the google custom search engine module apiclient
import httplib2
from artist_images_db import *
import sys

google_api_key = c.google_api_key

engine.echo = True

def get_artist_images(name):

    print(f"**************Google Custom Search Engine Request for {name} **************")
    http = httplib2.Http()
    service = discovery.build('customsearch', 'v1',
                              developerKey=google_api_key, http=http)
    z = service.cse().list(q=name, searchType='image', imgType='face', #alternative type is photo
                           imgSize='XXLARGE', num=10, 
                           cx='007924195092800608279:0o2y8a3v-kw').execute() 

    try:
        a = session.query(Artist).filter(func.lower(Artist.name)==name.lower()).one()
    except NoResultFound:
        print("Don't have that name in db so created it")
        a = Artist()
        a.name = name
        session.add(a)
        session.commit()
    except Exception as e:
        print("a = session.query(Artist).filter(func.lower.. error:", e) 
        return []

    # must delete images before you can add new whole new set of images
    #session.query(Image).filter_by(artist_id=a.id).delete()
    #session.commit()

    images = a.images

    for data in z.get('items', []): #['items']: # only empty search should be on artist='' and I think I am catching that but this makes sure
        image=Image()
        image.link = data['link']
        image.width = data['image']['width']
        image.height = data['image']['height']
        image.ok = True
        images.append(image)

    a.images = images
    session.commit()
            
    print("images = ", images)
    #return images 

#name = "Patty Griffin"
name = input("Which artist?")

try:
    artist = session.query(Artist).filter(func.lower(Artist.name)==name.lower()).one()
except NoResultFound:
    yes_no = input(f"I can't find that artist - do you want to look for images for {name}?")
    if yes_no[0].lower()=='y':
        get_artist_images(name)
    else:
        sys.exit()

print("Image count = ", len(artist.images))

for image in artist.images:
    print(image.link, image.width, image.height,image.ok)
    #session.delete(image)

# images will not actually be deleted without session.commit()
yes_no = input("Do you want to delete these images?")
if yes_no[0].lower()=='y':
    session.query(Image).filter_by(artist_id=artist.id).delete()
    session.commit()

yes_no = input("Do you want to look for new images?")
if yes_no[0].lower()=='y':
    get_artist_images(name)
else:
    sys.exit()

