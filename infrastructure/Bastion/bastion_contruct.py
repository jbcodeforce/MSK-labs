

from aws_cdk import (
    CfnOutput,
    aws_iam as iam,
    aws_ec2 as ec2
    )

from constructs import Construct

import requests

'''
This class is responsible for creating the bastion host with Java, AWS, Kafka, AWS MSK authentication jar...
It is deployed on the public of the subnet in the specified VPC.
'''
class BastionHost(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        theVpc: ec2.IVpc,
        roleToAssume: iam.Role
    ) -> None:
        
        super().__init__(scope, construct_id)

        if roleToAssume is None:
            roleToAssume = build_iam_role(self)

        self.security_group = ec2.SecurityGroup(
            self,
            "bastion_host_sg",
            vpc=theVpc,
            description="security group for bastion host"
        )
        
        bastion_host_instance = ec2.Instance(
            self,
            "bastion_host",
            vpc=theVpc,
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.MICRO),
            machine_image=build_or_get_am_image(),
            role=roleToAssume,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
            security_group=self.security_group
        )

        define_user_data(bastion_host_instance)
        authorize_ssh_access(bastion_host_instance)
    
        CfnOutput(
            self,
            "bastionoutput",
            value=bastion_host_instance.instance_id,
            description="Bastion host id",
            export_name="BastionHostIp",
        )

        
        
        

def build_iam_role(scope):
    iamRole = iam.Role(
            scope,
            "BastionRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            description="Role for Bastion host",
        )
    policy = iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")
    iamRole.add_managed_policy(policy)
    # Solution may include container apps deployed on ECR. We can use the bastion to build those image during dev too.
    iamRole.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("EC2InstanceProfileForImageBuilderECRContainerBuilds"))
    return iamRole

'''
Can use an existing snapshot or build a new image.
'''
def build_or_get_am_image():
    myAmiImage = ec2.LookupMachineImage(name="MyAcrBastion")
    if myAmiImage == None:
        myAmiImage=ec2.MachineImage.latest_amazon_linux2(
                    edition= ec2.AmazonLinuxEdition.STANDARD,
                    virtualization= ec2.AmazonLinuxVirt.HVM,
                    storage= ec2.AmazonLinuxStorage.GENERAL_PURPOSE
                )
    return myAmiImage


    

def define_user_data(host_instance: ec2.Instance):
        # Get kafka, AWS Cli, authentication library, with Java 11
        data = open("./Bastion/user_data.sh", "rb").read()
        commands = str(data,'utf-8')
        print(commands)
        host_instance.add_user_data(commands)


def authorize_ssh_access(host_instance: ec2.Instance):      
    my_ip=requests.get("https://checkip.amazonaws.com").text.strip()
    host_instance.connections.allow_from(ec2.Peer.ipv4(f"{my_ip}/32"), ec2.Port.tcp(22))


 
