output "instance_connection_name" {
  description = "Connection name for Cloud SQL instance"
  value       = google_sql_database_instance.main.connection_name
}

output "database_name" {
  description = "Name of the database"
  value       = google_sql_database.database.name
}

output "private_ip_address" {
  description = "Private IP address of the instance"
  value       = google_sql_database_instance.main.private_ip_address
}
