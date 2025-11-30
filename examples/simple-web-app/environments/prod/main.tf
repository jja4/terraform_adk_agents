module "vpc" {
  source = "../../modules/vpc"

  project_id     = var.project_id
  region         = var.region
  network_name   = var.network_name
  connector_cidr = "10.8.0.0/28"
}

module "cloud_sql" {
  source = "../../modules/cloud_sql"

  project_id    = var.project_id
  region        = var.region
  instance_name = var.db_instance_name
  database_name = var.database_name
  network_id    = module.vpc.network_id
  db_user       = var.db_user
  db_password   = var.db_password

  depends_on = [module.vpc]
}

resource "google_storage_bucket" "uploads" {
  name          = "${var.project_id}-uploads"
  location      = "US"
  project       = var.project_id
  force_destroy = true

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_service_account" "app" {
  account_id   = "web-app-sa"
  display_name = "Web Application Service Account"
  project      = var.project_id
}

resource "google_project_iam_member" "cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.app.email}"
}

resource "google_storage_bucket_iam_member" "object_admin" {
  bucket = google_storage_bucket.uploads.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.app.email}"
}

module "cloud_run" {
  source = "../../modules/cloud_run"

  project_id             = var.project_id
  region                 = var.region
  service_name           = var.service_name
  container_image        = var.container_image
  vpc_connector_id       = module.vpc.connector_id
  service_account_email  = google_service_account.app.email
  db_host                = module.cloud_sql.private_ip_address
  bucket_name            = google_storage_bucket.uploads.name

  depends_on = [
    module.vpc,
    module.cloud_sql,
    google_service_account.app
  ]
}
