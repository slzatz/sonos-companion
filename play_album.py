'''
This simple little script enables you to play an album from the command line
'''
from operator import itemgetter 
from SolrClient import SolrClient
from config import ec_uri
import boto3
import json

album = input("What album do you want to play? ")

if not album:
    sys.exit()

s3 = boto3.resource('s3')
obj = s3.Object('sonos-scrobble','location')
location = obj.get()['Body'].read().decode('utf-8')
queue_name = 'echo_sonos_ct' if location=='ct' else 'echo_sonos'
print("location = ", location)
print("queue_name =", queue_name)

sqs = boto3.resource('sqs', region_name='us-east-1')
queue = sqs.get_queue_by_name(QueueName=queue_name)

solr = SolrClient(ec_uri+':8983/solr')
collection = 'sonos_companion'

s = 'album:' + ' AND album:'.join(album.split())
result = solr.query(collection, {'q':s, 'rows':25, 'fields':['score','track','uri','album'], 'sort':'score desc'})
if  result.docs:
    selected_album = result.docs[0]['album']
    tracks = sorted([t for t in result.docs], key=itemgetter('track'))

    # The "if t['album']==selected_album" below only comes into play if we retrieved tracks from more than one album
    uris = [t['uri'] for t in tracks if t['album']==selected_album]
    sqs_response = queue.send_message(MessageBody=json.dumps({'action':'play', 'uris':uris}))
    print("Status Code =", sqs_response['ResponseMetadata']['HTTPStatusCode'])
    print("I will play {} songs from {}".format(len(uris), selected_album))
else:
    print("I couldn't find {}. Try again.".format(album))


