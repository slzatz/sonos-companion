'''
uses boto3
Gets album titles so they can be used by alexa custom slot
'''

import json
import boto3
from boto3.dynamodb.conditions import Attr, Key
from decimal import Decimal
from time import time
from datetime import datetime, timedelta
import requests
import config as c

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('amazon_music')

result = table.scan()

if result['Count']:

    f =  open('albums', 'w')
    albums = {}
    for track in result['Items']:
        albums[track.get('album', 'Missing')] = 1
    for album in sorted(albums.keys()):
        try:
            print("{}".format(album)) 
            f.write(album)
            f.write('\n')
        except (UnicodeDecodeError, UnicodeEncodeError):
            print("Unicode error")

    f.close()

