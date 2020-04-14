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
\x1b[7m - switches to inverted colors
\x1b[0m - return background to normal
\x1b(B - exit line drawing mode
\x1b(0 - enter line drawing mode
\033[s or \0337 - save cursor position
\033[u or \0338 - restore cursor position

Below is how icat does the cursor position:
  sys.stdout.buffer.write("\033[{};{}H".format(place.top + 1, x + extra_cells).encode("ascii"))
  sys.stdout.buffer.write(b"\0337") - save cursor
  sys.stdout.buffer.write(b"\0338") - restore cursor
'''
#from itertools import cycle
from config import google_api_key, google_translate_project_id, detectlanguage_key
import requests
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
import wand.image
from io import BytesIO
from base64 import standard_b64encode

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

# functions to draw graphs to kitty terminal window
def serialize_gr_command(cmd, payload=None):
    cmd = ','.join('{}={}'.format(k, v) for k, v in cmd.items())
    ans = []
    w = ans.append
    w(b'\033_G'), w(cmd.encode('ascii'))
    if payload:
       w(b';')
       w(payload)
    w(b'\033\\')
    return b''.join(ans)

def write_chunked(cmd, data):
    #print("In write_chunked\n") 
    data = standard_b64encode(data)
    while data:
        chunk, data = data[:4096], data[4096:]
        m = 1 if data else 0
        cmd['m'] = m
        sys.stdout.buffer.write(serialize_gr_command(cmd, chunk))
        sys.stdout.flush()
        cmd.clear()

def display_image(uri):
    '''image = sqlalchemy image object'''
    #print(uri)
    try:
        response = requests.get(uri, timeout=5.0)
    except (requests.exceptions.ConnectionError,
            requests.exceptions.TooManyRedirects,
            requests.exceptions.ChunkedEncodingError,
            requests.exceptions.ReadTimeout) as e:
        print(f"requests.get({uri}) generated exception:\n{e}")
        return

    if response.status_code != 200:
        print(f"{uri} returned a {response.status_code}")
        return
        
    # it is possible to have encoding == None and ascii == True
    if response.encoding or response.content.isascii():
        print(f"{uri} returned ascii text and not an image")
        return

    # this try/except is needed for occasional bad/unknown file format
    try:
        img = wand.image.Image(file=BytesIO(response.content))
    except Exception as e:
        print(f"wand.image.Image(file=BytesIO(response.content))"\
              f"generated exception from {uri} {e}")
        return

    if img.format == 'JPEG':
        img.format = 'png'

    ww = img.width
    hh = img.height
    sq = ww if ww <= hh else hh
    if ww > hh:
        t = ((ww-sq)//2,(hh-sq)//2,(ww+sq)//2,(hh+sq)//2) 
    else:
        t= ((ww-sq)//2, 0, (ww+sq)//2, sq)
    img.crop(*t)
    # resize should take the image and enlarge it without cropping 
    img.resize(400,400) #400x400

    f = BytesIO()
    img.save(f)
    img.close()
    f.seek(0)

    write_chunked({'a': 'T', 'f': 100}, f.read()) #f=100 is png;f=24->24bitRGB and f=32->32bit RGBA

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
    print("") # line feed
    sys.stdout.buffer.write(b"\0337") #save cursor position
    author,may_require_translation = choice(authors)
    q,line_count = get_quotation(author, may_require_translation)
    print(q)
    sys.stdout.buffer.write(b"\0338") #restore cursor position
    sys.stdout.buffer.write(b"\x1b[8B") #move down 8 lines to near middle of image
    print("  retrieving photo ...")
    sys.stdout.buffer.write(b"\x1b[9A")
    uri = get_wikipedia_image_uri(author)
    display_image(uri)    
    print("")
    if line_count > 22: 
        print((line_count-22)*"\n")
