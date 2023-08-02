import os
from aws_cdk import (
    Arn as arn,
    ArnFormat as af,
    Fn as fn
)
def getAppEnv():
    appName=os.getenv("APP_NAME").lower()
    if not appName:
        appName="app"
    if not os.path.isfile(f"./config/{appName}.yaml"):
        raise RuntimeError(f"File config/{appName}.yaml not found")
    return appName


def get_topic_name(kafka_cluster_arn: str, topic_name: str):

    # cluster-name/cluster-uuid
    _arn = arn.split(kafka_cluster_arn, af.SLASH_RESOURCE_SLASH_RESOURCE_NAME)
    cluster_name = _arn.resource
    cluster_uuid = _arn.resource_name

    prefix_arn = arn.split(kafka_cluster_arn, af.COLON_RESOURCE_NAME)

    # arn:{partition}:{service}:{region}:{account}:{resource}{sep}{resource-name}
    arn_with_topic = fn.join(
        delimiter="",
        list_of_values=[
            "arn",
            ":",
            prefix_arn.partition,
            ":",
            prefix_arn.service,
            ":",
            prefix_arn.region,
            ":",
            prefix_arn.account,
            ":topic/",
            cluster_name,
            "/",
            cluster_uuid,
            "/",
            topic_name,
        ],  # type: ignore
    )

    return arn_with_topic

def get_group_name(kafka_cluster_arn: str, group_name: str):

    # cluster-name/cluster-uuid
    _arn = arn.split(kafka_cluster_arn, af.SLASH_RESOURCE_SLASH_RESOURCE_NAME)
    cluster_name = _arn.resource
    cluster_uuid = _arn.resource_name

    prefix_arn = arn.split(kafka_cluster_arn, af.COLON_RESOURCE_NAME)

    # arn:{partition}:{service}:{region}:{account}:{resource}{sep}{resource-name}
    arn_with_group = fn.join(
        delimiter="",
        list_of_values=[
            "arn",
            ":",
            prefix_arn.partition,
            ":",
            prefix_arn.service,
            ":",
            prefix_arn.region,
            ":",
            prefix_arn.account,
            ":group/",
            cluster_name,
            "/",
            cluster_uuid,
            "/",
            group_name,
        ],  # type: ignore
    )

    return arn_with_group