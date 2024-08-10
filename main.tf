terraform {
  cloud {
    organization = "kanasva"
    workspaces {
      name = "ai-chest-xray-diagnosis-api"
    }
  }
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.36"
    }
  }
}

provider "aws" {
  region = "ap-southeast-2"
}

locals {
  project_name = "ai-chest-xray-diagnosis-api"
}

variable "image_uri" {
  description = "URI of the Docker image for the Lambda function"
  type        = string
  default     = "dummy"
}


### Start Lambda ###
resource "aws_iam_role" "lambda_exec" {
  name = local.project_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Sid    = ""
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      }
    ]
  })
}

# for lambda to create log
resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_cloudwatch_log_group" "lambda_log" {
  name = "/aws/lambda/${aws_lambda_function.lambda_function.function_name}"
  retention_in_days = 7
}

resource "aws_lambda_function" "lambda_function" {
  function_name = local.project_name
  role          = aws_iam_role.lambda_exec.arn
  timeout       = 60
  image_uri     = var.image_uri
  package_type  = "Image"
  architectures = ["arm64"]
  memory_size   = 1600
}
### End Lambda ###


## Start ECR ###
resource "aws_ecr_repository" "ecr" {
  name                 = "chest-xray-prediction"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "ecr_lifecycle" {
  repository = aws_ecr_repository.ecr.name

  policy = <<EOF
{
    "rules": [
        {
            "rulePriority": 1,
            "description": "Keep last 3 images",
            "selection": {
                "tagStatus": "any",
                "countType": "imageCountMoreThan",
                "countNumber": 2
            },
            "action": {
                "type": "expire"
            }
        }
    ]
}
EOF
}
## END ECR ###



output "function_name" {
  description = "Name of the Lambda function."
  value       = aws_lambda_function.lambda_function.function_name
}