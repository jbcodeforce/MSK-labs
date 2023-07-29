import boto3
from aws_cdk import (
    CfnOutput,
    Stack,
    aws_ec2 as ec2,
    aws_msk_alpha as msk,
    aws_iam as iam,
    aws_lambda as lbda,
    aws_lambda_event_sources as les,
    aws_kinesis as kinesis,
    aws_lambda as _lambda,
    aws_logs as logs
    )

from constructs import Construct
from helpers.BaseStack import BaseStack

client = boto3.client('kafka')

# Get MSK configuration defined externally
def getMSKConfigurationCreated():
    rep=client.list_configurations(MaxResults=1)
    uniqueConfig = rep['Configurations'][0]
    if uniqueConfig['Name'] == "ClusterConfiguration1":
        return msk.ClusterConfigurationInfo(
                arn= uniqueConfig['Arn'],
                revision= uniqueConfig['LatestRevision']['Revision'])
    else:
        return None
    

'''
The source is a Kinesis Data Stream, so this is the declaration with a lambda
to send some messages to it
'''
def defineKDSresources(stack):
    stream = kinesis.Stream(stack, "CarRideStream",
        stream_name="acr-carrides"
    )

    # producer lambda
    kds_producer_lambda = _lambda.Function(stack, "CarRideProducerLambda",
                                        runtime=_lambda.Runtime.PYTHON_3_9,
                                        code=_lambda.Code.from_asset("../src/kinesis-producer"),
                                        handler="KinesisProducer.lambda_handler",
                                        environment={
                                            "STREAM_NAME": stream.stream_name
                                        }
                                        )    
    stream.grant_write(kds_producer_lambda)
    return (stream,kds_producer_lambda)


def defineMSKCluster(stack, vpc: ec2.Vpc):
        cwLogGroup = logs.LogGroup(stack,"/msk",retention=logs.RetentionDays.ONE_DAY)
        mskSecurityGroup = ec2.SecurityGroup(stack, "AcrMSKSecurityGroup",
                                security_group_name="AcrMSKSecurityGroup",
                                vpc=vpc,
                                allow_all_outbound=True
                            )
       
        # At that time configuration info is not very helpful, better use shell script.
        confInfo = getMSKConfigurationCreated()
        # See https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_msk_alpha.html
        msk_cluster = msk.Cluster(stack, "AcrCluster",
            cluster_name="AcrCluster",
            kafka_version=msk.KafkaVersion.V2_8_1,
            vpc=vpc,
            configuration_info = confInfo,
            instance_type=ec2.InstanceType("kafka.t3.small"),
            number_of_broker_nodes=1, # In each AZ !!!
            security_groups=[mskSecurityGroup],
            vpc_subnets=ec2.SubnetSelection( subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            ebs_storage_info= msk.EbsStorageInfo(volume_size=10),
            logging=msk.BrokerLogging(cloudwatch_log_group=cwLogGroup)                       
            client_authentication=msk.ClientAuthentication.sasl(
                #scram=True
                iam=True
            )

        )

        '''
        msk_cluster.connections.allow_from(
            ec2.Peer.ipv4(vpc.vpc_cidr_block),
            ec2.Port.tcp(2181))
        msk_cluster.connections.allow_from(
            ec2.Peer.ipv4(vpc.vpc_cidr_block),
            ec2.Port.tcp(9094))
        
        '''
           # MSK may need traffic from anywhere
        msk_cluster.connections.allow_from_any_ipv4(ec2.Port.all_traffic(), "allow all from anywhere")
        return msk_cluster

def outputResources(stack):
        CfnOutput(stack,"Lambda producer to KDS",value=stack.kds_producer_lambda.function_arn)

        #CfnOutput(stack,"Kafka Bootstrap SASL/SCRAM",value=stack.msk_cluster.bootstrap_brokers_sasl_scram)
        # CfnOutput(self,"Kafka Bootstrap",value=self.msk_cluster.bootstrap_brokers)
        # CfnOutput(stack,"Kafka Cluster ARN",value=stack.msk_cluster.cluster_arn)
        # CfnOutput(self, "BootstrapBrokers", value=msk_cluster.bootstrap_brokers)
        # CfnOutput(self, "BootstrapBrokersTls", value=msk_cluster.bootstrap_brokers_tls)
        # CfnOutput(self, "BootstrapBrokersSaslScram", value=msk_cluster.bootstrap_brokers_sasl_scram)
        CfnOutput(stack, "BootstrapBrokerStringSaslIam", value=stack.msk_cluster.bootstrap_brokers_sasl_iam)
        # CfnOutput(self, "ZookeeperConnection", value=msk_cluster.zookeeper_connection_string)
        # CfnOutput(self, "ZookeeperConnectionTls", value=msk_cluster.zookeeper_connection_string_tls)

class MSKstack(BaseStack):

    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.stream, self.kds_producer_lambda = defineKDSresources(self)

        self.msk_cluster = defineMSKCluster(self,vpc)

        self.topic_name = "carrides"

        
        mskIamRole = iam.Role(self, "AcrMSKrole", 
            assumed_by= iam.ServicePrincipal("ec2.amazonaws.com"),
            role_name= "msk-role",
            description= "Role external client can assume to do action on MSK"
        )

        clusterPolicy = iam.Policy(self,"AcrClusterPolicy",
                            statements=[
                               iam.PolicyStatement(
                                effect= iam.Effect.ALLOW,
                                actions=["kafka-cluster:Connect",
                                         "kafka-cluster:DescribeCluster",
                                         "kafka-cluster:DescribeCluster",
                                         "kafka:Get*"],
                                        resources=[self.msk_cluster.cluster_arn]
                                ),
                                iam.PolicyStatement(
                                effect= iam.Effect.ALLOW,
                                actions=["kafka-cluster:DescribeTopic",
                                    "kafka-cluster:CreateTopic",
                                    "kafka-cluster:WriteData",
                                    "kafka-cluster:ReadData",
                                    "kafka-cluster:AlterGroup",
                                    "kafka-cluster:DescribeGroup"
                                    ],
                                    resources=[self.msk_cluster.cluster_arn + "/*"]
                                )

                            ])
        
        mskIamRole.attach_inline_policy(clusterPolicy)  
        # mskIamRole.attach_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("")) 
     
        # lambda as MSK consumer
        consumer_lambda = lbda.Function(self, "CarRideMSKConsumerLambda",
                                           runtime=lbda.Runtime.PYTHON_3_9,
                                           code=lbda.Code.from_asset("../src/msk-consumer"),
                                           handler="MSKConsumer.lambda_handler",
                                           environment={
                                               "TOPIC_NAME": self.topic_name
                                           }
        )
        
        consumer_lambda.add_event_source(les.ManagedKafkaEventSource(
            cluster_arn=self.msk_cluster.cluster_arn,
            topic=self.topic_name,
            batch_size=100,  # default
            starting_position=lbda.StartingPosition.TRIM_HORIZON
        ))

        outputResources(self)
        



    


    

    