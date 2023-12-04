import boto3
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def calculate_age_in_hours(creation_time_utc, current_time_utc):
    age = current_time_utc - creation_time_utc
    return age.total_seconds() / 3600  # Convert seconds to hours


def get_eks_cluster_tags(eks_client, cluster_name):
    # Retrieve EKS cluster tags
    account_id = boto3.client("sts").get_caller_identity().get("Account")
    region = boto3.session.Session().region_name

    resource_arn = f"arn:aws:eks:{region}:{account_id}:cluster/{cluster_name}"
    response = eks_client.list_tags_for_resource(resourceArn=resource_arn)
    return response.get("tags", {})


def lambda_handler(event, context):
    try:
        # Set the region to your AWS region
        region = context.invoked_function_arn.split(":")[
            3
        ]  # Extract region from Lambda ARN

        # Initialize AWS clients for EC2 and EKS
        ec2_client = boto3.client("ec2", region_name=region)
        eks_client = boto3.client("eks", region_name=region)

        # Get current time in UTC
        current_time_utc = datetime.now(timezone.utc)

        # Calculate the threshold time (24 hours ago)
        threshold_time_utc = current_time_utc - timedelta(hours=24)

        # Check EC2 instances
        ec2_instances = ec2_client.describe_instances()
        for reservation in ec2_instances["Reservations"]:
            for instance in reservation["Instances"]:
                instance_id = instance["InstanceId"]
                launch_time_utc = instance["LaunchTime"].replace(tzinfo=timezone.utc)
                tags = {tag["Key"]: tag["Value"] for tag in instance.get("Tags", [])}

                age_in_hours = calculate_age_in_hours(launch_time_utc, current_time_utc)

                # Check for "do-not-delete" tag
                do_not_delete = tags.get("do-not-delete", "").lower()
                if do_not_delete == "true":
                    print(
                        f"Skipping EC2 instance {instance_id} with 'do-not-delete' tag set to true"
                    )
                    print(
                        f"Instance ID: {instance_id}, Tags: {tags}, Age: {age_in_hours:.2f} hours"
                    )
                else:
                    if launch_time_utc < threshold_time_utc:
                        print(f"Deleting EC2 instance {instance_id}")
                        # ec2_client.terminate_instances(InstanceIds=[instance_id])
                    else:
                        print(
                            f"EC2 instance {instance_id} is not older than 24 hours but can be deleted"
                        )
                        print(
                            f"Instance ID: {instance_id}, Tags: {tags}, Age: {age_in_hours:.2f} hours"
                        )

        # Check EKS clusters
        eks_clusters = eks_client.list_clusters()
        for cluster_name in eks_clusters["clusters"]:
            cluster_tags = get_eks_cluster_tags(eks_client, cluster_name)

            # Extract the creation time directly as a datetime object
            cluster_details = eks_client.describe_cluster(name=cluster_name)
            created_at_utc = cluster_details["cluster"]["createdAt"].replace(
                tzinfo=timezone.utc
            )

            age_in_hours = calculate_age_in_hours(created_at_utc, current_time_utc)

            # Extract tags from the tags list, if available
            tags = (
                cluster_tags  # Adjust this line based on the structure of your response
            )

            # Check for "do-not-delete" tag
            do_not_delete = tags.get("do-not-delete", "").lower()
            if do_not_delete == "true":
                print(
                    f"Skipping EKS cluster {cluster_name} with 'do-not-delete' tag set to true"
                )
                print(
                    f"Cluster Name: {cluster_name}, Tags: {tags}, Age: {age_in_hours:.2f} hours"
                )
            else:
                if created_at_utc < threshold_time_utc:
                    print(f"Deleting EKS cluster {cluster_name}")
                    # Delete EKS cluster - Note: This will also delete associated resources
                    # eks_client.delete_cluster(name=cluster_name)
                else:
                    print(
                        f"EKS cluster {cluster_name} is not older than 24 hours but can be deleted"
                    )
                    print(
                        f"Cluster Name: {cluster_name}, Tags: {tags}, Age: {age_in_hours:.2f} hours"
                    )

        return {"statusCode": 200, "body": "Function execution completed successfully."}
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise e
