import boto.sqs
from boto.sqs.message import Message
conn = boto.sqs.connect_to_region(
    "us-east-1",
    aws_access_key_id='AKIAJZZMUDM7GMBJE2KQ',
    aws_secret_access_key='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')

