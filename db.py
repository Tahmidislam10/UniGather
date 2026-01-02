import os
import boto3

# 1. Setup global config
region = os.getenv("AWS_REGION", "eu-west-2")
users_table_name = os.getenv("USERS_TABLE", "users")
events_table_name = os.getenv("EVENTS_TABLE", "events")

# 2. Create the resource
dynamodb = boto3.resource("dynamodb", region_name=region)

# 3. Define the function your app.py is importing
def get_db():
    """Returns the base DynamoDB resource"""
    return dynamodb

# 4. Keep these as exports in case other parts of your app use them
users_table = dynamodb.Table(users_table_name)
events_table = dynamodb.Table(events_table_name)