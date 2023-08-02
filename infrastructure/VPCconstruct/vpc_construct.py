from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_logs as logs
)
from constructs import Construct

CIDR="10.0.0.0/16"
CIDR_MASK=24
'''
Create a VPC named {appname}-vpc with 2 private and 2 public subnets, the corresponding routing tables
and Internet gateway.
The security group 
'''
class VPCbase(Construct):
    # Config is a dictionary with application parameter
    def __init__(self, scope: Construct, construct_id: str, config: dict) -> None:
        super().__init__(scope, construct_id)

        subnets=[
                ec2.SubnetConfiguration(
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=CIDR_MASK
                ),
                ec2.SubnetConfiguration(
                    name="private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=CIDR_MASK
                )
            ]
        app_name=config.get("app_name")
        vpc_name=f"{app_name}-vpc"
        self.vpc = ec2.Vpc(self, vpc_name,
            max_azs=2,
            vpc_name=vpc_name,
            nat_gateways=1,
            ip_addresses=ec2.IpAddresses.cidr(CIDR),
            subnet_configuration=subnets
        )
        
        # Define flow logs
        log_group = logs.LogGroup(self, f"{vpc_name}-logs", retention=logs.RetentionDays.ONE_DAY)
        role:iam.IRole = iam.Role(self, 
                                  "VpcFlowLogRole", 
                                  assumed_by=iam.ServicePrincipal("vpc-flow-logs.amazonaws.com"))
        self.vpc.add_flow_log("vpcflowlog", 
                              destination=ec2.FlowLogDestination.to_cloud_watch_logs(log_group=log_group, 
                                                                                     iam_role=role)
                            )


    @property
    def get_vpc(self) -> ec2.IVpc:
        return self.vpc
    
