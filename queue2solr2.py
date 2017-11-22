'''
02-27-2016
THIS IS CURRENTLY THE SCRIPT TO USE TO MOVE TRACKS IN THE QUEUE INTO SOLR
The solr database is determined by the solr_uri in config.py - right now ec2
This works without having to play the tracks
The script asks whether this is an album to know whether to assign track numbers
from the queue positions or just default to track 1
Note that if the solr document already exists, the add operation will replace it. 
However, if you change the id at all by changing the album name or title it won't delete
the older versions.
The upload format for SolrClient (python3 solr client program) is jsonifying a list of dictionaries:
[{'id':'After_The_Gold_Rush_Birds', 'artist':'Neil Young', 'title':'Birds', 'album':'After the Gold Rush',
'uri':'x-sonos-http:amz%3atr%3a44ce93d2-4105-416a-a905-51fe0f38ed9a.mp4?sid=26&flags=8224&sn=2'...}{...
'''

from SolrClient import SolrClient
import sys
import json
import requests
from config import solr_uri
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
        sp = soco.discover(timeout=1)
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

def user_input(info):
    user_response = input("What do you want the {} to be? ".format(info))
    print("{} =".format(info), user_response)
    input("Is that correct (y or n)? ")
    if resp not in ('y', 'yes'):
        user_input(info)
    else:
        return user_response

cont = True
while cont:
    queue = master.get_queue()
    if len(queue) == 0:
        raise Exception("You must have at least one track in the queue")

    album = user_input("album title")
    artist = user_input("artist name")

    documents = []
    n=1
    for track in queue:
        title = track.title
        uri = track.uri
        id_ = album + ' ' + title
        id_ = id_.replace(' ', '_')
        id_ = id_.lower()
        document = {"id":id_, "title":title, "uri":uri, "album":album, "artist":artist, "track":n}
        print(repr(document).encode('cp1252', errors='replace')) 
        for k in document:
            print(str(k+':'+str(document[k])).encode('cp1252', errors='ignore'))
        documents.append(document)
        n+=1

    solr = SolrClient(solr_uri+'/solr')
    collection = 'sonos_companion'

    response = solr.index_json(collection, json.dumps(documents))
    print(response)

    # Since solr.commit didn't seem to work, substituted the below, which works
    url = solr_uri+"/solr/"+collection+"/update"
    r = requests.post(url, data={"commit":"true"})
    print(r.text)

    resp = input("Do you want to continue? (y or n) ")
    if resp not in ('y', 'yes'):
        cont = False

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
#    url = solr_uri+"/solr/"+collection+"/update"
#    r = requests.post(url, data={"commit":"true"})
#    print(r.text)
#
#    n+=100
