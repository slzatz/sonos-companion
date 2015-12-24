'''
uses boto3
enables you to check on scrobbles
        'location':c.location,
        'artist':track.get('artist'),
        'ts': int(time.time()), 
        'title':track.get('title'),
        'album':track.get('album'),
        'date':track.get('date')}
'''

import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal
import time

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('scrobble_new')

days = input("How many days do you want to go back? ")
location = input("Which location ('nyc' or 'ct')? ")

result = table.query(KeyConditionExpression=Key('location').eq(location) & Key('ts').gt(Decimal(time.time()-int(days)*86400)), ScanIndexForward=False) #by default the sort order is ascending

tracks = result['Items']
for track in tracks:
    print("'{artist}' - '{title}' from '{album}' played from {location}".format(**track))

