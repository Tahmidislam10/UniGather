output "ecr_repo" {
  value = aws_ecr_repository.app.repository_url
}
