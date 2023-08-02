from typing import List
from typing import Tuple
import logging as log
import boto3

from aws_cdk import (
    CfnOutput,
    aws_ec2 as ec2,
    aws_logs as logs,
    aws_msk_alpha as msk,
    aws_iam as iam
)

from constructs import Construct
from helpers.helpers import get_topic_name, get_group_name

log.basicConfig(level=log.INFO)

client = boto3.client('kafka')

# Get MSK configuration defined externally via script
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
Define a MSK Cluster within the private subnets of the VPC, with the iam role to be assumed by client apps 
to create groups, topics,...
'''    
class MSKCluster(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        kafka_vpc: ec2.IVpc,
        config: dict
    ) -> None:
        
        super().__init__(scope, construct_id)
        vpc = kafka_vpc
        sg = self.init_kafka_security_group(vpc=vpc)
        self.kafka_cluster = self.defineMSKCluster(construct_id,vpc, sg, config)
        self.client_iam_role = self.define_msk_client_iam_role(self.kafka_cluster.cluster_arn)
        self.security_group=sg
        CfnOutput(scope, "BootstrapBrokerStringSaslIam", value=self.kafka_cluster.bootstrap_brokers_sasl_iam)
       

    @property
    def get_kafka_cluster(self) -> msk.Cluster:
        return self.kafka_cluster

    @property
    def get_security_group(self) -> ec2.ISecurityGroup:
        return self.security_group

    def init_kafka_security_group(self, vpc: ec2.IVpc):
        kafka_security_group = ec2.SecurityGroup(
            self,
            "kafka_client_security_group",
            vpc=vpc,
            description="kafka client security group"
        )


        self.allow_tcp_ports_to_internally(kafka_security_group.connections, 
                                      [(2181, "Default Zookeeper"), 
                                       (2182, "TLS Zookeeper"),                          
                                       (9098, "IAM"),
                                       (9198, "IAM_public")])

        '''
        if using other authentication mechanism
            (9092, "Plaintext"),
            (9094,"TLS"),
            (9194,"TLS_public"),
            (9096, "SCRAM_SASL"),
            (9196, "SCRAM_SASL_public"),
        '''
        return kafka_security_group


    '''
    Define cross account, same region role and policy for client apps to access MSK
    '''
    def define_msk_client_iam_role(self, msk_cluster_arn: str):
        mskIamRole = iam.Role(self, "AcrMSKclientRole", 
            assumed_by= iam.ServicePrincipal("ec2.amazonaws.com"),
            role_name= "AcrMSKclientRole",
            description= "Role external client can assume to do action on MSK"
        )
        mskIamRole.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonSSMManagedInstanceCore"
            )
        )
        clusterPolicy = iam.Policy(self,"AcrMSKClusterPolicy",
                            statements=[
                               iam.PolicyStatement(
                                effect= iam.Effect.ALLOW,
                                actions=["kafka-cluster:Connect",
                                         "kafka-cluster:AlterCluster",
                                         "kafka-cluster:DescribeCluster",
                                         "kafka:ListClusters",
                                         "kafka:GetBootstrapBrokers",
                                         "kafka:Get*"],
                                        resources=[msk_cluster_arn]
                                ),
                                iam.PolicyStatement(
                                    effect= iam.Effect.ALLOW,
                                    actions=[
                                        "kafka-cluster:WriteData",
                                        "kafka-cluster:ReadData",
                                        "kafka-cluster:*Topic*",
                                        ],
                                        resources=[get_topic_name(kafka_cluster_arn=msk_cluster_arn, topic_name="*")]
                                    ),
                                iam.PolicyStatement(
                                    effect= iam.Effect.ALLOW,
                                    actions=["kafka-cluster:AlterGroup",
                                        "kafka-cluster:DescribeGroup"
                                        ],
                                        resources=[ get_group_name(kafka_cluster_arn=msk_cluster_arn, group_name="*")]
                                    )
                             
                            ])
        
        mskIamRole.attach_inline_policy(clusterPolicy)
        return mskIamRole

    def defineMSKCluster(self, 
                         name: str,
                         vpc: ec2.Vpc,  
                         mskSecurityGroup: ec2.ISecurityGroup,
                         config: dict):
        cwLogGroup = logs.LogGroup(self,"/msk",retention=logs.RetentionDays.ONE_DAY)
        
        
        # At that time configuration info is not very helpful, better use shell script.
        confInfo = getMSKConfigurationCreated()
        # See https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_msk_alpha.html
        msk_cluster = msk.Cluster(self, name,
            cluster_name=name,
            kafka_version=msk.KafkaVersion.V2_8_1,
            vpc=vpc,
            configuration_info = confInfo,
            instance_type=ec2.InstanceType(config.get("msk_ec2_type")),
            number_of_broker_nodes=1, # In each AZ !!!
            security_groups=[mskSecurityGroup],
            #vpc_subnets=ec2.SubnetSelection( subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            ebs_storage_info= msk.EbsStorageInfo(volume_size=10),
            logging=msk.BrokerLogging(cloudwatch_log_group=cwLogGroup),             
            client_authentication=msk.ClientAuthentication.sasl(
                iam=True
            ),
            monitoring= msk.MonitoringConfiguration(
                            cluster_monitoring_level=msk.ClusterMonitoringLevel.DEFAULT,
                            enable_prometheus_jmx_exporter=True,
                            enable_prometheus_node_exporter=True
                        )

        )

        return msk_cluster



    
    def allow_tcp_ports_to_internally (self,connection:ec2.Connections, ports:List[Tuple[int, str]]):
        for port in ports:
            connection.allow_internally(ec2.Port.tcp(port=port[0]), description=port[1])

        return 