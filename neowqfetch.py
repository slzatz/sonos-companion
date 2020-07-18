#!/home/slzatz/sonos-companion/bin/python

'''
Uses wikiquote for quotes and wikipedia for bio and images
Can be invoked with a name in quotes
or without anything on command line and will pick random
quote
'''

import sys
from io import BytesIO
from math import ceil
import sqlite3
import textwrap
from display_image import show_image, get_screen_size, resize_show_image

db_file = "/home/slzatz/sonos-companion/wq.db"
display_size = 125

conn = sqlite3.connect(db_file)
cur = conn.cursor()

if __name__ == "__main__":
    '''  
    Displays image, quote and bio of select authors
    '''

    line_count = 2
    x = get_screen_size()
    if x.cell_width == 0:
        sys.exit(1)
    
    # bug that values sometimes 2x what they should be
    if x.cell_width > 12:
        x.width = x.width//2
        x.height = x.height//2
        x.cell_width = x.cell_width//2
        x.cell_height = x.cell_height//2

    if len(sys.argv) == 1:

        cur.execute("SELECT authors.id, authors.name,authors.bio, quote FROM authors INNER JOIN quotes ON " \
                "authors.id=quotes.author_id ORDER BY RANDOM() LIMIT 1;")
        row = cur.fetchone()
        author_id, name, bio, quote = row 

    else:

        sql = "SELECT authors.id,authors.name,authors.bio,quote FROM authors " \
              "INNER JOIN quotes ON authors.id=quotes.author_id AND authors.name=? ORDER BY RANDOM() LIMIT 1;"

        cur.execute(sql, (sys.argv[1].title(),))
        row = cur.fetchone()
        author_id, name, bio, quote = row 

    cur.execute("SELECT image,size FROM images WHERE author_id=? ORDER BY RANDOM() LIMIT 1;", (author_id,))
    row = cur.fetchone()
    image = BytesIO(row[0])
    image_size = row[1]
    indent_cols = ceil(display_size/x.cell_width)
    indent = indent_cols * ' '
    max_chars_line = x.cols - 5

    quote = textwrap.wrap(quote, max_chars_line, initial_indent=indent, subsequent_indent=indent)
    line_count += len(quote)
    quote = "\n".join(quote)

    # just using one sentence bios but bios have up to 10 sentences
    bio = bio[:bio.find('.') + 1]
    bio = textwrap.wrap(bio, max_chars_line, initial_indent=indent, subsequent_indent=indent)
    line_count += len(bio)
    bio = "\n".join(bio)

    print() # line feed
    q = f"\x1b[3m{quote}\x1b[0m\n{indent}-- \x1b[1m{name}\x1b[0m\n\n{bio}"
    print(q)

    sys.stdout.buffer.write(f"\x1b[{line_count}A".encode('ascii')) # move back up line_count lines

    if display_size == image_size:
        show_image(image)
    else:
        resize_show_image(image, display_size, display_size)
    print()

    image_rows = display_size//x.cell_height
    if line_count > image_rows:
        print((line_count-image_rows)*"\n")
