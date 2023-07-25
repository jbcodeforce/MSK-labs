import boto3

msk = boto3.client('kafka')

# get all message from kafka topic


def lambda_handler(event,context):
    for record in event['Records']:
        print(record['body'])
        
