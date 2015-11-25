'''
uses boto3
enables you to check on scrobbles
'''

import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal
import time

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('scrobble_new')

days = input("How many days do you want to go back? ")

result = table.query(KeyConditionExpression=Key('location').eq('nyc') & Key('ts').gt(Decimal(time.time()-int(days)*86400)), ScanIndexForward=False) #by default the sort order is ascending

tracks = result['Items']
for track in tracks:
    print(track.get('artist'), track.get('title'))

