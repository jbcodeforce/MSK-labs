
from aws_cdk import  Stack, aws_ec2 as ec2

from constructs import Construct
from .helpers import getAppEnv


class BaseStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        # Order is important to avoid unexpected keyword argument 'config' exception.
        self.config = kwargs.pop("config", {})
        self.app_env = getAppEnv()
        super().__init__(scope, id, **kwargs)                  

    def lookup_vpc(self, vpc_name: str) -> ec2.Vpc:
        vpc = None
        try:
            vpc=ec2.Vpc.from_lookup(self, vpc_name, is_default=False)
        except:
            pass
        return vpc