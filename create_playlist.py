'''
Create a playlist manually by entering songs one at a time
and searching solr for the particular song
There is also create_playlist_from_queue.py that has you put the songs on the queue
(from a playlist or whatever) and creates a playlist from the queue by playing the queue
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
        result = solr.query(collection, {'q':s, 'rows':25, 'fields':['title', 'artist', 'album']}) 
        tracks = result.docs
        count = result.get_results_count()
        print("The playlist has {} tracks as follows:\n".format(count))
        for n,track in enumerate(tracks,1):
            try:
                print(n)
                #print('id: ' + track['id'])
                print('artist: ' + track['artist'])
                print('album: ' + track['album'])
                print('song: ' + track['title'])
                #print('uri: ' + track['uri'])
            except Exception as e:
                print(e)

try:
    while 1:
        track_title = input("\nwhat is the title of the track that you want to add to the playlist (Ctrl-C if done)? ")
        s = 'title:' + ' AND title:'.join(track_title.split())
        result = solr.query(collection, {'q':s, 'rows':10, 'fields':['score', 'title', 'artist', 'album'], 'sort':'score desc'}) 
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
                print('---------------------------------------------------------------')
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

ids = ['"{}"'.format(x[0]) for x in playlist] #" are necessary I suspect because of non-a-z characters like (
s = 'id:' + ' id:'.join(ids)
print("query string = ",s)
print('\n')
result = solr.query(collection, {'q':s, 'rows':25, 'fields':['title', 'artist', 'album']}) 
tracks = result.docs
count = result.get_results_count()
print("The playlist has {} tracks as follows:\n".format(count))
for n,track in enumerate(tracks,1):
    try:
        print('\n')
        print(n)
        #print('id: ' + track['id'])
        print('artist: ' + track['artist'])
        print('album: ' + track['album'])
        print('song: ' + track['title'])
        #print('uri: ' + track['uri'])
    except Exception as e:
        print(e)

res = input("Do you want to upload playlist {} to s3 (y or n) ? ".format(playlist_name))
if res.lower().startswith('y'):
    s3 = boto3.client('s3')
    #playlist = str(json.dumps(playlist))
    playlist = json.dumps(playlist)
    response = s3.put_object(Bucket='sonos-playlists', Key=playlist_name, Body=playlist)
    print("response to s3 put =",response)
