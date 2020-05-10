#!/home/slzatz/sonos-companion/bin/python

import sys
from io import BytesIO
from math import ceil
import sqlite3
import textwrap
from display_image import show_image, get_screen_size

db_file = "/home/slzatz/sonos-companion/gr.db"

conn = sqlite3.connect(db_file)
cur = conn.cursor()

if __name__ == "__main__":
    '''  
    id integer PRIMARY KEY,
    book_gr_id INTEGER NOT NULL,
    quote text NOT NULL,
    FOREIGN KEY(book_gr_id) REFERENCES books (gr_id),
    UNIQUE(quote)
    '''

    line_count = 2
    x = get_screen_size()
    author_image_size = 400

    indent_cols = ceil(author_image_size/x.cell_width)
    indent = indent_cols * ' '
    max_chars_line = x.cols - 5
    authoriz_image_size = 400

    cur.execute("SELECT book_gr_id,quote FROM quotes ORDER BY RANDOM() LIMIT 1;")
    row = cur.fetchone()

    book_gr_id = row[0]
    quote = textwrap.wrap(row[1], max_chars_line, initial_indent=indent, subsequent_indent=indent)
    line_count += len(quote)
    quote = "\n".join(quote)

    cur.execute("SELECT title,author_id FROM books WHERE gr_id=?", (book_gr_id,))
    row = cur.fetchone()
    title = row[0]
    author_id = row[1]

    cur.execute("SELECT name,bio FROM authors WHERE id=?", (author_id,))
    row = cur.fetchone()
    name = row[0]
    bio = textwrap.wrap(row[1], max_chars_line, initial_indent=indent, subsequent_indent=indent)
    line_count += len(bio)
    bio = "\n".join(bio)

    cur.execute("SELECT image FROM images WHERE author_id=?", (author_id,))
    row = cur.fetchone()
    image = BytesIO(row[0])
    print() # line feed

    q = f"\x1b[3m{quote}\x1b[0m\n{indent}-- \x1b[1m{title} by {name}\x1b[0m\n\n{bio}"
    print(q)

    sys.stdout.buffer.write(f"\x1b[{line_count}A".encode('ascii')) # move back up 9 lines
    sys.stdout.buffer.write(b"\x1b[7B") #move down 8 lines to near middle of image
    print("  retrieving photo ...")
    sys.stdout.buffer.write(b"\x1b[8A") # move back up 9 lines

    show_image(image)

    print()

    if line_count > 22: 
        print((line_count-22)*"\n")
