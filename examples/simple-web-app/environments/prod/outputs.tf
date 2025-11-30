output "service_url" {
  description = "URL of the deployed Cloud Run service"
  value       = module.cloud_run.service_url
}

output "database_connection" {
  description = "Cloud SQL instance connection name"
  value       = module.cloud_sql.instance_connection_name
}

output "storage_bucket" {
  description = "Storage bucket name for uploads"
  value       = google_storage_bucket.uploads.name
}

output "network_name" {
  description = "VPC network name"
  value       = module.vpc.network_name
}
