#!bin/python

import sys
import os
import random
from bs4 import BeautifulSoup
import requests
from display_image import generate_image, show_image, save_image

WIKI_REQUEST = "https://commons.wikimedia.org/w/index.php?search={search_term}&title=Special:MediaSearch&go=Go&type=image&uselang=en"
WIKI_FILE = "https://commons.wikimedia.org/wiki/File:" #Bob_Dylan_portrait.jpg
WIKI_CATEGORY = "https://commons.wikimedia.org/wiki/Category:" #Bob_Dylan
NUM_IMAGES = 6

# for a wikipedia special search
def get_wiki_images(search_term):
    search_term = search_term.lower()
    search_term = search_term.replace(' ', '+')
    try:
        response  = requests.get(WIKI_REQUEST.format(search_term=search_term))
    except Exception as e:
        print(e)
        return []

    html = BeautifulSoup(response.text, 'html.parser')
    #div = html.find('div', class_="wbmi-media-search-results__list wbmi-media-search-results__list--image")
    # this change noted on 06/21/2021
    div = html.find('div', class_="sdms-search-results__list sdms-search-results__list--image")
    zz = div.find_all('a')
    zz = random.sample(zz, NUM_IMAGES if len(zz) >= NUM_IMAGES else len(zz))
    uris = []
    for link in zz:
        try:
            response = requests.get(link.get('href'))
        except Exception as e:
            print(e)
            continue
        html = BeautifulSoup(response.text, 'html.parser')
        div = html.find('div', class_="fullImageLink")
        img = div.a.get('href')
        uris.append(img)

    return uris

# for retrieval using category name
def get_wiki_images2(search_term):
    search_term = search_term.title()
    search_term = search_term.replace(' ', '_')
    try:
        response  = requests.get(WIKI_CATEGORY+search_term)
        #print(response.url)
        #print(response.status_code)
    except Exception as e:
        print(e)
        return []

    html = BeautifulSoup(response.text, 'html.parser')

    #div = html.find('div', id_="mw-category-media")
    div = html.find('div', class_="mw-category-generated")

    zz = div.find_all('a')
    zz = random.sample(zz, NUM_IMAGES if len(zz) >= NUM_IMAGES else len(zz))
    uris = []
    for link in zz:
        try:
            response = requests.get("https://commons.wikimedia.org"+link.get('href'))
            #print(response.url)
        except Exception as e:
            print(e)
            continue
        html = BeautifulSoup(response.text, 'html.parser')
        try:
            div = html.find('div', class_="fullImageLink")
            img = div.a.get('href')
            uris.append(img)
        except Exception as e:
            print(e)
            continue

    return uris

def get_wiki_images3(search_term):
    search_term = search_term.title()
    search_term = search_term.replace(' ', '_')
    try:
        response  = requests.get(WIKI_CATEGORY+search_term)
        #print(response.url)
        #print(response.status_code)
    except Exception as e:
        print(e)
        return []

    html = BeautifulSoup(response.text, 'html.parser')
    print(html)

    #div = html.find('div', id_="mw-category-media")
    #div = html.find('div', class_="mw-category-generated")
    div = html.find('ul', class_="gallery mw-gallery-traditional")

    zz = div.find_all('a')
    zz = random.sample(zz, NUM_IMAGES if len(zz) >= NUM_IMAGES else len(zz))
    uris = []
    for link in zz:
        try:
            response = requests.get("https://commons.wikimedia.org"+link.get('href'))
            #print(response.url)
        except Exception as e:
            print(e)
            continue
        html = BeautifulSoup(response.text, 'html.parser')
        try:
            div = html.find('div', class_="fullImageLink")
            img = div.a.get('href')
            uris.append(img)
        except Exception as e:
            print(e)
            continue

    return uris
if __name__ == '__main__':

    # Use input as song title and artist name
     artist = sys.argv[1]
     z = get_wiki_images2(artist)
     for x in z:
         print(x)
         if os.path.splitext(x)[1].lower() in ['.png', '.jpg']: 
             img = generate_image(x, 900, 900)
             show_image(img)
             save_image(img, "testing123.png")
             print()

     exit(0)
     z = get_wiki_images(artist)
     a = artist.lower().replace(" ", "_")
     b = artist.lower().replace(" ", "")
     for x in z:
         if a in x.lower().replace("-", "_"):
             print(x, "Good url 1")
         elif b in x.lower():
             print(x, "Good url 2") # this situation where there is no space between names is rare and may not be worth it`
         else:
             print(x, "Bad url")
         zz = x.split("/")[-1]
         xx = WIKI_FILE+zz
         response = requests.get(xx)
         html = BeautifulSoup(response.text, 'html.parser')
         td = html.find('td', class_="description")
         if td:
             if artist.lower() in td.get_text().lower().replace("_", " ").replace("-", " ")[:50]:
                 print(xx, "Good description")
             else:
                 print(xx, "Bad description")
             #print(response.text)
             print(td.get_text().strip().split("\n")[0])
             #print(td.span)
             img = generate_image(x, 100, 100)
             show_image(img)

