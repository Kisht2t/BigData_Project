variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Project prefix used for all resource names"
  type        = string
  default     = "mars"
}

variable "anthropic_api_key" {
  description = "Anthropic API key for Claude"
  type        = string
  sensitive   = true
}

variable "qdrant_url" {
  description = "Qdrant Cloud cluster URL"
  type        = string
}

variable "qdrant_api_key" {
  description = "Qdrant Cloud API key"
  type        = string
  sensitive   = true
}

variable "orchestrator_image" {
  description = "ECR image URI for orchestrator"
  type        = string
}

variable "worker_image" {
  description = "ECR image URI for worker"
  type        = string
}

variable "frontend_image" {
  description = "ECR image URI for frontend"
  type        = string
}

variable "domain_name" {
  description = "Custom domain (e.g. marsresearch.io). Leave empty to use ALB URL only."
  type        = string
  default     = ""
}

variable "alarm_email" {
  description = "Email address to receive CloudWatch alarm notifications"
  type        = string
  default     = ""
}
