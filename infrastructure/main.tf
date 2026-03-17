terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment after creating the S3 bucket + DynamoDB table for state:
  # backend "s3" {
  #   bucket         = "mars-terraform-state"
  #   key            = "mars/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "mars-terraform-locks"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region
}

# ─── ECR Repositories ──────────────────────────────────────────────────
resource "aws_ecr_repository" "orchestrator" {
  name                 = "${var.project}-orchestrator"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
  tags                 = { Project = var.project }
}

resource "aws_ecr_repository" "worker" {
  name                 = "${var.project}-worker"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
  tags                 = { Project = var.project }
}

resource "aws_ecr_repository" "frontend" {
  name                 = "${var.project}-frontend"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
  tags                 = { Project = var.project }
}

resource "aws_ecr_repository" "ingestion" {
  name                 = "${var.project}-ingestion"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
  tags                 = { Project = var.project }
}

# ─── Secrets Manager ───────────────────────────────────────────────────
resource "aws_secretsmanager_secret" "anthropic" {
  name = "${var.project}/anthropic"
  tags = { Project = var.project }
}

resource "aws_secretsmanager_secret_version" "anthropic" {
  secret_id     = aws_secretsmanager_secret.anthropic.id
  secret_string = jsonencode({ api_key = var.anthropic_api_key })
}

resource "aws_secretsmanager_secret" "qdrant" {
  name = "${var.project}/qdrant"
  tags = { Project = var.project }
}

resource "aws_secretsmanager_secret_version" "qdrant" {
  secret_id     = aws_secretsmanager_secret.qdrant.id
  secret_string = jsonencode({ url = var.qdrant_url, api_key = var.qdrant_api_key })
}

# ─── Modules ───────────────────────────────────────────────────────────
module "storage" {
  source  = "./modules/storage"
  project = var.project
}

# ─── DNS + TLS (only created when domain_name is set) ──────────────────
module "dns" {
  count        = var.domain_name != "" ? 1 : 0
  source       = "./modules/dns"
  project      = var.project
  domain_name  = var.domain_name
  alb_dns_name = module.networking.alb_dns_name
  alb_zone_id  = module.networking.alb_zone_id
}

module "networking" {
  source          = "./modules/networking"
  project         = var.project
  certificate_arn = var.domain_name != "" ? module.dns[0].certificate_arn : ""
}

# ─── Monitoring ────────────────────────────────────────────────────────
module "monitoring" {
  source                     = "./modules/monitoring"
  project                    = var.project
  aws_region                 = var.aws_region
  alb_arn_suffix             = module.networking.alb_arn_suffix
  orchestrator_tg_arn_suffix = module.networking.orchestrator_tg_arn_suffix
  frontend_tg_arn_suffix     = module.networking.frontend_tg_arn_suffix
  alarm_email                = var.alarm_email
}

module "iam" {
  source               = "./modules/iam"
  project              = var.project
  sqs_queue_arn        = module.storage.sqs_queue_arn
  s3_bucket_name       = module.storage.s3_bucket_name
  dynamodb_results_arn = "arn:aws:dynamodb:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/${module.storage.dynamodb_results}"
  dynamodb_history_arn = "arn:aws:dynamodb:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/${module.storage.dynamodb_history}"
}

module "ecs" {
  source                     = "./modules/ecs"
  project                    = var.project
  aws_region                 = var.aws_region
  orchestrator_image         = var.orchestrator_image
  worker_image               = var.worker_image
  frontend_image             = var.frontend_image
  orchestrator_task_role_arn = module.iam.orchestrator_task_role_arn
  worker_task_role_arn       = module.iam.worker_task_role_arn
  frontend_task_role_arn     = module.iam.frontend_task_role_arn
  ecs_execution_role_arn     = module.iam.ecs_execution_role_arn
  public_subnet_ids          = module.networking.public_subnet_ids
  ecs_security_group_id      = module.networking.ecs_security_group_id
  orchestrator_tg_arn        = module.networking.orchestrator_tg_arn
  frontend_tg_arn            = module.networking.frontend_tg_arn
  sqs_queue_url              = module.storage.sqs_queue_url
  dynamodb_results_table     = module.storage.dynamodb_results
  dynamodb_history_table     = module.storage.dynamodb_history
  s3_bucket_name             = module.storage.s3_bucket_name
  anthropic_secret_arn       = aws_secretsmanager_secret.anthropic.arn
  qdrant_secret_arn          = aws_secretsmanager_secret.qdrant.arn
}

data "aws_caller_identity" "current" {}
