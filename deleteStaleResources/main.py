import boto3
from datetime import datetime, timedelta


def lambda_handler(event, context):
    ec2 = boto3.client("ec2")

    # Get a list of resources (e.g., EC2 instances)
    response = ec2.describe_instances()

    # Define the age threshold (24 hours)
    age_threshold = datetime.utcnow() - timedelta(hours=24)

    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            launch_time = instance["LaunchTime"]
            instance_id = instance["InstanceId"]

            # Check if the instance has the "Do-not-delete" tag
            tags = ec2.describe_tags(
                Filters=[{"Name": "resource-id", "Values": [instance_id]}]
            )["Tags"]
            do_not_delete_tag = any(tag["Key"] == "Do-not-delete" for tag in tags)

            if launch_time < age_threshold and not do_not_delete_tag:
                # Delete the resource
                ec2.terminate_instances(InstanceIds=[instance_id])
                print(f"Terminated instance: {instance_id}")
