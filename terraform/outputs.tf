output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.a2p_repo.repository_url
}

output "load_balancer_dns" {
  description = "Load balancer DNS name"
  value       = aws_lb.a2p_alb.dns_name
}

output "load_balancer_url" {
  description = "Load balancer URL"
  value       = "http://${aws_lb.a2p_alb.dns_name}"
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.a2p_cluster.name
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.a2p_service.name
}
