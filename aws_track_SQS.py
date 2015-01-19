'''
Program intended to be run from AWS EC2 to track songs played no matter from where
Because you pay for SMS after 100 using SNS I decided to just use twitter direct messaging instead
However, tft_sonos.py is still putting songs in SQS and the code below retrieves them

'''
import sys
from time import sleep
import boto.sqs
import config as c
conn = boto.sqs.connect_to_region(
    "us-east-1",
    aws_access_key_id=c.aws_access_key_id,
    aws_secret_access_key=c.aws_secret_access_key)

q = conn.get_all_queues()[0]
print "Queues =",q
count = q.count()
print "Queue count =",count

#q.dump('messages.txt', sep='\n------------------\n') #utility to print all messages
n = 0
zz = []

while 1:
    messages = q.get_messages(10, 30, attributes=['SentTimestamp'], message_attributes=['All']) #'artist','song','album']) #'All') #second parameter is the time message will be invisible
    if not messages:
        break
    for m in messages:
        #body=m.get_body()
        #print body
        #attributes = m.attributes
        #print "attributes=",attributes
        ma = m.message_attributes
        if ma:
            text = "artist: {}; song: {}; album: {}".format(ma['artist']['string_value'], ma['song']['string_value'], ma['album']['string_value'])
            zz.append((int(m.attributes['SentTimestamp']), text))
        else:
            q.delete_message(m)
            
        n+=1

print "Printed {} messages".format(n)
zz.sort()
zz.reverse()
for z in zz:
    print z[0],z[1]
