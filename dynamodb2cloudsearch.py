'''
This script allows you to move data from dynamodb to cloudsearch
It uses boto for cloudsearch and boto3 for dynamodb
I do think the future may be bypassing dynamo completely and just going
from sonos to cloudsearch
Note that I had to change the permissions to be completely open to allow all access when this script runs
and then change the permissions to be more restrictive
If not you get some cryptic error about adds
When it fails to commit, not clear to me if some documents do get committed
Not 100% sure what it does when there is an existing document but I don't see dups
in the database right now
'''

from boto.cloudsearch2.layer2 import Layer2
from boto.cloudsearch2.domain import Domain
import boto.cloudsearch2
import boto3
import sys
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

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('amazon_music')

results = table.scan()
items = results['Items']
n = 0
while True:
    cur_items = items[n:n+100]

    if not cur_items:
        break

    doc_service = domain.get_document_service()

    for item in cur_items:
        docid = item['album'] + ' ' + item['title']
        docid = docid.replace(' ', '_')
        doc_service.add(docid, item)

    try:    
        resp=doc_service.commit()
        print(resp)
    except Exception as e:
        print(e)

    n+=100
