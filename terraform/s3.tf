# --- S3 Bucket for ALB Logs ---
resource "aws_s3_bucket" "lb_logs" {
  # Bucket names must be globally unique
  bucket        = "${var.app_name}-logs-${random_id.bucket_suffix.hex}"
  force_destroy = true # Allows terraform to delete the bucket even if it has logs

  tags = {
    Name        = "ALB Logs"
    Environment = "Dev"
  }
}

# --- Lifecycle Rule (Free Tier Safety) ---
resource "aws_s3_bucket_lifecycle_configuration" "lb_logs_lifecycle" {
  bucket = aws_s3_bucket.lb_logs.id

  rule {
    id     = "delete-logs-after-7-days"
    status = "Enabled"

    expiration {
      days = 7 # Deletes logs after a week to save space
    }
  }
}

# --- Encryption (Required for ALB Logs) ---
resource "aws_s3_bucket_server_side_encryption_configuration" "lb_logs_encryption" {
  bucket = aws_s3_bucket.lb_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256" # Only SSE-S3 is supported for ALB logs
    }
  }
}

# --- Bucket Policy (Allows ALB to write logs) ---
resource "aws_s3_bucket_policy" "lb_logs_policy" {
  bucket = aws_s3_bucket.lb_logs.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          # This ID (652711504416) is the official AWS ELB account for eu-west-2
          AWS = "arn:aws:iam::652711504416:root"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.lb_logs.arn}/*"
      }
    ]
  })
}

# Random suffix to ensure global bucket name uniqueness
resource "random_id" "bucket_suffix" {
  byte_length = 4
}