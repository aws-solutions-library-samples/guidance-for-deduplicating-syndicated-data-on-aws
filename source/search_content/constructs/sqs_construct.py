from aws_cdk import (
    aws_sqs as sqs,
)
from constructs import Construct
from search_content.config import Queue


class ContentQueue(Construct):

    def __init__(self, scope: Construct, contruct_id: str) -> None:
        super().__init__(scope, contruct_id)

        # The code that defines your stack goes here

        queue = sqs.Queue(
            self, "SearchContentQueue",
            visibility_timeout=Queue.VISIBILITY_TIME_OUT,
            retention_period=Queue.RETENTION,
            encryption=sqs.QueueEncryption.SQS_MANAGED,
            enforce_ssl=True,
            queue_name= Queue.NAME
        )

        self.arn = queue.queue_arn
        self.queue = queue
