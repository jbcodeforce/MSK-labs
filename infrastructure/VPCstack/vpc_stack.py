from aws_cdk import (
    # Duration,
    CfnOutput,
    aws_ec2 as ec2,
    aws_iam as iam
)
from constructs import Construct
from helpers.BaseStack import BaseStack
import requests

CIDR="10.0.0.0/16"

class VPCstack(BaseStack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        if self.config.get("vpc_name") is None:
            self.vpc = self.create_vpc(construct_id)
        else:
            self.vpc = self.lookup_vpc(self.config.get("vpc_name"))
        self.bastionSecurityGroup = self.createBastionSecurityGroup()
        
        
    def create_vpc(self, vpc_name: str) -> ec2.Vpc:

        vpc = ec2.Vpc(self, vpc_name,
            cidr=self.config.get("vpc_cidr"),
            max_azs=2,
            vpc_name=vpc_name,
            nat_gateways=1,
            ip_addresses=ec2.IpAddresses.cidr(CIDR),
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=self.config.get("cidr_mask")
                ),
                ec2.SubnetConfiguration(
                    name="private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=self.config.get("cidr_mask")
                )
            ]
        )

        return vpc
    
    def createBastionSecurityGroup(self):
        r=requests.get("https://checkip.amazonaws.com")
        my_ip = r.text.strip()

        amzn_linux = ec2.MachineImage.latest_amazon_linux2(
            edition= ec2.AmazonLinuxEdition.STANDARD,
            virtualization= ec2.AmazonLinuxVirt.HVM,
            storage= ec2.AmazonLinuxStorage.GENERAL_PURPOSE
        )

        sg = ec2.SecurityGroup(self, "bastion-sg", vpc=self.vpc, allow_all_outbound=True,)

        role = iam.Role(
            self,
            "BastionRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            description="Role for Bastion host",
        )
        policy = iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")
        role.add_managed_policy(policy)
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("EC2InstanceProfileForImageBuilderECRContainerBuilds"))
 
        myAmiImage = ec2.LookupMachineImage(name="MyAcrBastion")
        bastion = ec2.Instance(
            self,
            "BastionHost",
            instance_name=self.config.get("bastion_name"),
            key_name=self.config.get("key_name"),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.MICRO),
            machine_image=myAmiImage,
            security_group=sg,
            role=role,
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
        )

        bastion.connections.allow_from(ec2.Peer.ipv4(f"{my_ip}/32"), ec2.Port.all_traffic())

        CfnOutput(self, "bastion-public-dns-name", value=bastion.instance_public_dns_name)
        CfnOutput(self, "bastion-private-ip", value=bastion.instance_private_ip)

        return sg
