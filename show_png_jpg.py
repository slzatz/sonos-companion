#!bin/python
'''
Takes a url as its sole argument and displays the image.

There are three current possiblities for handling the image.

1) If it's a PNG, "stream" the image and don't save it to disk.
2) If it's a JPEG, can convert into a PNG and then stream
3) Or if it's a JPEG, can save to a temporary file and display

'''
import sys
from base64 import standard_b64encode
import zlib
import wand.image
import requests
from io import BytesIO
import os
from tempfile import NamedTemporaryFile
from math import ceil
from images import GraphicsCommand, fsenc
from kitty.utils import screen_size_function

can_transfer_with_files = False
screen_size = None

def calculate_in_cell_x_offset(width: int, cell_width: int, align: str):
    if align == 'left':
        return 0
    extra_pixels = width % cell_width
    if not extra_pixels:
        return 0
    if align == 'right':
        return cell_width - extra_pixels
    return (cell_width - extra_pixels) // 2

def get_screen_size_function():
    global screen_size
    if screen_size is None:
        screen_size = screen_size_function()
    return screen_size

def get_screen_size():
    screen_size = get_screen_size_function()
    return screen_size()

def set_cursor(cmd, width: int, height: int, align: str):
    ss = get_screen_size()
    cw = int(ss.width / ss.cols)
    num_of_cells_needed = int(ceil(width / cw))
    if num_of_cells_needed > ss.cols:
        w, h = fit_image(width, height, ss.width, height)
        ch = int(ss.height / ss.rows)
        num_of_rows_needed = int(ceil(height / ch))
        cmd.c, cmd.r = ss.cols, num_of_rows_needed
    else:
        cmd.X = calculate_in_cell_x_offset(width, cw, align)
        extra_cells = 0
        if align == 'center':
            extra_cells = (ss.cols - num_of_cells_needed) // 2
        elif align == 'right':
            extra_cells = (ss.cols - num_of_cells_needed)
        if extra_cells:
            sys.stdout.buffer.write(b' ' * extra_cells)

# two functions below expect cmd to be a GraphicsCommand object
def write_gr_cmd(cmd, payload=None):
    sys.stdout.buffer.write(cmd.serialize(payload or b''))
    sys.stdout.flush()

def write_chunked2(cmd, data):
    if cmd.f != 100:
        data = zlib.compress(data)
        cmd.o = 'z'
    data = standard_b64encode(data)
    while data:
        chunk, data = data[:4096], data[4096:]
        cmd.m = 1 if data else 0
        write_gr_cmd(cmd, chunk)
        cmd.clear()

# two functions below expect cmd to be a dictionary
def serialize_gr_command(cmd, payload=None):
    cmd = ','.join(f"{k}={v}" for k,v in cmd.items())
    ans = []
    w = ans.append
    w(b'\033_G'), w(cmd.encode('ascii'))
    if payload:
       w(b';')
       w(payload)
    w(b'\033\\')
    return b''.join(ans)

def write_chunked(cmd, data):
    data = standard_b64encode(data)
    while data:
        chunk, data = data[:4096], data[4096:]
        m = 1 if data else 0
        cmd['m'] = m
        sys.stdout.buffer.write(serialize_gr_command(cmd, chunk))
        sys.stdout.flush()
        cmd.clear()

def display_image(uri):
    global can_transfer_with_files
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

    ww = img.width
    hh = img.height
    sq = ww if ww <= hh else hh
    if ww > hh:
        t = ((ww-sq)//2,(hh-sq)//2,(ww+sq)//2,(hh+sq)//2) 
    else:
        t= ((ww-sq)//2, 0, (ww+sq)//2, sq)
    img.crop(*t)
    # resize should take the image and enlarge it without cropping 
    img.resize(100,100) #400x400

    # right now only able to send .png to kitty but kitty supports jpeg too
    #if img.format == 'JPEG':
    #    img.format = 'PNG'

    sys.stdout.write("\x1b[1J") # - erase up
    sys.stdout.flush()
    print() # for some reason this is necessary or images are not displayed
    #sys.stdout.buffer.write(b'\033[J'), sys.stdout.flush()
    #set_cursor(cmd2, 100,100, 'center')

    if img.format == 'JPEG':

        cmd = GraphicsCommand()

        fmt = 32 if img.alpha_channel else 24 # right now not using because 0 seems to work
        cmd.a = 'T'
        cmd.f = 0 # 0 seems to work and ? same as 32
        cmd.s = img.width
        cmd.v = img.height
        cmd.t = 't' # transmission media is [t]temporary file

        tf = NamedTemporaryFile(suffix='.rgba', delete=False)
        img.save(filename = tf.name)
        img.close()

        write_gr_cmd(cmd, standard_b64encode(os.path.abspath(tf.name).encode(fsenc)))

    elif img.format == 'PNG':

        # PNG is [f]ormat = 100
        # this will be used for png where you don't need a temp file
        f = BytesIO()
        img.save(f)
        img.close()
        f.seek(0)

        write_chunked({'a':'T', 'f':100}, f.read())

    print()
    sys.stdout.flush()

if __name__ == "__main__":
    display_image(sys.argv[1])
