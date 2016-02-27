'''
THIS IS CURRENTLY THE SCRIPT TO USE TO MOVE TRACKS IN THE QUEUE INTO SOLR
This works without having to play the tracks
Note that if the solr document already exists, the add operation will replace it. 

The upload format for SolrClient (python3 solr client program) is jsonifying a list of dictionaries:
[{'id':'After_The_Gold_Rush_Birds', 'artist':'Neil Young', 'title':'Birds', 'album':'After the Gold Rush',
'uri':'x-sonos-http:amz%3atr%3a44ce93d2-4105-416a-a905-51fe0f38ed9a.mp4?sid=26&flags=8224&sn=2'...}{...
'''

from SolrClient import SolrClient
import sys
import json
import requests
from config import ec_uri
import os
from time import sleep
import datetime
home = os.path.split(os.getcwd())[0]
sys.path = [os.path.join(home, 'SoCo')] + sys.path
import soco
from soco import config

config.CACHE_ENABLED = False

n = 0
while 1:
    n+=1
    print("attempt "+str(n))
    try:
        sp = soco.discover(timeout=2)
        speakers = {s.player_name:s for s in sp}
    except TypeError as e:    
        print(e)
        sleep(1)       
    else:
        break 
    
for sn in speakers:
        print("{} -- coordinator:{}".format(sn, speakers[sn].group.coordinator.player_name))

master_name = input("Which speaker do you want to be master? ")
master = speakers.get(master_name)
if master:
    print("Master speaker is: {}".format(master.player_name))
else:
    print("Somehow you didn't pick a master or spell it correctly (case matters")
    sys.exit(1)

print('\n')

#Note appears possible to pick up title, album and artist
#album = input("What is the album? ")
#artist = input("Who is the artist? ")
queue = master.get_queue()
if len(queue) == 0:
    raise Exception("You must have at least one track in the queue")

documents = []
n=1
for track in queue:
    title = track.title
    album = track.album
    artist = track.creator
    id_ = album + ' ' + title
    id_ = id_.replace(' ', '_')
    document = {"id":id_, "title":title, "uri":track.resources[0].uri, "album":album, "artist":artist, "track":n}
    print(document)
    documents.append(document)
    n+=1

solr = SolrClient(ec_uri+':8983/solr')
collection = 'sonos_companion'

#cur_documents = json.dumps(documents) 
#response = solr.index_json(collection, cur_documents) 
response = solr.index_json(collection, json.dumps(documents))
print(response)

# Since solr.commit didn't seem to work, substituted the below, which works
url = ec_uri+":8983/solr/"+collection+"/update"
r = requests.post(url, data={"commit":"true"})
print(r.text)

######################################################################
# The below would be if you had a lot of documents
#n = 0
#while True:
#    # there are limitations in how many docs can be uploaded in a batch but it's more than 100
#    cur_documents = documents[n:n+100]
#
#    if not cur_documents:
#        break
#
#    cur_documents = json.dumps(cur_documents) 
#    response = solr.index_json(collection, cur_documents) 
#    print(response)
#    #The commit from SolrClient is not working
#    #response = solr.commit(collection, waitSearcher=False)
#    #print(response)
#
#    # Since solr.commit didn't seem to work, substituted the below, which works
#    url = ec_uri+":8983/solr/"+collection+"/update"
#    r = requests.post(url, data={"commit":"true"})
#    print(r.text)
#
#    n+=100
