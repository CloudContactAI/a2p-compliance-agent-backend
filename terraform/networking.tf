# Security Group for ECS
resource "aws_security_group" "a2p_sg" {
  name_prefix = "a2p-compliance-sg"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5001
    to_port     = 5001
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "a2p-compliance-sg"
  }
}

# Application Load Balancer
resource "aws_lb" "a2p_alb" {
  name               = "a2p-compliance-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets           = var.subnet_ids

  tags = {
    Name = "a2p-compliance-alb"
  }
}

# ALB Security Group
resource "aws_security_group" "alb_sg" {
  name_prefix = "a2p-alb-sg"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "a2p-alb-sg"
  }
}

# Target Group
resource "aws_lb_target_group" "a2p_tg" {
  name        = "a2p-compliance-tg"
  port        = 5001
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/api/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name = "a2p-compliance-tg"
  }
}

# ALB Listener
resource "aws_lb_listener" "a2p_listener" {
  load_balancer_arn = aws_lb.a2p_alb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.a2p_tg.arn
  }
}
