output "network_id" {
  description = "The ID of the VPC network"
  value       = google_compute_network.vpc.id
}

output "network_name" {
  description = "The name of the VPC network"
  value       = google_compute_network.vpc.name
}

output "connector_id" {
  description = "The ID of the VPC connector"
  value       = google_vpc_access_connector.connector.id
}
