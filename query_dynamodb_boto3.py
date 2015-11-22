'''
uses boto3
This program was used to test whether when you scrobble songs to dynamodb that they
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
'''

import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from time import time

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('scrobble_new')

result = table.query(KeyConditionExpression=Key('location').eq('nyc'), ScanIndexForward=False, Limit=5) #by default the sort order is ascending
print(result)

track = result['Items'][0]
if track['ts'] > 0: #Decimal(time.time())-300:
    output_speech = "The song is {}. The artist is {} and the album is {}.".format(track.get('title','No title'), track.get('artist', 'No artist'), track.get('album', 'No album'))
    print(output_speech)
