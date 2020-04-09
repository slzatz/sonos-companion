#!bin/python

'''
Gets random quotations from wikiquote along with bios and images from wikipedia.
If quotation is not in English, using Google Cloud Translage v3beta (has free tier)
to translate the quotation.

\x1b[NC moves cursor forward by N columns
write(STDOUT_FILENO, "\x1b[2J", 4); //clears the screen
write(STDOUT_FILENO, "\x1b[H", 3); //send cursor home
int nchars = snprintf(lf_ret, sizeof(lf_ret), "\r\n\x1b[%dC", EDITOR_LEFT_MARGIN);
ab.append("\x1b[7m", 4); //switches to inverted colors
write(STDOUT_FILENO, "\x1b[37;1mw", 8); //'T' corner
write(STDOUT_FILENO, "\x1b[0m", 4); // return background to normal (? necessary)
  write(STDOUT_FILENO, "\x1b(B", 3); //exit line drawing mode
  write(STDOUT_FILENO, "\x1b(0", 3); // Enter line drawing mode
   Save cursor position:
  \033[s
- Restore cursor position:
  \033[u
'''
from itertools import cycle
from config import google_api_key, google_translate_project_id, detectlanguage_key
import requests
from random import choice
import html
import wikipedia
import wikiquote
import textwrap
import detectlanguage
from authors import authors
from google.cloud import translate_v3beta1 as translate # the v3 api has a free tier
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
        print(f"status code = {response.status_code}")
        #print(f"{uri} returned a {response.status_code}")
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
    img.save(filename = "images/zzzz")
    img.close()

    #with open("images/zzzz", 'rb') as f:
    #    write_chunked({'a': 'T', 'f': 100}, f.read()) #f=100 is png;f=24->24bitRGB and f=32->32bit RGBA

    #print("\x1b[0;50H")

def get_quotation():
    author,may_require_translation = choice(authors)
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

    s = f"Translated from {language}<br/>" if language else ""
    z = " \n \n" if translation else ""

    #lines = textwrap.wrap(repr(translation) quote + "\n" + repr(translation), max_chars_line)
    lines = textwrap.wrap(f"{translation}{z}{quote}", max_chars_line, initial_indent="                                                   ", subsequent_indent="                                                   ")
    lines = "\n".join(lines)

    try:
        bio = wikipedia.summary(author)
    except Exception as e:
        print(f"Couldn't retrieve {author} bio from wikipedia: {e}")
        text = f"Couldn't retrieve {author} bio from wikipedia: {html.escape(repr(e))}"
    else:
        index = bio.find(".", 400)
        if index != -1:
            bio = bio[:index + 1]
        bio = textwrap.wrap(bio, max_chars_line, initial_indent="                                                   ")
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
            
        #data = {"header":author, "uri":uri, "type":"image"} 
        display_image(uri)
    
    return lines + "\n" + bio[:100]


if __name__ == "__main__":
    sys.stdout.write("\x1b[2J")
    sys.stdout.write("\x1b[0;0H")
    sys.stdout.write("\x1b[s")
    q = get_quotation()
    print(q)
    sys.stdout.write("\x1b[u")
    sys.stdout.write("\x1b[1B")
    #print("\x1b[0;0H")
    with open("images/zzzz", 'rb') as f:
        write_chunked({'a': 'T', 'f': 100}, f.read()) #f=100 is png;f=24->24bitRGB and f=32->32bit RGBA
    print("\n")
