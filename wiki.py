#!/home/slzatz/sonos-companion/bin/python

'''
Gets summary of a wikipedia topic.
Made some modifications to wikipedia.py
'''

import re
from random import choice
import html
import wikipedia
import textwrap
import sys
from display_image import display_image

max_chars_line = 100

def get_page(topic):
    try:
        page = wikipedia.page(topic) # I changed auto_suggest = False to the default (I changed page function in wikipedia.py
    except Exception as e:
        print(f"Couldn't find {topic} wikipedia: {e}")
        return
    return page

def format_summary(page):
    # currently splits into 10 sentences
    line_count = 2
    indent = 45*" "
    summary = ' '.join(re.split(r'(?<=[.:;])\s', page.summary)[:10])
    summary = textwrap.wrap(summary, max_chars_line, initial_indent=indent, subsequent_indent=indent)
    line_count += len(summary)
    summary = "\n".join(summary)
    return f"{indent}\x1b[1m{page.title}\x1b[0m\n\n\x1b[3m{summary}\x1b[0m", line_count


# not in use and either is slz mod of wikipedia.py summary2
def get_summary(topic):
    line_count = 2
    indent = 45*" "

    try:
        page,summary = wikipedia.summary2(topic, sentences=10) # auto_suggest = True is default (I changed page function in wikipedia.py
    except Exception as e:
        print(f"Couldn't find {topic} wikipedia: {e}")
        return

    summary = textwrap.wrap(summary, max_chars_line, initial_indent=indent, subsequent_indent=indent)
    line_count += len(summary)
    summary = "\n".join(summary)
    return f"{indent}\x1b[1m{page.title}\x1b[0m\n\n\x1b[3m{summary}\x1b[0m", line_count, page

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
    print() # line feed
    # Note saving and restoring cursor position didn't work when there was scrolling
    # but counting lines works
    if len(sys.argv) < 2:
        print("You need to enter a topic!")
        sys.exit()
    topic = sys.argv[1]
    #summary, line_count, page = get_summary(topic)
    page = get_page(topic)
    if not page:
        sys.exit()
    summary,line_count = format_summary(page)
    print(summary)
    sys.stdout.buffer.write(f"\x1b[{line_count}A".encode('ascii')) # move back up line_count lines
    sys.stdout.buffer.write(b"\x1b[7B") #move down 7 lines to near middle of image
    print("  retrieving photo ...")
    sys.stdout.buffer.write(b"\x1b[9A") # move back up 9 lines
    uri = get_wikipedia_image_uri(page) 
    if uri:
        display_image(uri, 400, 400, erase=False)    
    else:
        print("No image")
    print()
    if line_count > 22: 
        print((line_count-22)*"\n")
