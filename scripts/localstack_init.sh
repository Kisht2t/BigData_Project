#!/bin/bash
# Initializes local AWS resources via LocalStack on container startup

echo "Initializing LocalStack resources..."

AWS="aws --endpoint-url=http://localhost:4566 --region us-east-1"

# SQS Queue
$AWS sqs create-queue --queue-name mars-agent-tasks
echo "Created SQS queue: mars-agent-tasks"

# DynamoDB — retrieval results table
$AWS dynamodb create-table \
  --table-name mars-results \
  --attribute-definitions AttributeName=correlation_id,AttributeType=S AttributeName=source,AttributeType=S \
  --key-schema AttributeName=correlation_id,KeyType=HASH AttributeName=source,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST
echo "Created DynamoDB table: mars-results"

# DynamoDB — conversation history table
$AWS dynamodb create-table \
  --table-name mars-history \
  --attribute-definitions AttributeName=session_id,AttributeType=S AttributeName=timestamp,AttributeType=S \
  --key-schema AttributeName=session_id,KeyType=HASH AttributeName=timestamp,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST
echo "Created DynamoDB table: mars-history"

# S3 Bucket
$AWS s3 mb s3://mars-documents-local
echo "Created S3 bucket: mars-documents-local"

echo "LocalStack initialization complete."
