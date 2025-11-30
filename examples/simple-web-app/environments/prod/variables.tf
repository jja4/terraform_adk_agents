variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "network_name" {
  description = "Name of the VPC network"
  type        = string
  default     = "web-app-network"
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
  default     = "web-api-service"
}

variable "container_image" {
  description = "Container image to deploy"
  type        = string
  default     = "gcr.io/cloudrun/hello"
}

variable "db_instance_name" {
  description = "Name of the Cloud SQL instance"
  type        = string
  default     = "web-app-db"
}

variable "database_name" {
  description = "Name of the database"
  type        = string
  default     = "appdb"
}

variable "db_user" {
  description = "Database username"
  type        = string
  default     = "appuser"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}
