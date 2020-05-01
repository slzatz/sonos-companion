#!/home/slzatz/sonos-companion/bin/python

'''
Gets random quotations from wikiquote along with bios and images from wikipedia.
If quotation is not in English, using Google Cloud Translage v3beta (has free tier)
to translate the quotation.
'''

import sys
import os
import urllib.request
from bs4 import BeautifulSoup
from config import goodreads_key, goodreads_secret
from pathlib import Path
home = str(Path.home())
sys.path = [home] + sys.path
from goodreads import client

import re
from config import google_translate_project_id, detectlanguage_key
from random import choice
import html
import wikipedia
import wikiquote
import textwrap
import detectlanguage
from authors import authors
#from google.cloud import translate_v3beta1 as translate # the v3 api has a free tier
from google.cloud import translate # the v3 api has a free tier
from display_image import display_image

translate_client = translate.TranslationServiceClient()
# not sure correct value but docs say for non-regionalized requests
# use global and their example uses global
location = "global" 
parent = translate_client.location_path(google_translate_project_id, location)

detectlanguage.configuration.api_key = detectlanguage_key

lang_map = dict()
for x in detectlanguage.languages():
    lang_map[x["code"]] = x["name"]

max_chars_line = 100
indent = 45*" "
    
base_url = 'https://www.goodreads.com/work/quotes/'

def cleanedUpQuote(quote):              # To remove stray html tags from the retrieved results
    quote = re.sub('<.*?>','',quote)
    return quote

def get_gr_page(author):

    gc = client.GoodreadsClient(goodreads_key, goodreads_secret)

    #bookIdList = gc.search_books(author)

    book_ids = gc.search_books(author, search_field='author')
    # order seems to be driven by likelihood of quotes so
    book_ids = book_ids[:3]
    print(book_ids)
    #n = randrange(len(book_ids))
    #book_id = book_ids[n]
    while 1:
        book_id = choice(book_ids)
        print(f"{book_id=}")

        #baseUrl = 'https://www.goodreads.com/work/quotes/'
        #author = author.replace(' ','-')
        #s = bookIdList[0] + '-' + author
        #finalUrl = baseUrl + s;
        try:
            #page = urllib.request.urlopen(finalUrl).read()
            page = urllib.request.urlopen(base_url+book_id).read()
        except Exception as e:
            print(f"Exception retrieving from goodreads: {e}")
            return None

        soup = BeautifulSoup(page,"lxml")
        if soup.find("div",class_="quoteText"):
            return soup
        book_ids.remove(book_id)
        if not book_ids:
            return None

#def get_gr_quotation(author):
def get_gr_quotation(soup):

    #gc = client.GoodreadsClient(goodreads_key, goodreads_secret)

    #book_ids = gc.search_books(author, search_field='author')
    #book_ids = book_ids[:3]
    #while 1:
    #    book_id = choice(book_ids)
    #    print(f"{book_id=}")

    #    #baseUrl = 'https://www.goodreads.com/work/quotes/'
    #    #author = author.replace(' ','-')
    #    #s = bookIdList[0] + '-' + author
    #    #finalUrl = baseUrl + s;
    #    try:
    #        #page = urllib.request.urlopen(finalUrl).read()
    #        page = urllib.request.urlopen(base_url+book_id).read()
    #    except Exception as e:
    #        print(f"Exception retrieving from goodreads: {e}")
    #        quote = f"Couldn't retrieve goodreads  quotation from {author}. Received exception: {html.escape(repr(e))}"
    #        return quote, 1

    #    soup = BeautifulSoup(page,"lxml")
        
    quote_divs = soup.find_all("div",class_="quoteText")
    #authors = soup.find_all("span", class_="authorOrTitle")
    quote_div = choice(quote_divs)
    text = str(quote_div)
    matchQ = re.findall('“(.*)”',text) # finds all matches inside quotations
    matchQ = re.search('“(.*)”',text) # finds all matches inside quotations
    #quote = cleanedUpQuote(matchQ[0]) # uses first match
    quote = cleanedUpQuote(matchQ.group(0)) # uses first match
    lines = textwrap.wrap(quote, max_chars_line, initial_indent=indent, subsequent_indent=indent)
    line_count = len(lines)
    lines = "\n".join(lines)
    return lines, line_count 

def get_gr_title(soup):
    title_tag = soup.find("title")
    title = title_tag.text
    title = title.replace("Quotes ", "")
    return title


def get_quotation(author, may_require_translation):
    #author,may_require_translation = choice(authors)
    global auto_suggest
    try:
        quote = choice(wikiquote.quotes(author))
    except Exception as e:
        print(f"Exception retrieving from wikiquote: {e}")
        quote = f"Couldn't retrieve the quotation from {author}. Received exception: {html.escape(repr(e))}"

    quote = quote.replace(chr(173), "") # appears to be extended ascii 173 in Churchil quotes (? others)
    if may_require_translation:
        lang_code = detectlanguage.simple_detect(quote)
        if lang_code != "en":
            language = lang_map.get(lang_code, "No language code match")
            #translation = translate_client.translate(quote, "en")
            response = translate_client.translate_text(
                                             parent=parent,
                                             contents=[quote],
                                             mime_type='text/plain', 
                                             source_language_code=lang_code,
                                             target_language_code='en')

            translation = response.translations[0]
            translation = f"{translation}".replace("translated_text: ", "").replace('"', '')
        else:
            language = ""
            translation = ""
    else:
        language = ""
        translation = ""

    s = f"Translated from {language}\n" if language else ""
    z = f"\n\n{s}" if translation else ""

    # at current screen mag and font a 400 x 400 picture = 22 lines
    #line_count = 2
    #indent = 45*" "
    lines = textwrap.wrap(f"{translation}{z}{quote}", max_chars_line, initial_indent=indent, subsequent_indent=indent)
    line_count = len(lines)
    lines = "\n".join(lines)
    return lines, line_count 

def get_page(topic):
    try:
        page = wikipedia.page(topic) # I changed auto_suggest = False to the default (I changed page function in wikipedia.py
    except Exception as e:
        print(f"Couldn't find {topic} wikipedia: {e}")
        return
    return page

def format_summary(page):
    # currently splits into 10 sentences
    #line_count = 2
    indent = 45*" "
    summary = ' '.join(re.split(r'(?<=[.:;])\s', page.summary)[:10])
    summary = textwrap.wrap(summary, max_chars_line, initial_indent=indent, subsequent_indent=indent)
    line_count = len(summary)
    summary = "\n".join(summary)
    return summary, line_count
    return f"{indent}\x1b[1m{page.title}\x1b[0m\n\n\x1b[3m{summary}\x1b[0m", line_count

def get_wikipedia_image_uri(page):

    images = page.images
    if images:
        while 1:
            if len(images) == 1:
                uri = images[0]
                break
            uri = choice(images)
            pos = uri.rfind('.')
            if uri[pos:].lower() in [".jpg", ".jpeg"]:
                break
            else:
                images.remove(uri)
    else:
        uri = None

    return uri
if __name__ == "__main__":
    line_count = 2
    print() # line feed
    # saving and restoring cursor position didn't work when there was scrolling
    #sys.stdout.buffer.write(b"\0337") #save cursor position
    if len(sys.argv) == 1:
        author,may_require_translation = choice(authors)
    else:
        author, may_require_translation = sys.argv[1].title(), False
    #quotation, cnt = get_quotation(author, may_require_translation)
    gr_page = get_gr_page(author)
    #quotation, cnt = get_goodreads_quotation(author)
    quotation, cnt = get_gr_quotation(gr_page)
    line_count += cnt
    title_author = get_gr_title(gr_page)
    wiki_page = get_page(author)
    if not wiki_page:
        wiki_page = ""
    bio, cnt = format_summary(wiki_page)
    line_count += cnt
    q = f"\x1b[3m{quotation}\x1b[0m\n{indent}-- \x1b[1m{title_author}\x1b[0m\n\n{bio}"
    print(q)
    sys.stdout.buffer.write(f"\x1b[{line_count}A".encode('ascii')) # move back up 9 lines
    #sys.stdout.buffer.write(b"\0338") #restore cursor position
    sys.stdout.buffer.write(b"\x1b[7B") #move down 8 lines to near middle of image
    print("  retrieving photo ...")
    sys.stdout.buffer.write(b"\x1b[9A") # move back up 9 lines
    uri = get_wikipedia_image_uri(wiki_page) 
    display_image(uri, 400, 400, erase=False)    
    print()
    if line_count > 22: 
        print((line_count-22)*"\n")
