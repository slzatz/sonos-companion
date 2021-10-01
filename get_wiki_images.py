#!bin/python

import sys
import random
from bs4 import BeautifulSoup
import requests
from display_image import generate_image, show_image

WIKI_REQUEST = "https://commons.wikimedia.org/w/index.php?search={search_term}&title=Special:MediaSearch&go=Go&type=image&uselang=en"
#WIKI_REQUEST = 'https://commons.wikimedia.org/wiki/Special:MediaSearch?type=image&search=%22'
WIKI_FILE = "https://commons.wikimedia.org/wiki/File:" #Bob_Dylan_portrait.jpg
NUM_IMAGES = 10

def get_wiki_images(search_term):
    search_term = search_term.lower()
    search_term = search_term.replace(' ', '+')
    try:
        #response  = requests.get(WIKI_REQUEST+search_term+"%22")
        #response  = requests.get(f"https://commons.wikimedia.org/w/index.php?search={search_term}&title=Special:MediaSearch&go=Go&type=image&uselang=en")
        response  = requests.get(WIKI_REQUEST.format(search_term=search_term))
        #print(response)
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


if __name__ == '__main__':

    # Use input as song title and artist name
     artist = sys.argv[1]
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

