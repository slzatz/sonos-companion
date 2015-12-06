'''
REMEMBER TO CHANGE THE PERMISSIONS
This script allows you to move data from a file to cloudsearch
Not 100% sure what it does when there is an existing document but I don't see dups
trackinfo.py was used to get tracks out of rhapsody
It would be possible to add that code here so it went straight from sonos to cloudsearch
There are more items then we need to upload to cloudsearch so we do process the file information to remove unnecessary fields:

    item = {k:item[k] for k in item if k in ('artist','album','title','uri', 'album_art')}

Boto3 document format below
[
 {"type": "add",
  "id":   "tt0484562",
  "fields": {
    "title": "The Seeker: The Dark Is Rising",
    "directors": "Cunningham, David L.",
    "genres": ["Adventure","Drama","Fantasy","Thriller"],
    "actors": ["McShane, Ian","Eccleston, Christopher","Conroy, Frances",
              "Crewson, Wendy","Ludwig, Alexander","Cosmo, James",
              "Warner, Amelia","Hickey, John Benjamin","Piddock, Jim",
              "Lockhart, Emma"]
  }
 },
 {"type": "delete",
  "id":   "tt0484575"
 }
]
'''

from boto.cloudsearch2.layer2 import Layer2
from boto.cloudsearch2.domain import Domain
import boto.cloudsearch2
#import boto3
#cloudsearchdomain = boto3.client('cloudsearchdomain', endpoint_url=c.aws_cs_url, region_name='us-east-1')
#response = cloudsearchdomain.upload_documents( documents=b'bytes', contentType='application/json') # docs are json
import sys
import json
import config as c
conn = boto.cloudsearch2.connect_to_region("us-east-1",
             aws_access_key_id=c.aws_access_key_id,
             aws_secret_access_key=c.aws_secret_access_key)

domain_data =  conn.describe_domains('sonos-companion')

domain_data = (domain_data['DescribeDomainsResponse']
                          ['DescribeDomainsResult']
                          ['DomainStatusList'])

domain = Domain(conn, domain_data[0])
print(domain)
print("\nNOTE: you need to open up the permissions by going to the Web dashboard of CloudSearch.\n")
file_name = input("What file do you want to use for uploading data to CloudSearch ?")

with open(file_name,'r') as f:
    z = f.read()

full_items = json.loads(z)
items = []
for item in full_items:
    item = {k:item[k] for k in item if k in ('artist','album','title','uri', 'album_art')}
    items.append(item)

#documents = json.dumps(items) #boto3

n = 0
while True:
    # there are limitations in how many docs can be uploaded in a batch but it's more than 100
    cur_items = items[n:n+100]

    if not cur_items:
        break

    doc_service = domain.get_document_service()

    for item in cur_items:
        print(item)
        docid = item['album'] + ' ' + item['title']
        docid = docid.replace(' ', '_')
        doc_service.add(docid, item)

    try:    
        resp=doc_service.commit()
        print(resp) #<boto.cloudsearch2.document.CommitResponse object at 0x027EF1D0>
    except Exception as e:
        print("Exception trying to write CloudSearch: ", e) #The cryptic exception will be 'adds' if permissions issue

    n+=100
