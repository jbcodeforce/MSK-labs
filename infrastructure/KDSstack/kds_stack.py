# import cdk
from aws_cdk import (
    CfnOutput,
    aws_ec2 as ec2,
    aws_kinesis as kinesis,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_logs as logs,
    )

from constructs import Construct
from helpers.BaseStack import BaseStack

class KDSstack(BaseStack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.stream = kinesis.Stream(self, "CarRideStream",
            stream_name="acr-carrides"
        )

        # producer lambda
        producer_lambda = _lambda.Function(self, "CarRideProducerLambda",
                                           runtime=_lambda.Runtime.PYTHON_3_9,
                                           code=_lambda.Code.from_asset("../src/kinesis-producer"),
                                           handler="KinesisProducer.lambda_handler",
                                           environment={
                                               "STREAM_NAME": self.stream.stream_name
                                           }
                                           )    
        self.stream.grant_write(producer_lambda)


