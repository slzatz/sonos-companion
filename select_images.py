#!/home/slzatz/sonos-companion/bin/python

'''
invoked by ./select_images.py "Samuel Johnson"
and will show you images that you can select and
reject and will check to see if you already have
the image

1) includes the option to delete existing images
2) option to do google image search in addition to wikipedia image search

'''

import sys
from io import BytesIO
import grfetch
import wisdomfetch
from display_image import display_image, generate_image, show_image
import sqlite3
from apiclient import discovery #google custom search api
import httplib2 #needed by the google custom search engine module apiclient
from config import google_api_key

#db_file = "/home/slzatz/sonos-companion/gr.db"
db_file = "/home/slzatz/sonos-companion/wq.db"
author_image_size = 200

conn = sqlite3.connect(db_file)
cur = conn.cursor()

def store_image(conn, author_id, url, image, size):

    sql = ''' INSERT INTO images(author_id, url, image, size)
              VALUES(?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, (author_id, url, image, size))
    conn.commit()
    return cur.lastrowid

def get_google_images(name):

    print(f"**************Google Custom Search Engine Request for {name} **************")
    http = httplib2.Http()
    service = discovery.build('customsearch', 'v1',
                              developerKey=google_api_key, http=http)
    name = f'"{name}"' # ? better search with  name quoted

    z = service.cse().list(q=name, searchType='image', imgType='face', #alternative type is photo
                           #imgSize='xxlarge', num=10, 
                           num=10, 
                           cx='007924195092800608279:0o2y8a3v-kw').execute() 

    uris = [data['link'] for data in z.get('items', [])]

    return uris 

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("You need to supply a name!")
        sys.exit(1)

    #sql = "SELECT authors.id,authors.name FROM authors " \
    #      "INNER JOIN quotes ON authors.id=quotes.author_id AND authors.name=? ORDER BY RANDOM() LIMIT 1;"

    sql = "SELECT id,name FROM authors WHERE name=? OR name=?" 
    cur.execute(sql, (sys.argv[1], sys.argv[1].title()))
    row = cur.fetchone()
    if row:
        author_id, name = row
    else:
        print(f"Can't find {sys.argv[1]}!!")
        sys.exit(1)
        #sql = "SELECT id,name FROM authors WHERE name=?" 
        #cur.execute(sql, (sys.argv[1],))
        #row = cur.fetchone()
        #if row:
        #    author_id, name = row
        #else:
        #    print(f"Can't find {sys.argv[1]}!!")


    cur.execute("SELECT url,image,size FROM images WHERE author_id=?", (author_id,))
    rows = cur.fetchall()
    for row in rows:
        url, image, size = row
        image = BytesIO(image)
        print() # line feed
        print(f"\x1b[1m{author_id} {name}\x1b[0m\n")
        #sys.stdout.buffer.write(f"\x1b[{line_count}A".encode('ascii')) # move back up line_count lines
        show_image(image)
        print()
        response = input("This image is currently in the database - do you want to KEEP it? ")
        if response[0].lower() != 'y':
            cur.execute("DELETE FROM images WHERE url=?", (url,))
            conn.commit()

    response = input("Do you want to look for more images? ")
    if response[0].lower() != 'y':
        sys.exit()

    print("Will look first in the Wikipedia\n\n")

    wiki_page = wisdomfetch.get_page(name)
    if not wiki_page:
        print(f"Could not find {name} page!")
        sys.exit(1)        

    uris = grfetch.get_all_wikipedia_image_uris(wiki_page)
    if not uris:
        print(f"Could not find any images for {name} on their wiki page!")
        #sys.exit(1)        

    for uri in uris:
        display_image(uri, 200, 200, False)
        cur.execute("SELECT COUNT(1) FROM images WHERE url=?", (uri,))
        row = cur.fetchone()
        if row[0] == 1:
            print("We already have that url in the database!")
            continue
        response = input("Do you want to use this image? ")
        if response[0].lower() == 'y':
            f = generate_image(uri, author_image_size, author_image_size)
            image = f.getvalue()
            store_image(conn, author_id, uri, image, author_image_size)

    response = input("Do you want to do a google search for images? ")
    if response[0].lower() != 'y':
        sys.exit()
    uris = get_google_images(name)
    if not uris:
        print(f"Could not find any google images for {name}!")
        sys.exit(1)        

    for uri in uris:
        result = display_image(uri, 200, 200, False)
        if not result:
            continue
        cur.execute("SELECT COUNT(1) FROM images WHERE url=?", (uri,))
        row = cur.fetchone()
        if row[0] == 1:
            print("We already have that url in the database!")
            continue
        response = input("Do you want to use this image? ")
        if response[0].lower() == 'y':
            f = generate_image(uri, author_image_size, author_image_size)
            image = f.getvalue()
            store_image(conn, author_id, uri, image, author_image_size)

#response = do you want to use google image search?
