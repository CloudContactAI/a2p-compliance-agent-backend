terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.67.0"  # Use much older stable version
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
}

# ECR Repository
resource "aws_ecr_repository" "a2p_repo" {
  name = "a2p-compliance-agent"
}

# CodeBuild for CI/CD
resource "aws_codebuild_project" "a2p_build" {
  name         = "a2p-compliance-agent-build"
  service_role = aws_iam_role.codebuild_role.arn

  artifacts {
    type = "CODEPIPELINE"
  }

  environment {
    compute_type = "BUILD_GENERAL1_SMALL"
    image        = "aws/codebuild/amazonlinux2-x86_64-standard:5.0"
    type         = "LINUX_CONTAINER"
    privileged_mode = true

    environment_variable {
      name  = "AWS_DEFAULT_REGION"
      value = var.aws_region
    }
    environment_variable {
      name  = "ECR_REPOSITORY_URI"
      value = aws_ecr_repository.a2p_repo.repository_url
    }
  }

  source {
    type = "CODEPIPELINE"
    buildspec = "buildspec.yml"
  }
}

# CodePipeline
resource "aws_codepipeline" "a2p_pipeline" {
  name     = "a2p-compliance-agent-pipeline"
  role_arn = aws_iam_role.codepipeline_role.arn

  artifact_store {
    location = aws_s3_bucket.pipeline_artifacts.bucket
    type     = "S3"
  }

  stage {
    name = "Source"
    action {
      name             = "Source"
      category         = "Source"
      owner            = "ThirdParty"
      provider         = "GitHub"
      version          = "1"
      output_artifacts = ["source_output"]

      configuration = {
        Owner      = var.github_owner
        Repo       = var.github_repo
        Branch     = var.github_branch
        OAuthToken = var.github_token
      }
    }
  }

  stage {
    name = "Build"
    action {
      name             = "Build"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      input_artifacts  = ["source_output"]
      output_artifacts = ["build_output"]
      version          = "1"

      configuration = {
        ProjectName = aws_codebuild_project.a2p_build.name
      }
    }
  }

  stage {
    name = "Deploy"
    action {
      name            = "Deploy"
      category        = "Deploy"
      owner           = "AWS"
      provider        = "ECS"
      input_artifacts = ["build_output"]
      version         = "1"

      configuration = {
        ClusterName = aws_ecs_cluster.a2p_cluster.name
        ServiceName = aws_ecs_service.a2p_service.name
      }
    }
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "a2p_cluster" {
  name = "a2p-compliance-cluster"
}

# ECS Task Definition
resource "aws_ecs_task_definition" "a2p_task" {
  family                   = "a2p-compliance-agent"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn           = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "a2p-compliance-agent"
      image = "${aws_ecr_repository.a2p_repo.repository_url}:latest"
      portMappings = [
        {
          containerPort = 5001
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "ADMIN_USER"
          value = "Admin"
        },
        {
          name  = "ADMIN_PASSWORD"
          value = "Maws@1234"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.a2p_logs.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

# ECS Service
resource "aws_ecs_service" "a2p_service" {
  name            = "a2p-compliance-service"
  cluster         = aws_ecs_cluster.a2p_cluster.id
  task_definition = aws_ecs_task_definition.a2p_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.subnet_ids
    security_groups = [aws_security_group.a2p_sg.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.a2p_tg.arn
    container_name   = "a2p-compliance-agent"
    container_port   = 5001
  }
}
