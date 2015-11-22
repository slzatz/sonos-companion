'''
uses boto3
This program was used to transfer data from one dynamodb to another when creating a new scrobble db
Main reason was to create a location field so I know where the song was played but haven't really starting using it
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

import json
import boto3
from boto3.dynamodb.conditions import Attr, Key
from decimal import Decimal
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
old_table = dynamodb.Table('scrobble')
new_table = dynamodb.Table('scrobble_new')

result = old_table.scan()

tracks = result['Items']
for track in tracks:
    data = {
            'location':'nyc',# or 'NYC', 'CT' to use the following to get last song table.query(KeyConditionExpression=Key('location').eq('nyc'), Limit=1)
            'artist':track.get('artist'),
            'ts': int(track.get('ts')), # shouldn't need to truncate to an integer but getting 20 digits to left of decimal point in dynamo
            'title':track.get('title'),
            'album':track.get('album'),
            'date':track.get('date'),
            'scrobble':int(track.get('scrobble',0))} #it's a string although probably should be converted to a integer

    data = {k:v for k,v in data.items() if v} 
    try:
        new_table.put_item(Item=data)
    except Exception as e:
        print "Exception trying to write dynamodb scrobble table:", e
    else:
        print "{} sent successfully to dynamodb".format(json.dumps(data))
