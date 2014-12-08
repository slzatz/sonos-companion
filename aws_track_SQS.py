'''
Program intended to be run from AWS EC2 to track songs played no matter from where
This works but you pay for SMS after 100 so I think I'll just use twitter direct messaging
Putting songs in SQS is a way to track them but probably best just to put in a database

'''
import sys
from time import sleep
import boto.sqs
import boto.sns
from boto.sqs.message import Message
import config as c
conn = boto.sqs.connect_to_region(
    "us-east-1",
    aws_access_key_id=c.aws_access_key_id,
    aws_secret_access_key=c.aws_secret_access_key)

q = conn.get_all_queues()[0]

sns_conn = boto.sns.connect_to_region(
    "us-east-1",
    aws_access_key_id=c.aws_access_key_id,
    aws_secret_access_key=c.aws_secret_access_key)

#topics = sns_conn.get_all_topics()
#print topics
#z = sns_conn.create_topic('sonos')
#print "z=",z
topics = sns_conn.get_all_topics()
print topics
mytopics = topics["ListTopicsResponse"]["ListTopicsResult"]["Topics"]
print "mytopics=", mytopics

mytopic_arn = mytopics[0]["TopicArn"]
print "mytopic_arn=", mytopic_arn
subscriptions = sns_conn.get_all_subscriptions_by_topic(mytopic_arn)
print "subscriptions=",subscriptions
msg = "." #can't be empty but doesn't show up in SMS
subj = "SNS message over boto - this is a longer message - let's see and here is an even longer message"
res = sns_conn.publish(mytopic_arn, msg, subj)
print "res=",res
sys.exit()
while 1:
    m = q.get_messages()
    if m:
        m = m[0]
        body = m.get_body()
        print body
        q.delete_message(m)
    sleep(30)
