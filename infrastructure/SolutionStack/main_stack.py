from aws_cdk import (
    CfnOutput,
    Stack,
    aws_ec2 as ec2,
    aws_kinesis as kinesis,
    aws_lambda as _lambda,
    aws_iam as iam
)

from constructs import Construct
from helpers.BaseStack import BaseStack
from VPCconstruct.vpc_construct import VPCbase
from MSKconstruct.msk_contruct import MSKCluster
from Bastion.bastion_contruct import BastionHost
from .msk_clients import MSKClients

'''
Define the components for the demo:
- Kinesis Data Stream
- MSK cluster in the given VPC
- Bastion Host with bootstrap info
'''
class SolutionStack(BaseStack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        base_name = self.config.get("app_name")
        app_vpc = VPCbase(self,f"{base_name}-vpc", self.config)
        stream, kds_producer_lambda = defineKDSresources(self,self.config)
        msk = MSKCluster(self, f"{base_name}-msk", kafka_vpc=app_vpc.vpc, config=self.config)
        bastion_host = BastionHost(
            self,
            self.config.get("bastion_host_name"),
            theVpc=app_vpc.vpc,
            roleToAssume= msk.client_iam_role
        )
 
        allow_bastion_host_to_access_kafka(
            msk.security_group, 
            bastion_host.security_group
        )
        mskClient= MSKClients(self, f"{base_name}-clients", msk_cluster=msk.kafka_cluster, config=self.config)

'''
The source is a Kinesis Data Stream, so this is the declaration with a lambda
to send some messages to it
'''
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


def allow_bastion_host_to_access_kafka( 
            kafka_sg: ec2.ISecurityGroup, 
            bastion_host_sg: ec2.ISecurityGroup):
    kafka_sg.connections.allow_from(other=bastion_host_sg.connections, 
                                    port_range=ec2.Port.tcp(9098))
    # add more mapping if needed
    return None

