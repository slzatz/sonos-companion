import sys
import wand.image
import requests
from io import BytesIO
from base64 import standard_b64encode

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
    print("In write_chunked\n") 
    data = standard_b64encode(data)
    while data:
        chunk, data = data[:4096], data[4096:]
        m = 1 if data else 0
        cmd['m'] = m
        sys.stdout.buffer.write(serialize_gr_command(cmd, chunk))
        sys.stdout.flush()
        cmd.clear()

def display_image(image):
    '''image = sqlalchemy image object'''
    print("\n*****\n", image.link)
    try:
        response = requests.get(image.link, timeout=5.0)
    except (requests.exceptions.ConnectionError,
            requests.exceptions.TooManyRedirects,
            requests.exceptions.ChunkedEncodingError,
            requests.exceptions.ReadTimeout) as e:
        print(f"requests.get({image.link}) generated exception:\n{e}")
        #image.ok = False
        #session.commit()
        #print(f"{image.link} ok set to False")
        return

    print(f"status code = {response.status_code}")
    if response.status_code != 200:
        print(f"{image.link} returned a {response.status_code}")
        #image.ok = False
        #session.commit()
        #print(f"{image.link} ok set to False")
        return
        
    # it is possible to have encoding == None and ascii == True
    if response.encoding or response.content.isascii():
        print(f"{image.link} returned ascii text and not an image")
        #image.ok = False
        #session.commit()
        #print(f"{image.link} ok set to False")
        return

    # this try/except is needed for occasional bad/unknown file format
    try:
        img = wand.image.Image(file=BytesIO(response.content))
    except Exception as e:
        print(f"wand.image.Image(file=BytesIO(response.content))"\
              f"generated exception from {image.link} {e}")
        #image.ok = False
        #session.commit()
        #print(f"{image.link} ok set to False")
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

    with open("images/zzzz", 'rb') as f:
        write_chunked({'a': 'T', 'f': 100}, f.read())
