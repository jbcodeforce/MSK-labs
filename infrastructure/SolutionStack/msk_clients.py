from aws_cdk import (
    aws_msk_alpha as msk,
    aws_iam as iam,
    aws_lambda as lbda,
    aws_ec2 as ec2,
    aws_lambda_event_sources as les,
)

from constructs import Construct

class MSKClients(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        msk_cluster: msk.Cluster,
        config: dict
    ) -> None:
        
        super().__init__(scope, construct_id)

        # lambda as MSK consumer
        consumer_lambda = lbda.Function(self, "CarRideMSKConsumerLambda",
                                           runtime=lbda.Runtime.PYTHON_3_9,
                                           code=lbda.Code.from_asset("../src/msk-consumer"),
                                           handler="MSKConsumer.lambda_handler",
                                           environment={
                                               "TOPIC_NAME": config.get("msk_topic_name")
                                           }
        )
        
        consumer_lambda.add_event_source(les.ManagedKafkaEventSource(
            cluster_arn= msk_cluster.cluster_arn,
            topic=config.get("msk_topic_name"),
            batch_size=100,  # default
            starting_position=lbda.StartingPosition.TRIM_HORIZON
        ))

        