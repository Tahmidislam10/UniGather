# --- Execution Role (Used by ECS to pull images and send logs) ---
resource "aws_iam_role" "ecs_exec" {
  name = "${var.app_name}-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_exec_attach" {
  role       = aws_iam_role.ecs_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# --- Task Role (Used by your Flask code to talk to AWS services) ---
resource "aws_iam_role" "ecs_task" {
  name = "${var.app_name}-task"

  assume_role_policy = aws_iam_role.ecs_exec.assume_role_policy
}

# Policy allowing the app to read/write to DynamoDB 
resource "aws_iam_role_policy" "dynamodb_access" {
  name = "${var.app_name}-dynamo-policy"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Effect   = "Allow"
        Resource = "*" # Allows access to all tables in the account
      }
    ]
  })
}