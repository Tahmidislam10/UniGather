import boto3
import os

def get_table(table_name):
    # If running on EC2, boto3 can use IAM roles instead of hardcoded keys
    dynamodb = boto3.resource('dynamodb', region_name=os.getenv("AWS_REGION", "us-east-1"))
    return dynamodb.Table(table_name)