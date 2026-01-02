variable "app_name" {
  default = "g13-web-app"
}


variable "vpc_cidr" {
  default = "10.0.0.0/16"
}


variable "image_tag" {
  description = "Docker image tag deployed to ECS"
}

variable "domain_name" {
  description = "The custom domain bought on Cloudflare"
  default     = "younesblog.org"
}