'''
This script loads solr sonos_companion from data that had been in solr but needs to be moved or reindexed
Most recently was used to move sonos db from solr on ec2 to solr on raspi
'''

from SolrClient import SolrClient
import sys
import json
import requests
from config import ec_uri # if this is run again probably not ec_uri (from uri)
uri = 'http://192.168.1.122' #if run again this may also need to be changed (to uri)

solr_old = SolrClient(ec_uri+':8983/solr')
solr_new = SolrClient(uri+':8983/solr')
collection = 'sonos_companion'
start = 0
temp = [1]
while len(temp) > 0:
    result = solr_old.query(collection, {'q':'*', 'rows':1000, 'start':start}) 
    temp = result.data['response']['docs']
    #print(repr(temp).encode('cp1252', errors='replace'))
    start+=1000

    documents = []
    for item in temp:
        document = {'id':item['id'].lower()}
        # apparently ran the first time to transfer to raspi without track in the list
        # the reason so few tracks actually have a track number (I did a few starting 08072016)
        document.update({k:item[k] for k in item if k in ('album','artist','title','uri','track')})
        documents.append(document)
    #print(documents)

    n = 0
    while True:
        # there are limitations in how many docs can be uploaded in a batch but it's more than 100
        cur_documents = documents[n:n+100]

        if not cur_documents:
            break

        cur_documents = json.dumps(cur_documents) 
        response = solr_new.index_json(collection, cur_documents) 
        print(response)

        # Since solr.commit didn't seem to work, substituted the below, which works
        url = uri+":8983/solr/"+collection+"/update"
        r = requests.post(url, data={"commit":"true"})
        print(r.text)

        n+=100
