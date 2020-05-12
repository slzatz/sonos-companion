#!/home/slzatz/sonos-companion/bin/python

'''
Gets random quotations from wikiquote along with bios and images from wikipedia.
If quotation is not in English, using Google Cloud Translage v3beta (has free tier)
to translate the quotation.
'''

import sys
import re
from config import google_translate_project_id, detectlanguage_key, author_image_size
from math import ceil
from random import choice
import html
import wikipedia
import wikiquote
import textwrap
import detectlanguage
from authors import authors
#from google.cloud import translate_v3beta1 as translate # the v3 api has a free tier
from google.cloud import translate # the v3 api has a free tier
from display_image import display_image, get_screen_size

translate_client = translate.TranslationServiceClient()
# not sure correct value but docs say for non-regionalized requests
# use global and their example uses global
location = "global" 
parent = translate_client.location_path(google_translate_project_id, location)

detectlanguage.configuration.api_key = detectlanguage_key

lang_map = dict()
for x in detectlanguage.languages():
    lang_map[x["code"]] = x["name"]

#max_chars_line = 100
#indent = 45*" "

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

    lines = textwrap.wrap(f"{translation}{z}{quote}", max_chars_line, initial_indent=indent, subsequent_indent=indent)
    line_count = len(lines)
    lines = "\n".join(lines)
    return lines, line_count 

def get_all_quotations(author, may_require_translation):
    #author,may_require_translation = choice(authors)
    global auto_suggest
    try:
        quotes = wikiquote.quotes(author)
    except Exception as e:
        print(f"Exception retrieving from wikiquote: {e}")
        return

    quote_list = list()
    for quote in quotes:

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
        quote_list.append(f"{translation}{z}{quote}")

    # return a list of quotes
    return quote_list

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
    #indent = 45*" "
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
    x = get_screen_size()
    indent_cols = ceil(author_image_size/x.cell_width)
    indent = indent_cols * ' '
    max_chars_line = x.cols - 5
    #indent = ceil(author_image_size/x.cell_width) * ' '
    print() # line feed
    # saving and restoring cursor position didn't work when there was scrolling
    #sys.stdout.buffer.write(b"\0337") #save cursor position
    if len(sys.argv) == 1:
        author,may_require_translation = choice(authors)
    else:
        author, may_require_translation = sys.argv[1].title(), False
    quotation, cnt = get_quotation(author, may_require_translation)
    line_count += cnt
    wiki_page = get_page(author)
    if not wiki_page:
        wiki_page = ""
    bio, cnt = format_summary(wiki_page)
    line_count += cnt
    q = f"\x1b[3m{quotation}\x1b[0m\n{indent}-- \x1b[1m{author}\x1b[0m\n\n{bio}"
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
