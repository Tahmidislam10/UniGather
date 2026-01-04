import os
import boto3

# Global config setup
region = os.getenv("AWS_REGION", "eu-west-2")
users_table_name = os.getenv("USERS_TABLE", "users")
events_table_name = os.getenv("EVENTS_TABLE", "events")

# Creates the resource
dynamodb = boto3.resource("dynamodb", region_name=region)

def get_db():
    """Returns the base DynamoDB resource"""
    return dynamodb

users_table = dynamodb.Table(users_table_name)
events_table = dynamodb.Table(events_table_name)