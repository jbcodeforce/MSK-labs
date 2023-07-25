import boto3
from aws_cdk import (
    CfnOutput,
    aws_ec2 as ec2,
    aws_msk_alpha as msk,
    aws_iam as iam,
    aws_lambda as lbda,
    aws_lambda_event_sources as les,

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
    
class MSKstack(BaseStack):

    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.topic_name = "carrides"

        mskSecurityGroup = ec2.SecurityGroup(self, "AcrMSKSecurityGroup",
                                security_group_name="AcrMSKSecurityGroup",
                                vpc=vpc,
                                allow_all_outbound=True
                            )
       
        # At that time configuration info is not very helpful, better use shell script.
        confInfo = getMSKConfigurationCreated()
        msk_cluster = msk.Cluster(self, "AcrCluster",
            cluster_name="AcrCluster",
            kafka_version=msk.KafkaVersion.V3_4_0,
            vpc=vpc,
            configuration_info = confInfo,
            instance_type=ec2.InstanceType("kafka.t3.small"),
            number_of_broker_nodes=1, # In each AZ !!!
            security_groups=[mskSecurityGroup],
            vpc_subnets=ec2.SubnetSelection( subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            ebs_storage_info= msk.EbsStorageInfo(volume_size=10),                         
            client_authentication=msk.ClientAuthentication.sasl(
                #scram=True
                iam=True
            )

        )
        # use when authentication KMS key was created
        # msk_cluster.add_user("mskAdmin")

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
                                        resources=[msk_cluster.cluster_arn]
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
                                    resources=[msk_cluster.cluster_arn + "/*"]
                                )

                            ])
        
        mskIamRole.attach_inline_policy(clusterPolicy)  
        # mskIamRole.attach_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("")) 
        # MSK may need traffic from anywhere
        msk_cluster.connections.allowFromAnyIpv4(ec2.Port.allTraffic(), "allow all from anywhere");
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
            cluster_arn=msk_cluster.cluster_arn,
            topic=self.topic_name,
            batch_size=100,  # default
            starting_position=lbda.StartingPosition.TRIM_HORIZON
        ))

        CfnOutput(self,"Kafka Bootstrap SASL/SCRAM",value=msk_cluster.bootstrap_brokers_sasl_scram)
        CfnOutput(self,"Kafka Bootstrap",value=msk_cluster.bootstrap_brokers)
        CfnOutput(self,"Kafka Cluster ARN",value=msk_cluster.cluster_arn)
