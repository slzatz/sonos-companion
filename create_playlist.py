'''
Create a playlist manually by entering songs one at a time
and searching solr for the particular song
Advantage of this script is that it can add to an existing playlist
There is also create_playlist_from_queue.py where you put the songs on the queue
and there is a add2queue.py where you can decide after selecting songs whether
you want to create a playlist
'''
from SolrClient import SolrClient
from config import ec_uri
import boto3
import botocore
import json

solr = SolrClient(ec_uri+':8983/solr')
collection = 'sonos_companion'

playlist_name = input("What do you want to call the playlist that will be uploaded to s3 [Note: will be changed to lower case]? ")
playlist_name = playlist_name.lower()
playlist=[]

s3 = boto3.resource('s3')
object = s3.Object('sonos-playlists', playlist_name)
try:
    z = object.get()['Body'].read()
except botocore.exceptions.ClientError as e:
    if e.response['Error']['Code'] == "NoSuchKey":
        exists = False
    else:
        raise e
else:
    exists = True
    
if not exists:
    print("Playlist '{}' does not exist".format(playlist_name))
else:
    res = input("Playlist '{}' exists - do you want to replace or add to it?(r or a) ".format(playlist_name))
        
    if res.startswith('a'):
        playlist = json.loads(z.decode('utf-8'))
        ids = ['"{}"'.format(x[0]) for x in playlist] #" are necessary I suspect because of non-a-z characters like (
        s = 'id:' + ' id:'.join(ids)
        print("query string = ",s)
        print('\n')
        result = solr.query(collection, {'q':s, 'rows':25, 'fl':['title', 'artist', 'album']}) 
        tracks = result.docs
        count = result.get_results_count()
        print("The playlist has {} tracks as follows:\n".format(count))
        for n,track in enumerate(tracks,1):
            try:
                print(n)
                print('artist: ' + track['artist'])
                print('album: ' + track['album'])
                print('song: ' + track['title'])
            except Exception as e:
                print(e)

try:
    while 1:
        track_title = input("\nwhat is the title of the track that you want to add to the playlist (Ctrl-C if done)? ")
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
            print('------------------------------------------------------------------------')
            res = input("Do you want to add that to the playlist (y or n)? ")
            if res.lower().startswith('y'):
                 playlist.append((track['id'], track['uri']))
                 print(track['title'], "added to playlist")
        else:    
            print("track count =",count)
            #tracks = result.data['response']['docs']
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
                print('------------------------------------------------------------------------')
            res = input("Which track to you want (0=None)? ")
            num = int(res)
            if num:
                 track = tracks[num-1]
                 playlist.append((track['id'], track['uri']))
                 print(track['title'], "added to playlist")

except KeyboardInterrupt:
    pass

print('\n')
print(playlist)
print('\n')

ids = ['"{}"'.format(x[0]) for x in playlist] #"(quotations) are necessary for solr presumably because of non-a-z characters like "("
s = 'id:' + ' id:'.join(ids)
print("query string = ",s)
print('\n')
result = solr.query(collection, {'q':s, 'rows':25, 'fl':['title', 'artist', 'album']}) 
tracks = result.docs
count = result.get_results_count()
print("The playlist has {} tracks as follows:\n".format(count))
for n,track in enumerate(tracks,1):
    try:
        print('\n')
        print(n)
        print('artist: ' + track['artist'])
        print('album: ' + track['album'])
        print('song: ' + track['title'])
    except Exception as e:
        print(e)

res = input("Do you want to upload playlist {} to s3 (y or n) ? ".format(playlist_name))
if res.lower().startswith('y'):
    s3 = boto3.client('s3')
    response = s3.put_object(Bucket='sonos-playlists', Key=playlist_name, Body=json.dumps(playlist))
    print("response to s3 put =",response)

res = input("Do you want to play playlist {} now (y or n)? ".format(playlist_name))
if res.lower().startswith('y'):

    s3 = boto3.resource('s3')
    obj = s3.Object('sonos-scrobble','location')
    location = obj.get()['Body'].read().decode('utf-8')
    queue_name = 'echo_sonos_ct' if location=='ct' else 'echo_sonos'
    print("location = ", location)
    print("queue_name =", queue_name)
    sqs = boto3.resource('sqs', region_name='us-east-1')
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    uris = [x[1] for x in playlist] #" are necessary I suspect because of non-a-z characters like (
    sqs_response = queue.send_message(MessageBody=json.dumps({'action':'play', 'uris':uris}))
    print("Status Code =", sqs_response['ResponseMetadata']['HTTPStatusCode'])
