variable "project" {}

# ─── S3 ────────────────────────────────────────────────────────────────
resource "aws_s3_bucket" "documents" {
  bucket = "${var.project}-documents-${data.aws_caller_identity.current.account_id}"

  tags = { Project = var.project }
}

resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id
  versioning_configuration { status = "Disabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "documents" {
  bucket                  = aws_s3_bucket.documents.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ─── SQS ───────────────────────────────────────────────────────────────
resource "aws_sqs_queue" "agent_tasks" {
  name                       = "${var.project}-agent-tasks"
  visibility_timeout_seconds = 60
  message_retention_seconds  = 86400  # 1 day

  tags = { Project = var.project }
}

# ─── DynamoDB — retrieval results ──────────────────────────────────────
resource "aws_dynamodb_table" "results" {
  name         = "${var.project}-results"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "correlation_id"
  range_key    = "source"

  attribute {
    name = "correlation_id"
    type = "S"
  }

  attribute {
    name = "source"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = { Project = var.project }
}

# ─── DynamoDB — conversation history ───────────────────────────────────
resource "aws_dynamodb_table" "history" {
  name         = "${var.project}-history"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "session_id"
  range_key    = "timestamp"

  attribute {
    name = "session_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = { Project = var.project }
}

data "aws_caller_identity" "current" {}

# ─── Outputs ───────────────────────────────────────────────────────────
output "s3_bucket_name"    { value = aws_s3_bucket.documents.bucket }
output "sqs_queue_url"     { value = aws_sqs_queue.agent_tasks.url }
output "sqs_queue_arn"     { value = aws_sqs_queue.agent_tasks.arn }
output "dynamodb_results"  { value = aws_dynamodb_table.results.name }
output "dynamodb_history"  { value = aws_dynamodb_table.history.name }
