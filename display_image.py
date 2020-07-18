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
#from images import GraphicsCommand, fsenc
#from kitty.utils import screen_size_function
import array
import fcntl
import termios
from PIL import Image
from dataclasses import dataclass, fields

try:
    fsenc = sys.getfilesystemencoding() or 'utf-8'
    codecs.lookup(fsenc)
except Exception:
    fsenc = 'utf-8'

#@dataclassa # no real need to do this as dataclass since
#getting the fields from a dataclass and just getting
#the annotations seems superficially pretty similar
class GraphicsCommand:
    a: str = 't'      # GRT_a = 't'  # action
    f: int = 32       #GRT_f = 32   # image data format
    t: str  = 'd'     # GRT_t = 'd'  # transmission medium
    s: int = 0        # sent image width
    v: int = 0        # sent image height
    S: int = 0        # size of data to read from file
    O: int = 0        # offset of data to read from file
    i: int = 0        # image id
    o: None = None    #Optional[GRT_o] = None  # type of compression
    m: int = 0        #GRT_m = 0    # 0 or 1 whether there is more chunked data
    x: int = 0        # left edge of image area to display
    y: int = 0        # top edge of image area to display
    w: int = 0        # image width to display
    h: int = 0        # image height to display
    X: int = 0        # X-offset within cell
    Y: int = 0        # Y-offset within cell
    c: int = 0        # number of cols to display image over
    r: int = 0        # number of rows to display image over
    z: int = 0        # z-index
    d: str = 'a'      #GRT_d = 'a'  # what to delete

    def serialize(self, payload = b''):
        items = []
        # if dataclass something like:
        #for k in fields(cmd):
            #val = getattr(self, k.name) and so on ...
        for k in GraphicsCommand.__annotations__:
            val = getattr(self, k)
            defval = getattr(GraphicsCommand, k)
            if val != defval and val is not None:
                items.append('{}={}'.format(k, val))

        ans = []
        w = ans.append
        w(b'\033_G')
        w(','.join(items).encode('ascii'))
        if payload:
            w(b';')
            w(payload)
        w(b'\033\\')
        return b''.join(ans)

    def clear(self):
        for k in GraphicsCommand.__annotations__:
            defval = getattr(GraphicsCommand, k)
            setattr(self, k, defval)

@dataclass
class ScreenSize():
    # @dataclass essentially creates an __init__ with these attributes
    rows: int
    cols: int
    width: int
    height: int
    cell_width: int
    cell_height: int
    
def calculate_in_cell_x_offset(width: int, cell_width: int, align: str):
    if align == 'left':
        return 0
    extra_pixels = width % cell_width
    if not extra_pixels:
        return 0
    if align == 'right':
        return cell_width - extra_pixels
    return (cell_width - extra_pixels) // 2

def get_screen_size():
    buf = array.array('H', [0, 0, 0, 0])
    fcntl.ioctl(sys.stdout, termios.TIOCGWINSZ, buf)
    rows, cols, width, height = tuple(buf)
    cell_width = width//(cols or 1)
    cell_height = height//(rows or 1)
    return ScreenSize(rows, cols, width, height, cell_width, cell_height)

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

def display_image(uri, w=None, h=None, erase=True):
    #global can_transfer_with_files
    try:
        response = requests.get(uri, timeout=5.0)
    except (requests.exceptions.ConnectionError,
            requests.exceptions.TooManyRedirects,
            requests.exceptions.ChunkedEncodingError,
            requests.exceptions.ReadTimeout) as e:
        print(f"requests.get({uri}) generated exception:\n{e}")
        return False

    if response.status_code != 200:
        print(f"status code = {response.status_code}")
        return False
        
    # it is possible to have encoding == None and ascii == True
    if response.encoding or response.content.isascii():
        print(f"{uri} returned ascii text and not an image")
        return False

    # this try/except is needed for occasional bad/unknown file format
    try:
        img = wand.image.Image(file=BytesIO(response.content))
    except Exception as e:
        print(f"wand.image.Image(file=BytesIO(response.content))"\
              f"generated exception from {uri} {e}")
        return False

    ww = img.width
    hh = img.height
    sq = ww if ww <= hh else hh
    if ww > hh:
        t = ((ww-sq)//2,(hh-sq)//2,(ww+sq)//2,(hh+sq)//2) 
    else:
        t= ((ww-sq)//2, 0, (ww+sq)//2, sq)
    img.crop(*t)
    # resize should take the image and enlarge it without cropping 
    if w and h:
        img.resize(w,h) #400x400

    # right now only able to send .png to kitty but kitty supports jpeg too
    #if img.format == 'JPEG':
    #    img.format = 'PNG'

    if erase:
        sys.stdout.write("\x1b_Ga=d\x1b\\") #delete image - note doesn't delete text
        sys.stdout.write("\x1b[1J") # - erase text up from cursor
        sys.stdout.flush()

    print() # for some reason this is necessary or images are not displayed
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
        # PNG is working without saving a file to disk
        f = BytesIO()
        img.save(f)
        img.close()
        f.seek(0)

        write_chunked({'a':'T', 'f':100}, f.read())

    else:
        print("format is not JPEG or PNG")
        return False

    print()
    sys.stdout.flush()
    return True

def display_blended_image(uri_0, uri_1, w=None, h=None, erase=True):
    images = []
    uris = [uri_0, uri_1]
    i = 0
    for uri in uris:
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
        if w and h:
            img.resize(w,h) #400x400

        # right now only able to send .png to kitty but kitty supports jpeg too
        if img.format == 'JPEG':
            img.format = 'PNG'

        #if erase:
        if 0:
            sys.stdout.write("\x1b_Ga=d\x1b\\") #delete image - note doesn't delete text
            sys.stdout.write("\x1b[1J") # - erase text up from cursor
            sys.stdout.flush()

        print() # for some reason this is necessary or images are not displayed
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
            # PNG is working without saving a file to disk
            f = BytesIO()
            img.save(f)
            img.close()
            f.seek(0)
            #images[i] = Image.open(f)
            img = Image.open(f)
            #print(f"{img.mode=}")
            if img.mode != "L":
                img = img.convert("L")
            #if img.mode != "RGB":
            #    img = img.convert("RGB")
            #print(f"{img=}")
            images.append(img)
            #i += 1

    img = Image.blend(images[0], images[1], .5)

    f2 = BytesIO()
    #p_img_2.save(f2, format='png')
    img.save(f2, format='png')
    f2.seek(0)

    write_chunked({'a':'T', 'f':100}, f2.read())

    print()
    sys.stdout.flush()

def blend_images(f1, f2, alpha):
    img1 = Image.open(f1)
    img2 = Image.open(f2)

    if img1.mode != img2.mode:
        print(img1)
        print(img2)
        sys.exit()
        #return f1 if img1.mode == "RGB" else f2

    try:
        img = Image.blend(img1, img2, alpha)
    except ValueError as e:
        # ValueError is when modes don't match and that shouldn't happen
        print()
        print()
        print(e)
        print(f"{img1.mode=}")
        print(f"{img2.mode=}")
        sys.exit(1)
        #return

    f = BytesIO()
    img.save(f, format='png')
    f.seek(0)
    return f

def show_image(f):
    write_chunked({'a':'T', 'f':100}, f.read())

def resize_show_image(f, w, h):
    img = Image.open(f) # PIL Image
    img = img.resize((w, h))
    g = BytesIO()
    img.save(g, format='png')
    g.seek(0)
    write_chunked({'a':'T', 'f':100}, g.read())

def generate_image(uri, w=None, h=None):

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
    if w and h:
        img.resize(w,h) #400x400

    # wand/imagemagick converts from JPEG to PNG
    # with the code below
    # should probably look for PIL[LOW] equivalent
    #if img.format == 'JPEG':
    #    img.format = 'PNG'

    if img.format != 'PNG':
        img.format = 'PNG'

    f = BytesIO()
    img.save(f)
    img.close()
    f.seek(0)
    img = Image.open(f)

    #print(f"before {img=}")
    if img.mode != "RGB":
        img = img.convert("RGB")
        f.seek(0)
    #print(f"after {img=}")

    img.save(f, format='png')
    f.seek(0)
    return f

    # so right now this will never be true
   # if img.format == 'JPEG':

   #     cmd = GraphicsCommand()

   #     fmt = 32 if img.alpha_channel else 24 # right now not using because 0 seems to work
   #     cmd.a = 'T'
   #     cmd.f = 0 # 0 seems to work and ? same as 32
   #     cmd.s = img.width
   #     cmd.v = img.height
   #     cmd.t = 't' # transmission media is [t]temporary file

   #     tf = NamedTemporaryFile(suffix='.rgba', delete=False)
   #     img.save(filename = tf.name)
   #     img.close()

   #     write_gr_cmd(cmd, standard_b64encode(os.path.abspath(tf.name).encode(fsenc)))

   # elif img.format == 'PNG':

   #     f = BytesIO()
   #     img.save(f)
   #     img.close()
   #     f.seek(0)
   #     img = Image.open(f)

   #     #print(f"before {img=}")
   #     if img.mode != "RGB":
   #         img = img.convert("RGB")
   #         f.seek(0)
   #     #print(f"after {img=}")

   #     img.save(f, format='png')
   #     f.seek(0)
   #     return f

def generate_image2(uri, w=None, h=None):

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
    if w and h:
        img.resize(w,h) #400x400

    # wand/imagemagick converts from JPEG to PNG
    # with the code below
    # should probably look for PIL[LOW] equivalent

    if img.format != 'PNG':
        img.format = 'PNG'

    f = BytesIO()
    img.save(f)
    img.close()
    f.seek(0)
    img = Image.open(f)

    if img.mode != "RGB":
        img = img.convert("RGB")
        f.seek(0)

    img.save(f, format='png')
    f.seek(0)
    return f,ww,hh

if __name__ == "__main__":
    display_image(sys.argv[1])
    display_blended_image(sys.argv[1], sys.argv[2])

