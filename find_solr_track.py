'''
Create a playlist manually by entering songs one at a time
and searching solr for the particular song
There is also create_playlist_from_queue.py that has you put the songs on the queue
(from a playlist or whatever) and creates a playlist from the queue 
'''
from SolrClient import SolrClient
from config import ec_uri

solr = SolrClient(ec_uri+':8983/solr')
collection = 'sonos_companion'

track_title = input("\nwhat is the title of the track that you are looking for? ")
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
    print('------------------------------------------------------------------------------------------------')
else:    
    print("track count =",count)
    for n,track in enumerate(tracks,1):
        try:
            #print('\n')
            print(n)
            print('id: ' + track['id'])
            print('artist: ' + track['artist'])
            print('album: ' + track['album'])
            print('song: ' + track['title'])
            print('uri: ' + track['uri'])
        except Exception as e:
            print(e)
        print('--------------------------------------------------------------------------------------------------')
    #res = input("Which track to you want (0=None)? ")
    #num = int(res)
    #if num:
    #    print(num)
