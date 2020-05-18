#!/home/slzatz/sonos-companion/bin/python

'''
Gets random quotations from goodreads.com along with bios and images from wikipedia.
'''

import sys
import os
import urllib.request
from bs4 import BeautifulSoup
from config import goodreads_key, goodreads_secret, author_image_size
from pathlib import Path
home = str(Path.home())
sys.path = [home] + sys.path
from goodreads import client
import re
from random import choice
import wikipedia
import textwrap
from authors import authors
from display_image import display_image, get_screen_size
from math import ceil

#max_chars_line = 100 # note this should be calculated from the screen width and char_width
    
gr_url = 'https://www.goodreads.com/work/quotes/'

# To remove stray html tags from the retrieved results
# have seen stray <br/> but maybe best to look and substitute \n
def cleanedUpQuote(quote):              
    quote = re.sub('<.*?>','', quote)
    return quote

def get_all_book_ids(author):
    gc = client.GoodreadsClient(goodreads_key, goodreads_secret)
    book_ids = gc.search_books(author, search_field='author')
    return book_ids

def get_page_from_book_id(book_id): #page   ?page=2

    try:
        page = urllib.request.urlopen(gr_url + book_id).read()
    except Exception as e:
        print(f"Exception retrieving from goodreads: {e}")
        return
    soup = BeautifulSoup(page,"lxml")
    return soup

def get_quotes_from_page(soup):

    quote_divs = soup.find_all("div",class_="quoteText")
    if not quote_divs:
        return

    quotes = list()
    for quote_div in quote_divs:
        text = str(quote_div)
        matchQ = re.search('“(.*)”',text) # finds all matches inside quotations
        #quote = matchQ.group(0) # uses first match
        quote = matchQ.group(0)[1:-1]
        #quotes.append(matchQ.group(0))
        quotes.append(quote)

    return quotes 

def get_quotes_from_book_id(book_id):

    try:
        page = urllib.request.urlopen(gr_url + book_id).read()
    except Exception as e:
        print(f"Exception retrieving from goodreads: {e}")
        return None

    soup = BeautifulSoup(page,"lxml")
    quote_divs = soup.find_all("div",class_="quoteText")
    if not quote_divs:
        return

    quotes = list()
    for quote_div in quote_divs:
        text = str(quote_div)
        matchQ = re.search('“(.*)”',text) # finds all matches inside quotations
        #quote = matchQ.group(0) # uses first match
        #quote = matchQ.group(0).replace('“', '').replace('”', '')
        quote = matchQ.group(0)[1:-1]
        #quotes.append(matchQ.group(0))
        quotes.append(quote)

    return quotes 

def get_gr_page(author):

    gc = client.GoodreadsClient(goodreads_key, goodreads_secret)

    book_ids = gc.search_books(author, search_field='author')
    # order seems to be driven by likelihood of quotes so
    book_ids = book_ids[:3]
    #print(book_ids)
    #n = randrange(len(book_ids))
    #book_id = book_ids[n]
    while 1:
        book_id = choice(book_ids)
        #print(f"{book_id=}")

        try:
            page = urllib.request.urlopen(gr_url + book_id).read()
        except Exception as e:
            print(f"Exception retrieving from goodreads: {e}")
            return None

        soup = BeautifulSoup(page,"lxml")
        if soup.find("div",class_="quoteText"):
            return soup
        book_ids.remove(book_id)
        if not book_ids:
            return None

def get_gr_quotation(soup):

    quote_divs = soup.find_all("div",class_="quoteText")
    quote_div = choice(quote_divs)
    text = str(quote_div)
    #matchQ = re.findall('“(.*)”',text) # finds all matches inside quotations
    matchQ = re.search('“(.*)”',text) # finds all matches inside quotations
    quote = cleanedUpQuote(matchQ.group(0)) # uses first match
    lines = textwrap.wrap(quote, max_chars_line, initial_indent=indent, subsequent_indent=indent)
    line_count = len(lines)
    lines = "\n".join(lines)
    return lines, line_count 

def get_gr_raw_quotation(soup):
    quote_divs = soup.find_all("div",class_="quoteText")
    quote_div = choice(quote_divs)
    text = str(quote_div)
    #matchQ = re.findall('“(.*)”',text) # finds all matches inside quotations
    matchQ = re.search('“(.*)”',text) # finds all matches inside quotations
    return matchQ.group(0)

def get_gr_title(soup):
    title_tag = soup.find("title")
    title = title_tag.text
    title = title.replace("Quotes ", "")
    return title

def get_wiki_page(topic):
    try:
        page = wikipedia.page(topic) # I changed auto_suggest = False to the default (I changed page function in wikipedia.py
    except Exception as e:
        print(f"Couldn't find {topic} wikipedia: {e}")
        return
    return page

def format_wiki_summary(page):
    summary = ' '.join(re.split(r'(?<=[.:;])\s', page.summary)[:10]) # currently splits into 10 sentences
    summary = textwrap.wrap(summary, max_chars_line, initial_indent=indent, subsequent_indent=indent)
    line_count = len(summary)
    summary = "\n".join(summary)
    return summary, line_count

def get_wiki_summary(page, lines=10):
    #summary = ' '.join(re.split(r'(?<=[.:;])\s', page.summary)[:lines]) # default = 10
    summary = '.'.join(page.summary.split('.')[:lines]) # default = 10
    return summary + '.'

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

def get_all_wikipedia_image_uris(page):

    uri_list = list()
    for uri in page.images:        
        pos = uri.rfind('.')
        if uri[pos:].lower() in [".jpg", ".jpeg"]:
            uri_list.append(uri)

    return uri_list

if __name__ == "__main__":
    line_count = 2
    x = get_screen_size()
    indent_cols = ceil(author_image_size/x.cell_width)
    #indent = ceil(author_image_size/x.cell_width) * ' '
    indent = indent_cols * ' '
    max_chars_line = x.cols - 5
    #print(x)
    print() # line feed
    # saving and restoring cursor position didn't work when there was scrolling
    #sys.stdout.buffer.write(b"\0337") #save cursor position
    if len(sys.argv) == 1:
        author,may_require_translation = choice(authors)
    else:
        author, may_require_translation = sys.argv[1].title(), False
    #quotation, cnt = get_quotation(author, may_require_translation)
    gr_page = get_gr_page(author)
    quotation, cnt = get_gr_quotation(gr_page)
    line_count += cnt
    title_author = get_gr_title(gr_page)
    wiki_page = get_wiki_page(author)
    if not wiki_page:
        wiki_page = ""
    bio, cnt = format_wiki_summary(wiki_page)
    line_count += cnt
    q = f"\x1b[3m{quotation}\x1b[0m\n{indent}-- \x1b[1m{title_author}\x1b[0m\n\n{bio}"
    print(q)
    sys.stdout.buffer.write(f"\x1b[{line_count}A".encode('ascii')) # move back up 9 lines
    #sys.stdout.buffer.write(b"\0338") #restore cursor position
    sys.stdout.buffer.write(b"\x1b[7B") #move down 8 lines to near middle of image
    print("  retrieving photo ...")
    sys.stdout.buffer.write(b"\x1b[9A") # move back up 9 lines
    uri = get_wikipedia_image_uri(wiki_page) 
    display_image(uri, author_image_size, author_image_size, erase=False)    
    print()
    if line_count > 22: 
        print((line_count-22)*"\n")
