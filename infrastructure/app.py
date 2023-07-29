#!/usr/bin/env python3
import os

import aws_cdk as cdk


from helpers.helpers import getAppEnv

from VPCstack.vpc_stack import VPCstack
from MSKstack.msk_stack import MSKstack

import yaml

def load_configuration(appName: str) -> dict:
    with open(f"./config/{appName}.yaml", 'r') as f:
        vars= yaml.load(f, Loader=yaml.FullLoader)
    return vars

def init_app() -> cdk.App:
    app = cdk.App()
    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION'))
    app_env = getAppEnv()
    config = load_configuration(app_env)
    ## Add nested stacks below
    vpc_stack = VPCstack(app, f"{app_env}-vpc",env=env,config=config)
    msk_stack = MSKstack(app, f"{app_env}-msk",vpc=vpc_stack.vpc,env=env,config=config)
    return app




if __name__ == "__main__":
    app = init_app()
    app.synth()