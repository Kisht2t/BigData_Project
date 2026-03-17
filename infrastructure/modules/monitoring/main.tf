variable "project" {}
variable "aws_region" {}
variable "alb_arn_suffix" {}
variable "orchestrator_tg_arn_suffix" {}
variable "frontend_tg_arn_suffix" {}
variable "alarm_email" { default = "" }

# ─── SNS Topic for alarm notifications ────────────────────────────────
resource "aws_sns_topic" "alarms" {
  name = "${var.project}-alarms"
  tags = { Project = var.project }
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.alarm_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alarms.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

# ─── ALB: 5xx error rate ──────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "alb_5xx" {
  alarm_name          = "${var.project}-alb-5xx-errors"
  alarm_description   = "ALB 5xx error rate > 10 in 5 minutes"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "HTTPCode_ELB_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  ok_actions          = [aws_sns_topic.alarms.arn]

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }

  tags = { Project = var.project }
}

# ─── ALB: target 5xx errors ───────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "target_5xx" {
  alarm_name          = "${var.project}-target-5xx-errors"
  alarm_description   = "Backend 5xx errors > 10 in 5 minutes"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  ok_actions          = [aws_sns_topic.alarms.arn]

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }

  tags = { Project = var.project }
}

# ─── ALB: response time p99 ───────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "response_time" {
  alarm_name          = "${var.project}-response-time-p99"
  alarm_description   = "p99 response time > 30s"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  extended_statistic  = "p99"
  threshold           = 30
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alarms.arn]

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }

  tags = { Project = var.project }
}

# ─── ALB: unhealthy host count ────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "unhealthy_orchestrator" {
  alarm_name          = "${var.project}-orchestrator-unhealthy"
  alarm_description   = "Orchestrator has 0 healthy hosts"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Minimum"
  threshold           = 1
  treat_missing_data  = "breaching"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  ok_actions          = [aws_sns_topic.alarms.arn]

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
    TargetGroup  = var.orchestrator_tg_arn_suffix
  }

  tags = { Project = var.project }
}

resource "aws_cloudwatch_metric_alarm" "unhealthy_frontend" {
  alarm_name          = "${var.project}-frontend-unhealthy"
  alarm_description   = "Frontend has 0 healthy hosts"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Minimum"
  threshold           = 1
  treat_missing_data  = "breaching"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  ok_actions          = [aws_sns_topic.alarms.arn]

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
    TargetGroup  = var.frontend_tg_arn_suffix
  }

  tags = { Project = var.project }
}

# ─── ECS: orchestrator CPU ────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "orchestrator_cpu" {
  alarm_name          = "${var.project}-orchestrator-cpu"
  alarm_description   = "Orchestrator CPU > 80%"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alarms.arn]

  dimensions = {
    ClusterName = "${var.project}-cluster"
    ServiceName = "${var.project}-orchestrator"
  }

  tags = { Project = var.project }
}

# ─── ECS: orchestrator memory ─────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "orchestrator_memory" {
  alarm_name          = "${var.project}-orchestrator-memory"
  alarm_description   = "Orchestrator memory > 80%"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alarms.arn]

  dimensions = {
    ClusterName = "${var.project}-cluster"
    ServiceName = "${var.project}-orchestrator"
  }

  tags = { Project = var.project }
}

# ─── ECS: worker CPU ──────────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "worker_cpu" {
  alarm_name          = "${var.project}-worker-cpu"
  alarm_description   = "Worker CPU > 80%"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alarms.arn]

  dimensions = {
    ClusterName = "${var.project}-cluster"
    ServiceName = "${var.project}-worker"
  }

  tags = { Project = var.project }
}

# ─── SQS: queue depth spike ───────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "sqs_depth" {
  alarm_name          = "${var.project}-sqs-queue-depth"
  alarm_description   = "SQS queue has > 50 messages (workers not keeping up)"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Maximum"
  threshold           = 50
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alarms.arn]

  dimensions = {
    QueueName = "${var.project}-agent-tasks"
  }

  tags = { Project = var.project }
}

# ─── CloudWatch Dashboard ─────────────────────────────────────────────
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric", x = 0, y = 0, width = 12, height = 6
        properties = {
          title  = "ALB Request Count & Error Rate"
          region = var.aws_region
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", var.alb_arn_suffix],
            ["AWS/ApplicationELB", "HTTPCode_ELB_5XX_Count", "LoadBalancer", var.alb_arn_suffix],
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "LoadBalancer", var.alb_arn_suffix]
          ]
          period = 300
          stat   = "Sum"
          view   = "timeSeries"
        }
      },
      {
        type = "metric", x = 12, y = 0, width = 12, height = 6
        properties = {
          title  = "ALB Response Time (p50 / p99)"
          region = var.aws_region
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", var.alb_arn_suffix, { stat = "p50" }],
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", var.alb_arn_suffix, { stat = "p99" }]
          ]
          period = 300
          view   = "timeSeries"
        }
      },
      {
        type = "metric", x = 0, y = 6, width = 12, height = 6
        properties = {
          title  = "ECS CPU Utilization"
          region = var.aws_region
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ClusterName", "${var.project}-cluster", "ServiceName", "${var.project}-orchestrator"],
            ["AWS/ECS", "CPUUtilization", "ClusterName", "${var.project}-cluster", "ServiceName", "${var.project}-worker"],
            ["AWS/ECS", "CPUUtilization", "ClusterName", "${var.project}-cluster", "ServiceName", "${var.project}-frontend"]
          ]
          period = 300
          stat   = "Average"
          view   = "timeSeries"
        }
      },
      {
        type = "metric", x = 12, y = 6, width = 12, height = 6
        properties = {
          title  = "ECS Memory Utilization"
          region = var.aws_region
          metrics = [
            ["AWS/ECS", "MemoryUtilization", "ClusterName", "${var.project}-cluster", "ServiceName", "${var.project}-orchestrator"],
            ["AWS/ECS", "MemoryUtilization", "ClusterName", "${var.project}-cluster", "ServiceName", "${var.project}-worker"],
            ["AWS/ECS", "MemoryUtilization", "ClusterName", "${var.project}-cluster", "ServiceName", "${var.project}-frontend"]
          ]
          period = 300
          stat   = "Average"
          view   = "timeSeries"
        }
      },
      {
        type = "metric", x = 0, y = 12, width = 12, height = 6
        properties = {
          title  = "SQS Queue Depth"
          region = var.aws_region
          metrics = [
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", "${var.project}-agent-tasks"],
            ["AWS/SQS", "NumberOfMessagesSent", "QueueName", "${var.project}-agent-tasks"],
            ["AWS/SQS", "NumberOfMessagesDeleted", "QueueName", "${var.project}-agent-tasks"]
          ]
          period = 300
          stat   = "Sum"
          view   = "timeSeries"
        }
      },
      {
        type = "metric", x = 12, y = 12, width = 12, height = 6
        properties = {
          title  = "Healthy Host Count"
          region = var.aws_region
          metrics = [
            ["AWS/ApplicationELB", "HealthyHostCount", "LoadBalancer", var.alb_arn_suffix, "TargetGroup", var.orchestrator_tg_arn_suffix],
            ["AWS/ApplicationELB", "HealthyHostCount", "LoadBalancer", var.alb_arn_suffix, "TargetGroup", var.frontend_tg_arn_suffix]
          ]
          period = 60
          stat   = "Minimum"
          view   = "timeSeries"
        }
      }
    ]
  })
}

# ─── Outputs ──────────────────────────────────────────────────────────
output "sns_topic_arn"    { value = aws_sns_topic.alarms.arn }
output "dashboard_url"    { value = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${var.project}-dashboard" }
