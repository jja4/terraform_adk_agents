resource "google_compute_network" "vpc" {
  name                    = var.network_name
  auto_create_subnetworks = false
  project                 = var.project_id
}

resource "google_vpc_access_connector" "connector" {
  name          = "${var.network_name}-connector"
  region        = var.region
  network       = google_compute_network.vpc.name
  ip_cidr_range = var.connector_cidr
  
  machine_type = "e2-micro"
  min_instances = 2
  max_instances = 3
}
