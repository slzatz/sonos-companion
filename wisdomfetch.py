#!bin/python

'''
Gets random quotations from wikiquote along with bios and images from wikipedia.
If quotation is not in English, using Google Cloud Translage v3beta (has free tier)
to translate the quotation.
Note hex 1b = octal 33 = decimal 27 = ESCAPE
\x1b[NC [ND moves cursor forward/back by N columns
\x1b[NA [NB moves cursor up/down by N rows
\x1b[2J - erase entire screen and go home
\x1b[J - erase down
\x1b[1J - erase up
\x1b[H - send cursor home
\x1b[{};{}H".format(place.top + 1, x + extra_cells).encode("ascii")
\x1b[7m - switches to inverted colors
\x1b[0m - return background to normal
\x1b(B - exit line drawing mode
\x1b(0 - enter line drawing mode
\x1b[s or \x1b7 - save cursor position
\x1b[u or \x1b8 - restore cursor position
'''

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
import sys
from show_png_jpg import display_image

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

def get_quotation(author, may_require_translation):
    #author,may_require_translation = choice(authors)
    try:
        quote = choice(wikiquote.quotes(author))
    except Exception as e:
        print(f"Exception retrieving from wikiquote: {e}")
        quote = f"Couldn't retrieve the quotation from {author}. Received exception: {html.escape(repr(e))}"

    quote = quote.replace(chr(173), "") # appears to be extended ascii 173 in Churchil quotes (? others):w
    if may_require_translation:
        lang_code = detectlanguage.simple_detect(quote)
        if lang_code != "en":
            language = lang_map.get(lang_code, "No language code match")
            #translation = translate_client.translate(quote, "en")
            response = translate_client.translate_text(
                                             parent=parent,
                                             contents=[quote],
                                             mime_type='text/plain',  # mime types: text/plain, text/html
                                             #source_language_code=lang_code+'-'+language,
                                             source_language_code=lang_code,
                                             #target_language_code='en-US')
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
    z = " \n \n" if translation else ""

    # at current screen mag and font a 400 x 400 picture = 22 lines
    line_count = 2
    indent = 45*" "
    lines = textwrap.wrap(f"{translation}{z}{quote}", max_chars_line, initial_indent=indent, subsequent_indent=indent)
    line_count += len(lines)
    lines = "\n".join(lines)

    try:
        bio = wikipedia.summary(author, sentences=3)
    except Exception as e:
        print(f"Couldn't retrieve {author} bio from wikipedia: {e}")
        text = f"Couldn't retrieve {author} bio from wikipedia: {html.escape(repr(e))}"
    else:
        bio = textwrap.wrap(bio, max_chars_line, initial_indent=indent, subsequent_indent=indent)
        line_count += len(bio)
        bio = "\n".join(bio)

    try:
        page = wikipedia.page(author)
        images = page.images
    except Exception as e:
        print(f"Could not retrieve page/images for {author}")
        print(f"Exception retrieving from wikipedia: {e}")
        data = {"uri":"searching"}

    else:
        while 1:
            uri = choice(images)
            if uri[-4:].lower() in [".jpg", ".png"]:
                break
            else:
                images.remove(uri)
            
    return f"\x1b[3m{lines}\x1b[0m\n{indent}-- \x1b[1m{author}\x1b[0m\n\n{bio}", line_count

def get_wikipedia_image_uri(author):

    try:
        page = wikipedia.page(author)
        images = page.images
    except Exception as e:
        print(f"Could not retrieve page/images for {author}")
        print(f"Exception retrieving from wikipedia: {e}")
        data = {"uri":"searching"}

    else:
        while 1:
            uri = choice(images)
            if uri[-4:].lower() in [".jpg", ".png"]:
                break
            else:
                images.remove(uri)
            
    return uri

if __name__ == "__main__":
    print() # line feed
    sys.stdout.buffer.write(b"\0337") #save cursor position
    if not sys.argv[1]:
        author,may_require_translation = choice(authors)
    else:
        author, may_require_translation = sys.argv[1], False
    q,line_count = get_quotation(author, may_require_translation)
    print(q)
    sys.stdout.buffer.write(b"\0338") #restore cursor position
    sys.stdout.buffer.write(b"\x1b[7B") #move down 8 lines to near middle of image
    print("  retrieving photo ...")
    sys.stdout.buffer.write(b"\x1b[9A")
    uri = get_wikipedia_image_uri(author) # move back up 9 lines
    display_image(uri, 400, 400, erase=False)    
    print()
    if line_count > 22: 
        print((line_count-22)*"\n")
