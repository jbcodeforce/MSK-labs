#!/usr/bin/env python3
import os

import aws_cdk as cdk


from helpers.helpers import getAppEnv

from SolutionStack.main_stack import SolutionStack

import yaml

# Externalize some of the application parameters
def load_configuration(appName: str) -> dict:
    with open(f"./config/{appName}.yaml", 'r') as f:
        vars= yaml.load(f, Loader=yaml.FullLoader)
    return vars

def init_app() -> cdk.App:
    app = cdk.App()
    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION'))
    app_env = getAppEnv()
    config = load_configuration(app_env)
    print(config)
    SolutionStack(app, f"{app_env}-msk-demo", env=env,config=config)
    return app


if __name__ == "__main__":
    app = init_app()
    app.synth()