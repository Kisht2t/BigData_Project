variable "project" {}
variable "aws_region" {}
variable "orchestrator_image" {}
variable "worker_image" {}
variable "frontend_image" {}
variable "orchestrator_task_role_arn" {}
variable "worker_task_role_arn" {}
variable "frontend_task_role_arn" {}
variable "ecs_execution_role_arn" {}
variable "public_subnet_ids" { type = list(string) }
variable "ecs_security_group_id" {}
variable "orchestrator_tg_arn" {}
variable "frontend_tg_arn" {}
variable "sqs_queue_url" {}
variable "dynamodb_results_table" {}
variable "dynamodb_history_table" {}
variable "s3_bucket_name" {}
variable "anthropic_secret_arn" {}
variable "qdrant_secret_arn" {}

# ─── ECS Cluster ───────────────────────────────────────────────────────
resource "aws_ecs_cluster" "main" {
  name = "${var.project}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = { Project = var.project }
}

# ─── CloudWatch Log Groups ─────────────────────────────────────────────
resource "aws_cloudwatch_log_group" "orchestrator" {
  name              = "/ecs/${var.project}/orchestrator"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/ecs/${var.project}/worker"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/${var.project}/frontend"
  retention_in_days = 7
}

# ─── Orchestrator Task Definition ──────────────────────────────────────
resource "aws_ecs_task_definition" "orchestrator" {
  family                   = "${var.project}-orchestrator"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  task_role_arn            = var.orchestrator_task_role_arn
  execution_role_arn       = var.ecs_execution_role_arn

  container_definitions = jsonencode([{
    name      = "orchestrator"
    image     = var.orchestrator_image
    essential = true
    portMappings = [{ containerPort = 8000, protocol = "tcp" }]
    environment = [
      { name = "ENVIRONMENT",            value = "production" },
      { name = "AWS_REGION",             value = var.aws_region },
      { name = "SQS_QUEUE_URL",          value = var.sqs_queue_url },
      { name = "DYNAMODB_TABLE_NAME",    value = var.dynamodb_results_table },
      { name = "DYNAMODB_HISTORY_TABLE", value = var.dynamodb_history_table },
      { name = "S3_BUCKET_NAME",         value = var.s3_bucket_name },
    ]
    secrets = [
      { name = "ANTHROPIC_API_KEY", valueFrom = "${var.anthropic_secret_arn}:api_key::" },
      { name = "QDRANT_URL",        valueFrom = "${var.qdrant_secret_arn}:url::" },
      { name = "QDRANT_API_KEY",    valueFrom = "${var.qdrant_secret_arn}:api_key::" },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.orchestrator.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

# ─── Worker Task Definition ────────────────────────────────────────────
resource "aws_ecs_task_definition" "worker" {
  family                   = "${var.project}-worker"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  task_role_arn            = var.worker_task_role_arn
  execution_role_arn       = var.ecs_execution_role_arn

  container_definitions = jsonencode([{
    name      = "worker"
    image     = var.worker_image
    essential = true
    environment = [
      { name = "ENVIRONMENT",         value = "production" },
      { name = "AWS_REGION",          value = var.aws_region },
      { name = "SQS_QUEUE_URL",       value = var.sqs_queue_url },
      { name = "DYNAMODB_TABLE_NAME", value = var.dynamodb_results_table },
    ]
    secrets = [
      { name = "QDRANT_URL",     valueFrom = "${var.qdrant_secret_arn}:url::" },
      { name = "QDRANT_API_KEY", valueFrom = "${var.qdrant_secret_arn}:api_key::" },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.worker.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

# ─── Frontend Task Definition ──────────────────────────────────────────
resource "aws_ecs_task_definition" "frontend" {
  family                   = "${var.project}-frontend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  task_role_arn            = var.frontend_task_role_arn
  execution_role_arn       = var.ecs_execution_role_arn

  container_definitions = jsonencode([{
    name      = "frontend"
    image     = var.frontend_image
    essential = true
    portMappings = [{ containerPort = 3000, protocol = "tcp" }]
    environment = [
      { name = "NEXT_PUBLIC_ORCHESTRATOR_URL", value = "http://${var.project}-alb/api" },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.frontend.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

# ─── ECS Services ──────────────────────────────────────────────────────
resource "aws_ecs_service" "orchestrator" {
  name            = "${var.project}-orchestrator"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.orchestrator.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.public_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = var.orchestrator_tg_arn
    container_name   = "orchestrator"
    container_port   = 8000
  }

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  lifecycle {
    ignore_changes = [task_definition]
  }
}

resource "aws_ecs_service" "worker" {
  name            = "${var.project}-worker"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.public_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = true
  }

  lifecycle {
    ignore_changes = [task_definition]
  }
}

resource "aws_ecs_service" "frontend" {
  name            = "${var.project}-frontend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.public_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = var.frontend_tg_arn
    container_name   = "frontend"
    container_port   = 3000
  }

  lifecycle {
    ignore_changes = [task_definition]
  }
}

output "cluster_name" { value = aws_ecs_cluster.main.name }
