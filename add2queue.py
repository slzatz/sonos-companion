'''
add tracks to the queue and optionally create a playlist
There is also create_playlist_from_queue.py that has you put the songs on the queue
(from a Sonos playlist or whatever) and creates a playlist from the queue 
There is also a create_playlist.py that is similar
Note this depends on the master that echo_check.py has selected
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
s3_location = s3.Object('sonos-scrobble','location')
location = s3_location.get()['Body'].read().decode('utf-8')
s3_master = s3.Object('sonos-scrobble','master/'+location)
master = s3_master.get()['Body'].read().decode('utf-8')
queue_name = 'echo_sonos_ct' if location=='ct' else 'echo_sonos'
print("location =", location)
print("queue_name =", queue_name)
print("master =", master)

sqs = boto3.resource('sqs', region_name='us-east-1')
queue = sqs.get_queue_by_name(QueueName=queue_name)
existing_queue = []
playlist = []

res = input("If there are songs in the queue, do you want to replace or add to them(r or a)? ")

if res.lower()=='a':
    action = 'add'
    s3 = boto3.resource('s3')
    s3obj = s3.Object('sonos-scrobble', 'queue')

    sqs_response = queue.send_message(MessageBody=json.dumps({'action':'get sonos queue'}))
    sleep(2)

    try:
        z = s3obj.get()['Body'].read()
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "NoSuchKey":
            exists = False
        else:
            raise e
    else:
        exists = True
        
    if not exists:
        print("Could not bring back queue")
    else:
        existing_queue = json.loads(z.decode('utf-8')) # you are just going to create duplicate playlists if you do this
        n = 1
        for track in existing_queue:
            print(n, track[0],track[1])
            n+=1

else:
    action = 'play'

try:
    while 1:
        track_title = input("\nwhat is the title of the track that you want to add to the queue (Ctrl-C if done)? ")
        s = 'title:' + ' AND title:'.join(track_title.split())
        result = solr.query(collection, {'q':s, 'rows':10, 'fl':['score', 'id', 'uri', 'title', 'artist', 'album'], 'sort':'score desc'}) 
        tracks = result.docs
        count = result.get_results_count()
        if count==0:
            print("Didn't find any tracks\n")
        elif count==1:
            track = tracks[0]
            try:
                print('id: ' + track['id'])
                print('artist: ' + track['artist'])
                print('album: ' + track['album'])
                print('song: ' + track['title'])
                print('uri: ' + track['uri'])
            except Exception as e:
                print(e)
            print('---------------------------------------------------------------')
            #res = input("Do you want to add that track to the queue(y or n)? ")
            #if res.lower().startswith('y'):
            playlist.append((track['id'], track['uri']))
            print(track['title'], "added to playlist")
        else:    
            print("track count =",count)
            for n,track in enumerate(tracks,1):
                try:
                    print('\n')
                    print(n)
                    print('id: ' + track['id'])
                    print('artist: ' + track['artist'])
                    print('album: ' + track['album'])
                    print('song: ' + track['title'])
                    print('uri: ' + track['uri'])
                except Exception as e:
                    print(e)
                print('---------------------------------------------------------------')
            res = input("Which track to you want (0=None)? ")
            num = int(res)
            if num:
                 track = tracks[num-1]
                 playlist.append((track['id'], track['uri']))
                 print(track['title'], "added to queue")

except KeyboardInterrupt:
    pass

uris = [x[1] for x in playlist]
sqs_response = queue.send_message(MessageBody=json.dumps({'action':action, 'uris':uris}))
print("Status Code =", sqs_response['ResponseMetadata']['HTTPStatusCode'])
if action == 'add':
    sqs_response = queue.send_message(MessageBody=json.dumps({'action':'resume'}))
    print("Status Code =", sqs_response['ResponseMetadata']['HTTPStatusCode'])
print('\n')

ids = ['"{}"'.format(x[0]) for x in playlist] #" are necessary because of non-a-z characters like "("
s = 'id:' + ' id:'.join(ids)
print("query string = ",s)
print('\n')
result = solr.query(collection, {'q':s, 'rows':25, 'fl':['title', 'artist', 'album']}) 
tracks = result.docs
count = result.get_results_count()
print("The queue has {} tracks as follows:\n".format(count))
for n,track in enumerate(tracks,1):
    try:
        print('\n')
        print(n)
        print('artist: ' + track['artist'])
        print('album: ' + track['album'])
        print('song: ' + track['title'])
    except Exception as e:
        print(e)
    
print('\n')
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
playlist = json.dumps(playlist.extend(existing_queue))
response = s3.put_object(Bucket='sonos-playlists', Key=playlist_name, Body=playlist)
print("response to s3 put =",response)
