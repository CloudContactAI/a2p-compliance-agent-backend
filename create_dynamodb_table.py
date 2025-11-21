"""
CloudContactAI A2P 10DLC Compliance Agent - DynamoDB Table Creator
Copyright (c) 2024 CloudContactAI, LLC. All rights reserved.

Utility script to create the DynamoDB table for A2P compliance submissions.
Run once during initial setup.
"""
import boto3

def create_submissions_table():
    session = boto3.Session(profile_name='ccai')
    dynamodb = session.resource('dynamodb', region_name='us-east-1')
    
    table = dynamodb.create_table(
        TableName='a2p-submissions',
        KeySchema=[
            {'AttributeName': 'submission_id', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'submission_id', 'AttributeType': 'S'},
            {'AttributeName': 'session_id', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'session-timestamp-index',
                'KeySchema': [
                    {'AttributeName': 'session_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'},
                'BillingMode': 'PAY_PER_REQUEST'
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    print(f"Creating table {table.table_name}...")
    table.wait_until_exists()
    print("Table created successfully!")

if __name__ == '__main__':
    create_submissions_table()
