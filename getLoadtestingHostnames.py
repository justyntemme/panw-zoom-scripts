import boto3
import os


access_key = os.environ['awsKey']
secret_key = os.environ['awsSecret']
region = 'us-east-2'

addresses = []

client = boto3.client('ec2', aws_access_key_id=access_key, aws_secret_access_key=secret_key,
                                  region_name=region)

conn = boto3.resource('ec2', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
instances = conn.instances.filter(Filters=[{'Name': 'tag:Name', 'Values': ['load-testing']}])
for instance in instances:
    if instance.state["Name"] == "running":
        addresses.append(instance.private_dns_name)
print("\n".join(addresses))


