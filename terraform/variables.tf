variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-2"
}

variable "project_name" {
  description = "Name prefix for all resources"
  type        = string
  default     = "task-manager"
}

variable "ami_id" {
  description = "Ubuntu 22.04 LTS AMI for ap-southeast-2"
  type        = string
  default     = "ami-0310483fb2b488153"
}

variable "ssh_public_key" {
  description = "Your public SSH key contents"
  type        = string
}