import boto3
import os

def get_db():
    # This returns the DynamoDB resource, not a specific table
    region = os.getenv("AWS_REGION", "eu-west-2")
    return boto3.resource('dynamodb', region_name=region)