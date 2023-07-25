import boto3
import os, json, calendar
from datetime import datetime

STREAM_NAME = os.environ['STREAM_NAME']
REGION = os.environ['AWS_REGION']

# connect to kinesis data streams
kinesis = boto3.client('kinesis', region_name=REGION)

def lambda_handler(event,context):
    # put records in kinesis data stream
    payload = {
        "carRide": json.dumps(event),
        "timestamp": str(calendar.timegm(datetime.utcnow().timetuple()))
        }
    kinesis.put_record(
        StreamName=STREAM_NAME,
        Data=json.dumps(payload),
        PartitionKey=event["orderID"])
    return {"statusCode":200, "body":"Successfully posted"}