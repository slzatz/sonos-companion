#!/home/slzatz/sonos-companion/bin/python

import sys
from io import BytesIO
from math import ceil
import sqlite3
import textwrap
from display_image import show_image, get_screen_size

db_file = "/home/slzatz/sonos-companion/wq.db"

conn = sqlite3.connect(db_file)
cur = conn.cursor()

if __name__ == "__main__":
    '''  
    Displays image, quote and bio of select authors
    '''

    line_count = 2
    x = get_screen_size()

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

    cur.execute("SELECT image,size FROM images WHERE author_id=?", (author_id,))
    row = cur.fetchone()
    image = BytesIO(row[0])
    author_image_size = row[1]
    indent_cols = ceil(author_image_size/x.cell_width)
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

    show_image(image)
    print()

    image_rows = author_image_size//x.cell_height
    if line_count > image_rows:
        print((line_count-image_rows)*"\n")
