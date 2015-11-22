'''
uses boto3
This program was used to test some querying strategies which may be less important with moving stuff to cloudsearch
Note some of these indexes have probably been eliminated
could be picked up by using boto3 to check on them

rrr = table.scan(Limit=10, FilterExpression=Attr("ts").gt(Decimal(z)-1000000))
rrr
{u'Count': 1, u'Items': [{u'album': u'I Carry Your Heart With Me (c)', u'artist': u'Hem', u'title': u'The Part Where You Let Go', 
u'ts': Decimal('1445364875'), u'date': u'2007 - Home
 Again, Home Again', u'scrobble': u'27'}], u'LastEvaluatedKey': {u'ts': Decimal('1442178047'), u'artist': u'Leo Kottke'}, 
u'ScannedCount': 10, 'ResponseMetadata': {'HTTPStatusCode':
200, 'RequestId': 'P3U632LF4NKTGP6MEJ228MLRDBVV4KQNSO5AEMVJF66Q9ASUAAJG'}}

if there are not results:
{u'Count': 0, u'Items': [], u'LastEvaluatedKey': {u'ts': Decimal('1442178047'), u'artist': u'Leo Kottke'}, u'ScannedCount': 10, 
'ResponseMetadata': {'HTTPStatusCode': 200, 'RequestId
': '2UVLSDD8147256OV6P0T03IBV7VV4KQNSO5AEMVJF66Q9ASUAAJG'}}
'scrobble_new
'''

import json
import boto3
from boto3.dynamodb.conditions import Attr, Key
from decimal import Decimal
from time import time
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('amazon_music')

#result = table.query(KeyConditionExpression=Key('album').eq("Children Running Through"))
#result = table.query(FilterExpression=Attr('artist').eq("Patty Griffin"), KeyConditionExpression=Key('album').eq("Children Running Through"))

#this worked but turned out since I needed to search on title too for some searches it was easier to just create an artist-title global secondary index
#result = table.query(IndexName='artist-index', KeyConditionExpression=Key('artist').eq('Neil Young'), FilterExpression=Attr('title').eq('After the Gold Rush'))

#this works and is the play neil young's after the gold rush
#result = table.query(IndexName='artist-title-index', KeyConditionExpression=Key('artist').eq('Patty Griffin') & Key('title').eq('Mad Mission'))
#The below this works
#result = table.query(IndexName='artist-title-index', KeyConditionExpression=Key('artist').eq('Patty Griffin'))
#below doesn't work because you always need the partition key in the search and the partition is artist
#result = table.query(IndexName='artist-title-index', KeyConditionExpression=Key('title').eq('After the Gold Rush'))
#The below won't work either because you always need the partition key in the search and the partition is album
#result = table.query(KeyConditionExpression=Key('title').eq('After the Gold Rush'))
result = table.query(IndexName='title-index', KeyConditionExpression=Key('title').eq('After the Gold Rush'))

if result['Count']:

    print(json.dumps(result).encode('cp1252', errors='replace'))
    songs = result['Items']
    y = [(s.get('title', ''), s.get('artist', ''), s.get('album', ''), s.get('uri', '')) for s in songs]
    for x in y:
        print("{}: {} - {} - {}".format(x[0], x[1], x[2], x[3]).encode('cp1252', errors='replace')) #yes, this is needed in python3 b/o windows terminal being cp1252

