#!bin/python
'''
python3 script: places images in sonos-companion/images 
then open image for display on kitty terminal
should not have to save the image to disk

'''
import sys
from base64 import standard_b64encode
import json
import time
import zlib
import wand.image
import requests
from io import BytesIO
import os
from tempfile import NamedTemporaryFile
from time import sleep
from math import ceil

from images import GraphicsCommand, fsenc
from kitty.utils import TTYIO, screen_size_function

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

def serialize_gr_command(cmd, payload=None):
    #cmd = ','.join('{}={}'.format(k, v) for k, v in cmd.items())
    cmd = ','.join(f"{k}={v}" for k,v in cmd.items())
    ans = []
    w = ans.append
    w(b'\033_G'), w(cmd.encode('ascii'))
    #print(f"{ans=}")
    if payload:
       w(b';')
       w(payload)
    w(b'\033\\')
    #print(f"{b''.join(ans)[:100]=}")
    return b''.join(ans)

def write_chunked(cmd, data):
    #print("In write_chunked\n") 
    #if cmd['f'] != 100:
    #    data = zlib.compress(data)
    #    cmd['o'] = 'z'
    data = standard_b64encode(data)
    while data:
        chunk, data = data[:4096], data[4096:]
        m = 1 if data else 0
        cmd['m'] = m
        sys.stdout.buffer.write(serialize_gr_command(cmd, chunk))
        sys.stdout.flush()
        cmd.clear()

#received = b''
#responses = {}
#def parse_responses():
#   for m in re.finditer(b'\033_Gi=([1|2]);(.+?)\033\\\\', received):
#       iid = m.group(1)
#       print(f"{iid=}")
#       if iid in (b'1', b'2'):
#           iid_ = int(iid.decode('ascii'))
#           if iid_ not in responses:
#               responses[iid_] = m.group(2) == b'OK'
#
#def more_needed(data):
#    #nonlocal received
#    global received
#    received += data
#    print(f"{received=}")
#    parse_responses()
#    return 1 not in responses or 2 not in responses

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


    # right now only able to send .png to kitty but kitty supports jpeg too
    #if img.format == 'JPEG':
    #    img.format = 'PNG'

    cmd2 = GraphicsCommand()

    if img.format == 'JPEG':
        fmt = 32 if img.alpha_channel else 24
        cmd = {'a':'T', 'f': fmt, 't':'d', 's':100, 'v':100, 'S':int(100*100*fmt/8)}
        #cmd = {'a':'T', 'f': fmt, 't':'d', 's':100, 'v':100}
        #cmd = {'a':'T', 'f': 32, 't':'d', 's':100, 'v':100}
        #cmd = {'f': fmt, 't':'d', 's':800, 'v':800}
        cmd2.a = 'T'
        cmd2.f = 0
        cmd2.s = img.width
        cmd2.v = img.height
        cmd2.t = 't'
    elif img.format == 'PNG':
        fmt = 100;
        cmd = {'a':'T', 'f':100}
        #cmd2.a = 'q'
        cmd2.a = 'T'
        cmd2.f = fmt
        #cmd2.t = 's'

    print(f"{fmt=}")

    ww = img.width
    hh = img.height
    sq = ww if ww <= hh else hh
    if ww > hh:
        t = ((ww-sq)//2,(hh-sq)//2,(ww+sq)//2,(hh+sq)//2) 
    else:
        t= ((ww-sq)//2, 0, (ww+sq)//2, sq)
    #img.crop(*t)
    # resize should take the image and enlarge it without cropping 
    #img.resize(100,100) #400x400

    tf = NamedTemporaryFile(suffix='.rgba', delete=False)
    #img.save(filename = "images/test")
    img.save(filename = tf.name)
    img.close()
    #for x in os.listdir("/tmp"):
    #    print(x)

    #f = BytesIO()
    #img.save(f)
    #img.close()
    #f.seek(0)
            
    #sys.stdout.write("\x1b_Ga=d\x1b\\") #delete image - works but doesn't delete old text - kitty graphics command
    #sys.stdout.write("\x1b[1J") # - erase up
    print() # for some reason this is necessary or images are not displayed

    #f = open("images/test.rgba", 'rb')
    #write_chunked({'a': 'T', 'f': fmt}, f.read())
    #print(f"{cmd=}")
    #print("before hello" , end="") 
    #write_chunked(cmd, f.read())
    #write_chunked2(cmd2, f.read())
    cmd = "a=T,f=24,t=f;s=100,v=100"
    #payload = bytes(tf.name)
    payload = b"images/test"
    payload=None 
    #payload = standard_b64encode(payload)
    ans = []
    w = ans.append
    w(b'\033_G'), w(cmd.encode('ascii'))
    #print(f"{ans=}")
    w(b';')
    if payload:
       w(b';')
       w(payload)
    w(b'\033\\')
    #print(f"{b''.join(ans)[:100]=}")
    #print()
    cmd3 = GraphicsCommand()
    cmd3.a = 'q'
    cmd3.i = 1
    cmd3.s = 1
    cmd3.v = 1
    #write_gr_cmd(cmd3, standard_b64encode(os.path.abspath("abcd").encode(fsenc)))
    sys.stdout.flush()
    received = b''
    responses = {}
#    def parse_responses():
#       for m in re.finditer(b'\033_Gi=([1|2]);(.+?)\033\\\\', received):
#           iid = m.group(1)
#           print(f"{iid=}")
#           if iid in (b'1', b'2'):
#               iid_ = int(iid.decode('ascii'))
#               if iid_ not in responses:
#                   responses[iid_] = m.group(2) == b'OK'
#
#    def more_needed(data):
#        nonlocal received
#        received += data
#        print(f"{received=}")
#        sys.stdout.flush()
#        parse_responses()
#        return 1 not in responses or 2 not in responses
#
#
#    with NamedTemporaryFile() as f:
#        f.write(b'abcd'), f.flush()
#        gc=GraphicsCommand()
#        gc.a = 'q'
#        gc.s = gc.v = gc.i = 1
#        write_gr_cmd(gc, standard_b64encode(b'abcd'))
#        gc.t = 'f'
#        gc.i = 2
#        write_gr_cmd(gc, standard_b64encode(f.name.encode(fsenc)))
#        resp = b''
#        resp0 = b''
#        while resp[-2:] != b'\x1b\\':
#            resp += sys.stdin.buffer.read(1)
#        while resp0[-2:] != b'\x1b\\':
#            resp0 += sys.stdin.buffer.read(1)
#        # with TTYIO() as io:
#        #    print("TTYIO")
#
#       #     io.recv(more_needed, timeout=2.0)
#        print(f"{resp=};{resp0=}")
#    with NamedTemporaryFile() as tmpf:
#        tmpf.write(bytearray([0xFF] * 3))
#        tmpf.flush()
#        for cmd in self._format_cmd_str(
#                {'a': 'q', 'i': 1, 'f': 24, 't': 'f', 's': 1, 'v': 1, 'S': 3},
#                payload=base64.standard_b64encode(tmpf.name.encode(self.fsenc))):
#            sys.stdout.buffer.write(cmd)
#        sys.stdout.flush()
#        resp = b''
#        while resp[-2:] != b'\x1b\\':
#            resp += sys.stdin.stdbin.read(1)
#    # set the transfer method based on the response
#    # if resp.find(b'OK') != -1:
#    if b'OK' in resp:
#        self.stream = False
#    elif b'EBADF' in resp:
#        self.stream = True
#    else:
#        raise ImgDisplayUnsupportedException(
#            'kitty replied an unexpected response: {}'.format(resp))
#
#
    sys.stdout.buffer.write(b'\033[J'), sys.stdout.flush()


    #print(f"{responses=}")
    #sys.stdout.flush()
    #print("hello", end="") 
    #sys.stdout.write("\x1b[0J")
    #sys.stdout.flush()
    sys.stdout.write(" ")
    sys.stdout.flush()
    set_cursor(cmd2, 100,100, 'center')
    resp1 = b''
    #write_gr_cmd(cmd2, standard_b64encode(os.path.abspath(f"{tf.name}").encode(fsenc)))
    #for x in os.listdir("/tmp"):
    #    print(x)
    #sys.stdout.flush()
    write_gr_cmd(cmd2, standard_b64encode(os.path.abspath(tf.name).encode(fsenc)))
   # while resp1[-2:] != b'\x1b\\':
    resp1 += sys.stdin.buffer.readline()
    #print(f"{resp1=}")
    print()
    b''.join(ans)
    #sys.stdout.buffer.write(b''.join(ans))
    #sys.stdout.flush()
    #print(f"{responses=}")


if __name__ == "__main__":
    #print(f"{sys.argv[1]=}")
    #if not sys.stdout.isatty():
    #    sys.stdout = open(os.ctermid(), 'w')
    #stdin_data = sys.stdin.buffer.read()
    #sys.stdin.close()
    #sys.stdin = open(os.ctermid(), 'r')
    display_image(sys.argv[1])
