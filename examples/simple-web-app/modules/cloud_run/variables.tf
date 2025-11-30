variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
}

variable "container_image" {
  description = "Container image to deploy"
  type        = string
}

variable "vpc_connector_id" {
  description = "ID of the VPC connector"
  type        = string
}

variable "service_account_email" {
  description = "Service account email for the Cloud Run service"
  type        = string
}

variable "db_host" {
  description = "Database host connection string"
  type        = string
}

variable "bucket_name" {
  description = "Storage bucket name"
  type        = string
}
