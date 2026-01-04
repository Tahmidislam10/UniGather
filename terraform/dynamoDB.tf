# DynamoDB Table for Events
resource "aws_dynamodb_table" "events_table" {
  name           = "events"
  billing_mode   = "PROVISIONED"
  read_capacity  = 5
  write_capacity = 5
  hash_key       = "id"

  attribute {
    name = "id"
    type = "S"
  }

  tags = {
    Name        = "UniGather-Events"
    Environment = "Dev"
  }
}

# DynamoDB Table for Users
resource "aws_dynamodb_table" "users_table" {
  name           = "users"
  billing_mode   = "PROVISIONED"
  read_capacity  = 5
  write_capacity = 5
  hash_key       = "id"

  attribute {
    name = "id"
    type = "S"
  }

  tags = {
    Name        = "UniGather-Users"
    Environment = "Dev"
  }
}