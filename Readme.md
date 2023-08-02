# MSK studies and labs

The goal of this repository is to share some code and practices around MSK.

The goal of this first proof of technology is to get messages from Amazon Kinesis Data Stream to Amazon Managed Service for Kafka using Kafka Connector Apache Camel source connector.

![](./docs/architecture.drawio.png)


## Infrastructure

Part of this solution is defined with Python CDK, and other part with Cloud Formation as MSK CDK is still in Alpha release and MSK connect is not supported in CDK yet (July 2023).

This `infrastucture` folder includes cdk stack and constructs to define the different elements of the labs:

* A VPC construct to define 2 private and 2 public subnets, with route tables, routes, NAT Gateway and Internet Gateway.
* A contruct for a EC2 Bastion host, with Kafka, Java and other important AWS cli tools
* A construct to define MSK cluster
* A Stack to include the solution components to stitch everything together.

* The VPC matches the following diagram:

![](./docs/hands-on-vpc.drawio.svg)

    * One internet gateway
    * Route tables are defined in each private subnet to outbound to NAT gateway
    * ACL to authorize inbound traffic
    * One NAT Gateway per public subnet with one ENI each.
    
* The bastion host uses a scripts to install Java, maven, docker, kafka, a library to authenticate to MSK, with specific aws Kafka client connection configuration. 
* The bastion host has a security group to authorize ssh on port 22 from a unique computer (the one running the cdk). It also use an Elastic Network Interface.
* IAM role to be assumed by MSK clients. The policy specifies action on Kafka cluster, topic and groups.
* The SolutionStack includes a function to define a Kinesis data streams and a simple Lambda function to post message to the KDS streams.


### Deployment

1. Create a Kafka cluster configuration from the properties file: `MSKconstruct/kafka-config.properties` with the following script:

```sh
# In  MSKconstruct folder
./addConfiguration.sh
```

1. Use CDK to deploy the solution stack and all needed constructs:

```sh
export APP_NAME=acr
cdk deploy
# it will take some minutes to create

```

1. Verify cluster state

```sh
aws kafka list-clusters
```


## Code explanation

### Kinesis Data Streams Producer App

The producer is a simple Lambda python function that is using boto3 Kinesis client to put record in a streams. The streams is defined in the CDK KDSstack, and passes the stream name as environment variable for the Lambda. See Lambda code in [src/kinesis-producer/KinesisProducer.py](https://github.com/jbcodeforce/MSK-labs/blob/main/src/kinesis-producer/KinesisProducer.py) and [CDK Solution stack](https://github.com/jbcodeforce/MSK-labs/blob/main/infrastructure/SolutionStack/main_stack.py).

```python
def defineKDSresources(stack, config):

    stream = kinesis.Stream(stack, 
        config.get("kds_name"),
        stream_name=config.get("kds_stream_name")
    )

    # producer lambda
    kds_producer_lambda = _lambda.Function(stack, config.get("producer_lambda_name"),
                                        runtime=_lambda.Runtime.PYTHON_3_10,
                                        code=_lambda.Code.from_asset("../src/kinesis-producer"),
                                        handler="KinesisProducer.lambda_handler",
                                        environment={
                                            "STREAM_NAME": stream.stream_name
                                        }
                                        )    
    stream.grant_write(kds_producer_lambda)
    return (stream,kds_producer_lambda)
```

### MSK and a Lambda topic consumer

A first basic implementation is to use a Lambda consumer and add MSK as an event source. The [cdk msk-clients](https://github.com/jbcodeforce/MSK-labs/blob/main/infrastructure/MSKstack/msk_stack.py) declares MSK cluster, and the lambda function.

We need to declare an IAM role that allows the connector to write to the destination topic. 

For the MSK cluster, the brokers are deployed in private subnet but with security group authorizing access from any hosts. 

### Apache Camel Kinesis data streams source connector

The Camel version 3.18.2 includes pre-packaged connector in [this documentation](https://camel.apache.org/camel-kafka-connector/next/reference/index.html) that we can download to a working folder.  Untar and then zip it to upload to S3

```sh
aws s3 cp ~/Code/tmp/camel-aws-kinesis-source-kafka-connector.zip s3://msk-lab-${ACCOUNT_ID}-plugins-bucket/
```

* Ensure MSK cluster is running. Then create a custom MSK Connect configuration using the plugin zip from S3 bucket:

![](./docs/msk-c-ui-1.png)

* Add the connector configuration from the [MSKConnect/CamelAwskinesissourceSourceConnector](https://github.com/jbcodeforce/MSK-labs/tree/main/infrastructure/MSKConnect/CamelAwskinesissourceSourceConnector.properties)
* Use auto scaling when we do not know the workload pattern, for demo use provisioned with 1 worker.
* Create a custom IAM role to read from Kinesis Data Streams with trusted entity being KafkaConnect

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "sts:AssumeRole"
            ],
            "Effect": "Allow",
            "Principal": {
                "Service": [
                    "kafkaconnect.amazonaws.com"
                ]
            }
        }
    ]
}
```

TBC..

MSK [Kafka connect documentation](https://docs.aws.amazon.com/msk/latest/developerguide/msk-connect.html).

## More information

* [AWS MSK workshop - MSK Connect lab](https://catalog.workshops.aws/msk-labs/en-US/mskconnect/overview)
* [Kafka Connect summary note](https://jbcodeforce.github.io/eda-studies/techno/kafka-connect/)
* [Apache Camel 3.18 connector list](https://camel.apache.org/camel-kafka-connector/next/reference/index.html).
* [Debezium Postgres connector](https://repo1.maven.org/maven2/io/debezium/debezium-connector-postgres)