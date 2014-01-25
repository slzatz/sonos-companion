import httplib2
import sys
import argparse

from apiclient import discovery

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("first_name")
parser.add_argument("last_name")
args = parser.parse_args()
#print(args.artist)


def main(artist):
  # Create an httplib2.Http object to handle our HTTP requests .
  http = httplib2.Http()

  # Construct the service object for the interacting with the CustomSearch API.
  service = discovery.build('customsearch', 'v1',  developerKey='AIzaSyCe7pbOm0sxYXwMWoMJMmWvqBcvaTftRC0', http=http)

  z = service.cse().list(q=artist, searchType='image', imgSize='medium', num=5, cx='007924195092800608279:0o2y8a3v-kw').execute() 

  #d = [{k: a[k] for k in ['link','image'] } for a in z['items']] #works but really want what's below

  q = []

  for x in z['items']:
    y = {}
    y['image'] = {k:x['image'][k] for k in ['height','width']}
    y['link'] = x['link']
    q.append(y)

  #[{'image':{k:x['image'][k] for k in ['height','width']},'link':x['link']} for x in z['items']]

  #{ your_key: old_dict[your_key] for your_key in your_keys }

  print q
  
if __name__ == '__main__':
  artist = args.first_name + ' ' +args.last_name
  main(artist)
