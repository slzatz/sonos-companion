'''
add tracks to the queue and optionally create a playlist
There is also create_playlist_from_queue.py that has you put the songs on the queue
(from a Sonos playlist or whatever) and creates a playlist from the queue 
There is also a create_playlist.py that is similar
'''
from SolrClient import SolrClient
from config import ec_uri
import boto3
import botocore
import json
import sys
import os
from time import sleep

solr = SolrClient(ec_uri+':8983/solr')
collection = 'sonos_companion'

s3 = boto3.resource('s3')
obj = s3.Object('sonos-scrobble','location')
location = obj.get()['Body'].read().decode('utf-8')
queue_name = 'echo_sonos_ct' if location=='ct' else 'echo_sonos'
print("location = ", location)
print("queue_name =", queue_name)
sqs = boto3.resource('sqs', region_name='us-east-1')
queue = sqs.get_queue_by_name(QueueName=queue_name)

s3 = boto3.resource('s3')
s3obj = s3.Object('sonos-scrobble', 'queue')

sqs_response = queue.send_message(MessageBody=json.dumps({'action':'get sonos queue'}))
sleep(1)

try:
    z = s3obj.get()['Body'].read()
except botocore.exceptions.ClientError as e:
    if e.response['Error']['Code'] == "NoSuchKey":
        print('NoSuchKey')
    raise e
else:
    playlist = json.loads(z.decode('utf-8'))

for n,(id_,uri) in enumerate(playlist,1):
    s = 'id:' + '"{}"'.format(id_)
    result = solr.query(collection, {'q':s, 'rows':1, 'fl':['title', 'artist', 'album', 'uri']}) 
    track = result.docs[0]
    #count = result.get_results_count()
    try:
        print(' ')
        print(n)
        print('artist: ' + track['artist'])
        print('album: ' + track['album'])
        print('song: ' + track['title'])
        print('uri: ' + track['uri'])
    except Exception as e:
        print(e)

sys.exit()

res = input("Do you want to create a playlist and upload to s3 (y or n) ? ")
if res.lower().startswith('n'):
    sys.exit()

playlist_name = input("What do you want to call the playlist that will be uploaded to s3 [Note: will be changed to lower case]? ")
playlist_name = playlist_name.lower()

s3 = boto3.resource('s3')
object = s3.Object('sonos-playlists', playlist_name)
try:
    z = object.get()['Body'].read()
except botocore.exceptions.ClientError as e:
    if e.response['Error']['Code'] == "NoSuchKey":
        print("Playlist '{}' does not exist".format(playlist_name))
    else:
        raise e
else:
    res = input("Playlist '{}' exists - do you want to replace it?(y or n) ".format(playlist_name))
    if res.lower().startswith('n'):
        sys.exit()

s3 = boto3.client('s3')
playlist = json.dumps(playlist)
response = s3.put_object(Bucket='sonos-playlists', Key=playlist_name, Body=playlist)
print("response to s3 put =",response)
