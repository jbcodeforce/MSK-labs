# MSK studies and labs

The goal of this repository is to share some code and practices around MSK.

## Infrastructure

This `infrastucture` folder includes cdk stacks to define the different elements of the labs.

## Lab 1

The goal of this first proof of technology is to get messages from Amazon Kinesis Data Stream to Amazon Managed Service for Kafka using Kafka Connector Apache Camel source connector.

![](./docs/architecture.drawio.png)

Part of this solution is defined with Python CDK, and other part with Cloud Formation as MSK CDK is still in Alpha release.

* The VPC to keep to isolate the elements and define a EC2 Bastion machine.
* The Producer and Kinesis Data Streams is defined in its own CDK stack:  KDSstack, to create a data streams and a simple Lambda function to post message to the streams.


Jumpstart the infrastructure with cdk on the following stacks:

```sh
export APP_NAME=acr
cdk deploy acr-vpc
cdk deploy acr-kds
```

### Complete the MSK deployment

* Create a cluster configuration from the properties file: `MSKstack/kafka-config.properties` with the following script:

```sh
#In  MSKstack
./addConfiguration.sh
```

* Launch the MSK cluster creation using CDK:

```sh
cdk deploy acr-msk
# it will take some minutes to create
aws kafka list-clusters
```

### Kinesis Data Streams Producer App

The producer is a simple Lambda python function that is using boto3 Kinesis client to put record in a streams. The streams is defined in the CDK KDSstack, and passes the stream name as environment variable for the Lambda. See Lambda code in [src/kinesis-producer/KinesisProducer.py](https://github.com/jbcodeforce/MSK-labs/blob/main/src/kinesis-producer/KinesisProducer.py) and [CDK KDSstack](https://github.com/jbcodeforce/MSK-labs/blob/main/infrastructure/KDSstack/kds_stack.py).

### MSK and a Lambda topic consumer

A first basic implementation is to use a Lambda consumer and add MSK as an event source. The [CDK MSKstack](https://github.com/jbcodeforce/MSK-labs/blob/main/infrastructure/MSKstack/msk_stack.py) declares MSK cluster, and the lambda function.

We need to declara an IAM role that allows the connector to write to the destination topic. 

For the MSK cluster, the brokers are deployed in private subnet but with security group authorizing access from any hosts.

### Apache Camel Kinesis data streams source connector

The Camel version 3.18.2 includes pre-packaged connector in [this documentation](https://camel.apache.org/camel-kafka-connector/next/reference/index.html) that we can download to a working folder.  Untar and then zip it to upload to S3

```sh
aws s3 cp ~/Code/tmp/camel-aws-kinesis-source-kafka-connector.zip s3://msk-lab-${ACCOUNT_ID}-plugins-bucket/
```

TBC..

MSK [Kafka connect documentation](https://docs.aws.amazon.com/msk/latest/developerguide/msk-connect.html).

## More information

* [AWS MSK workshop - MSK Connect lab](https://catalog.workshops.aws/msk-labs/en-US/mskconnect/overview)
* [Apache Camel 3.18 connector list](https://camel.apache.org/camel-kafka-connector/next/reference/index.html).
* [Debezium Postgres connector](https://repo1.maven.org/maven2/io/debezium/debezium-connector-postgres)