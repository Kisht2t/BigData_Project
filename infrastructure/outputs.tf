output "alb_url" {
  description = "Application Load Balancer URL — your app's public address"
  value       = "http://${module.networking.alb_dns_name}"
}

output "ecs_cluster_name" {
  value = module.ecs.cluster_name
}

output "s3_bucket_name" {
  value = module.storage.s3_bucket_name
}

output "sqs_queue_url" {
  value = module.storage.sqs_queue_url
}

output "ecr_orchestrator" {
  value = aws_ecr_repository.orchestrator.repository_url
}

output "ecr_worker" {
  value = aws_ecr_repository.worker.repository_url
}

output "ecr_frontend" {
  value = aws_ecr_repository.frontend.repository_url
}
