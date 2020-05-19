#!/home/slzatz/sonos-companion/bin/python

'''
invoked by ./select_music_images.py "Neil Young"
and will:
1) show existing artist images: in some cases we have stored the image
   and in other cases just the url - will ask whether to keep/convert or toss
2) go out to wikipedia to get images that you can accept/reject
3) do a google image search to get images that you can accept/reject
show you images that you can select and
reject and will check to see if you already have
the image

'''

import sys
from io import BytesIO
#import grfetch
#import wisdomfetch
import wikipedia
from display_image import display_image, generate_image, generate_image2, show_image
from apiclient import discovery #google custom search api
import httplib2 #needed by the google custom search engine module apiclient
from config import google_api_key, ec_id, ec_pw, ec_host, sonos_image_size
import psycopg2
from dataclasses import dataclass

params = {
  'database': 'artist_images',
  'user': ec_id,
  'password': ec_pw,
  'host': ec_host,
  'port': 5432
}
conn = psycopg2.connect(**params)
cur = conn.cursor()

@dataclass
class Image():
    # @dataclass essentially creates an __init__ with these attributes
    link: str
    width: int
    height: int
    OK: bool

def store_image(conn, artist_id, link, width, height, ok):

    sql = ''' INSERT INTO images(artist_id, link, width, height, ok) 
              VALUES(%s,%s,%s,%s,%s) RETURNING id'''
    cur = conn.cursor()
    cur.execute(sql, (artist_id, link, width, height, ok))
    id_ = cur.fetchone()[0]
    conn.commit()
    return id_

def store_image_file(conn, image_id, image):

    sql = "INSERT INTO image_files(image_id, image) VALUES(%s,%s);"
    cur = conn.cursor()
    cur.execute(sql, (image_id, image))
    conn.commit()
    #return cur.lastrowid
    return

def get_google_images(name):
    print(f"**************Google Custom Search Engine Request for {name} **************")
    http = httplib2.Http()
    service = discovery.build('customsearch', 'v1',
                              developerKey=google_api_key, http=http)
    z = service.cse().list(q=name, searchType='image', imgType='face', #alternative type is photo
                           imgSize='XXLARGE', num=10, 
                           cx='007924195092800608279:0o2y8a3v-kw').execute() 

    images = []

    for data in z.get('items', []): 
        image=Image(data['link'],
                    data['image']['width'],
                    data['image']['height'],
                    True) # is image OK - really not necessary anymore
        images.append(image)

    return images 

def get_page(topic):
    try:
        page = wikipedia.page(topic) # I changed auto_suggest = False to the default (I changed page function in wikipedia.py
    except Exception as e:
        print(f"Couldn't find {topic} wikipedia: {e}")
        return
    return page

def get_all_wikipedia_image_uris(page):
    uri_list = list()
    for uri in page.images:        
        pos = uri.rfind('.')
        if uri[pos:].lower() in [".jpg", ".jpeg"]:
            uri_list.append(uri)

    return uri_list

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("You need to supply a name!")
        sys.exit(1)

    #sql = "SELECT authors.id,authors.name FROM authors " \
    #      "INNER JOIN quotes ON authors.id=quotes.author_id AND authors.name=? ORDER BY RANDOM() LIMIT 1;"

    #sql = f"SELECT id,name FROM artists WHERE name='{sys.argv[1].title()}'" 
    sql = "SELECT id,name FROM artists WHERE name=%s OR name=%s;"
    cur.execute(sql, (sys.argv[1], sys.argv[1].title()))
    #cur.execute(sql)
    row = cur.fetchone()
    if row:
        artist_id, name = row
    else:
        print(f"Can't find {sys.argv[1]}!!")
        sys.exit(1)
    #    sql = "SELECT id,name FROM artists WHERE name=?" 
    #    cur.execute(sql, (sys.argv[1],))
    #    row = cur.fetchone()
    #    if row:
    #        artist_id, name = row
    #    else:
    #        print(f"Can't find {sys.argv[1]}!!")


    print(f"\x1b[1m{artist_id} {name}\x1b[0m\n")
    #cur.execute("SELECT link,width,height FROM images WHERE artist_id=?", (artist_id,))
    response = input("Do you want to look at the images currently in the database? ")
    if response[0].lower() == 'y':

        cur.execute(f"SELECT id,link,width,height FROM images WHERE artist_id={artist_id}")
        rows = cur.fetchall()
        for row in rows:
            image_id, link, width, height = row
            print() # line feed
            cur.execute("SELECT image FROM image_files WHERE image_id=%s", (image_id,))
            row = cur.fetchone()
            if row:
                show_image(BytesIO(row[0]))
                print()
                response = input("This image is being stored as bytes in the database  - do you want to KEEP it? ")
                if response[0].lower() != 'y':
                    cur.execute("DELETE FROM image_files WHERE image_id=%s", (image_id,))
                    cur.execute("DELETE FROM images WHERE id=%s", (image_id,))
                    conn.commit()
            else:
                display_image(link)
                print()
                response = input("This image is NOT being stored as bytes yet - do you want to KEEP it? ")
                if response[0].lower() == 'y':
                    f = generate_image(link, sonos_image_size, sonos_image_size)
                    image = f.getvalue()
                    store_image_file(conn, image_id, image)
                else:    
                    cur.execute("DELETE FROM images WHERE link=%s", (link,))
                    conn.commit()

    response = input("Do you want to look for images in the wikipedia? ")
    if response[0].lower() != 'y':
        sys.exit()

    #wiki_page = wisdomfetch.get_page(name)
    wiki_page = get_page(name)
    if not wiki_page:
        print(f"Could not find {name} page!")
        sys.exit(1)        

    #uris = grfetch.get_all_wikipedia_image_uris(wiki_page)
    uris = get_all_wikipedia_image_uris(wiki_page)
    if not uris:
        print(f"Could not find any images for {name} on their wiki page!")

    for uri in uris:
        display_image(uri, erase=False) # don't change size of image
        cur.execute("SELECT COUNT(1) FROM images WHERE link=%s;", (uri,))
        row = cur.fetchone()
        if row[0] == 1:
            print("We already have that url in the database!")
            continue
        response = input("Do you want to put this image into the database? ")
        if response[0].lower() == 'y':
            f,width,height = generate_image2(uri, sonos_image_size, sonos_image_size)
            image_id = store_image(conn, artist_id, uri, width, height, True)
            image = f.getvalue()
            store_image_file(conn, image_id, image)
            print("We stored the image data and the image file!")

    response = input("Do you want to do a google search for images? ")
    if response[0].lower() != 'y':
        sys.exit()
    images = get_google_images(name)
    if not images:
        print(f"Could not find any google images for {name}!")
        sys.exit(1)        

    for image in images:
        result = display_image(image.link, erase=False) # don't change size of image
        if not result:
            continue
        cur.execute("SELECT COUNT(1) FROM images WHERE link=%s;", (image.link,))
        row = cur.fetchone()
        if row[0] == 1:
            print("We already have that url in the database!")
            continue
        response = input("Do you want to use this image? ")
        if response[0].lower() == 'y':
            image_id = store_image(conn, artist_id, image.link, image.width, image.height, True)
            f = generate_image(image.link, sonos_image_size, sonos_image_size)
            image = f.getvalue()
            store_image_file(conn, image_id, image)
            print("We stored the image data and the image file!")

