'''
uses boto3

>>> rrr = table.scan(Limit=10, FilterExpression=Attr("ts").gt(Decimal(z)-1000000))
>>> rrr
{u'Count': 1, u'Items': [{u'album': u'I Carry Your Heart With Me (c)', u'artist': u'Hem', u'title': u'The Part Where You Let Go', 
u'ts': Decimal('1445364875'), u'date': u'2007 - Home
 Again, Home Again', u'scrobble': u'27'}], u'LastEvaluatedKey': {u'ts': Decimal('1442178047'), u'artist': u'Leo Kottke'}, 
u'ScannedCount': 10, 'ResponseMetadata': {'HTTPStatusCode':
200, 'RequestId': 'P3U632LF4NKTGP6MEJ228MLRDBVV4KQNSO5AEMVJF66Q9ASUAAJG'}}

{u'Count': 0, u'Items': [], u'LastEvaluatedKey': {u'ts': Decimal('1442178047'), u'artist': u'Leo Kottke'}, u'ScannedCount': 10, 
'ResponseMetadata': {'HTTPStatusCode': 200, 'RequestId
': '2UVLSDD8147256OV6P0T03IBV7VV4KQNSO5AEMVJF66Q9ASUAAJG'}}
'''

import json
import boto3
from boto3.dynamodb.conditions import Attr
from decimal import Decimal
from time import time
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('scrobble')

z = time()
result = table.scan(FilterExpression=Attr('ts').gt(Decimal(z)-300))

if result['Count']:

    songs = result['Items']
    y = [(s.get('ts', ''), s.get('title', ''), s.get('artist', ''), s.get('album', '')) for s in songs]
    y.sort(key = lambda x:x[0], reverse=True)

    for x in y:
        print "{}: {} - {} - {}".format(datetime.fromtimestamp(x[0]).strftime("%a %I:%M%p"), x[1], x[2], x[3])

    last_song = y[0]

    output_speech = "Song is {} Artist is {} Album is {}".format(last_song[1], last_song[2], last_song[3])

else:
    output_speech = "No song appears to be playing"

output_type = 'PlainText'

response = {'outputSpeech': {'type':output_type,'text':output_speech},"shouldEndSession":True, "sessionAttributes":{}}

print response
