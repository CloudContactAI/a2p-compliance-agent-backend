# S3 Bucket for Pipeline Artifacts
resource "aws_s3_bucket" "pipeline_artifacts" {
  bucket = "a2p-compliance-pipeline-artifacts-${random_string.bucket_suffix.result}"
}

resource "aws_s3_bucket_versioning" "pipeline_artifacts_versioning" {
  bucket = aws_s3_bucket.pipeline_artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "pipeline_artifacts_encryption" {
  bucket = aws_s3_bucket.pipeline_artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "a2p_logs" {
  name              = "/ecs/a2p-compliance-agent"
  retention_in_days = 7

  tags = {
    Name = "a2p-compliance-logs"
  }
}
