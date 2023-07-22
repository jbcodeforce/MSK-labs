import boto3
import os

STREAM_NAME = os.environ['STREAM_NAME']
REGION = os.environ['REGION']

# connect to kinesis data streams
kinesis = boto3.client('kinesis')

def lambda_handler(event,context):
    # put records in kinesis data stream
    kinesis.put_record(
        StreamName=STREAM_NAME,
        Data='This is a test',
        PartitionKey='partitionkey')
    return(event,context)