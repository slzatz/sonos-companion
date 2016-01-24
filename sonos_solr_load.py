'''
This script reloaded solr sonos_companion from data that had been in solr but needed to be reindexed
Problem is that the files used will already be out of date as songs will be added
The data was removed from solr using the following at the command line
from SolrClient import SolrClient
import json
from config import ec_uri 
solr = SolrClient(ec_uri+':8983/solr')
from config import ec_uri 
collection = 'sonos_companion'
>>> result1000 = solr.query(collection, {'q':'*', 'rows':1000, 'start':0}) 
>>> result999 = solr.query(collection, {'q':'*', 'rows':1000, 'start':999}) 
>>> result1998 = solr.query(collection, {'q':'*', 'rows':1000, 'start':1998}) 
...
>>> with open('last_854', 'w') as f:
>>>     f.write(json.dumps(result1998.data['response']['docs'])) 
The files are named first_1000, next_1000, last_854
'''

from SolrClient import SolrClient
import sys
import json
import requests
from config import ec_uri 

solr = SolrClient(ec_uri+':8983/solr')
collection = 'sonos_companion'

file_name = input("What file do you want to use for uploading data to solr sonos-companion?")

with open(file_name,'r') as f:
    z = f.read()

items = json.loads(z)
documents = []
for item in items:
    document = {}
    document.update({k:item[k] for k in item if k in ('id','album')})
    document.update({k:item[k][0] for k in item if k in ('artist','title','uri','album_art')})
    documents.append(document)
#print(documents)
#sys.exit()

n = 0
while True:
    # there are limitations in how many docs can be uploaded in a batch but it's more than 100
    cur_documents = documents[n:n+100]

    if not cur_documents:
        break

    cur_documents = json.dumps(cur_documents) 
    response = solr.index_json(collection, cur_documents) 
    print(response)

    #The commit from SolrClient is not working
    #response = solr.commit(collection, waitSearcher=False)
    #print(response)

    # Since solr.commit didn't seem to work, substituted the below, which works
    url = ec_uri+":8983/solr/"+collection+"/update"
    r = requests.post(url, data={"commit":"true"})
    print(r.text)

    n+=100
