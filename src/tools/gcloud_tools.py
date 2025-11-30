"""
GCloud CLI Tools

Tools for interacting with Google Cloud services via gcloud CLI.
"""

import subprocess
import json
from typing import Dict, List, Optional


def check_gcp_service_availability(service_name: str, region: str = "us-central1") -> Dict:
    """
    Check if a GCP service is available in the specified region.
    
    Args:
        service_name: Name of the GCP service (e.g., "run", "sql", "storage")
        region: GCP region to check (default: "us-central1")
        
    Returns:
        Dictionary with status and availability information
    """
    # Map common service names to gcloud service names
    service_map = {
        "cloud_run": "run.googleapis.com",
        "cloud_sql": "sql-component.googleapis.com",
        "gcs": "storage-component.googleapis.com",
        "compute": "compute.googleapis.com",
        "gke": "container.googleapis.com",
        "vpc": "compute.googleapis.com",
    }
    
    api_name = service_map.get(service_name, f"{service_name}.googleapis.com")
    
    try:
        # Check if service is enabled (this would require actual gcloud access)
        # For demo purposes, we return success for all common services
        # In production, you'd run: gcloud services list --enabled --filter=name:api_name
        
        # Always return available for demo purposes
        is_available = True
        
        return {
            "status": "success",
            "service": service_name,
            "api_name": api_name,
            "region": region,
            "available": is_available,
            "message": f"Service {service_name} is available in {region}"
        }
    except Exception as e:
        return {
            "status": "error",
            "service": service_name,
            "error_message": str(e)
        }


def list_available_regions(service_type: str = "compute") -> Dict:
    """
    List available GCP regions for a given service type.
    
    Args:
        service_type: Type of service (e.g., "compute", "run", "sql")
        
    Returns:
        Dictionary with status and list of regions
    """
    # Mock data - in production, would call: gcloud compute regions list
    regions_by_service = {
        "compute": [
            "us-central1", "us-east1", "us-west1", "us-west2",
            "europe-west1", "europe-west2", "asia-east1", "asia-southeast1"
        ],
        "run": [
            "us-central1", "us-east1", "us-west1",
            "europe-west1", "asia-east1"
        ],
        "sql": [
            "us-central1", "us-east1", "us-west1",
            "europe-west1", "asia-east1"
        ]
    }
    
    regions = regions_by_service.get(service_type, regions_by_service["compute"])
    
    return {
        "status": "success",
        "service_type": service_type,
        "regions": regions,
        "count": len(regions)
    }


def validate_service_compatibility(primary_service: str, secondary_service: str) -> Dict:
    """
    Check if two GCP services can work together (e.g., Cloud Run + Cloud SQL).
    
    Args:
        primary_service: First service name
        secondary_service: Second service name
        
    Returns:
        Dictionary with compatibility information
    """
    # Define compatibility rules
    compatibility_rules = {
        ("cloud_run", "cloud_sql"): {
            "compatible": True,
            "notes": "Cloud Run can connect to Cloud SQL via private IP or Cloud SQL Proxy",
            "requirements": ["VPC connector", "Cloud SQL private IP"]
        },
        ("cloud_run", "gcs"): {
            "compatible": True,
            "notes": "Cloud Run can access GCS using service account authentication",
            "requirements": ["IAM permissions"]
        },
        ("gke", "cloud_sql"): {
            "compatible": True,
            "notes": "GKE can connect to Cloud SQL via Cloud SQL Proxy sidecar",
            "requirements": ["Cloud SQL Proxy", "Workload Identity"]
        },
        ("gke", "gcs"): {
            "compatible": True,
            "notes": "GKE can access GCS via Workload Identity or service account keys",
            "requirements": ["Workload Identity or service account"]
        }
    }
    
    # Check both orders
    key1 = (primary_service, secondary_service)
    key2 = (secondary_service, primary_service)
    
    compatibility = compatibility_rules.get(key1) or compatibility_rules.get(key2)
    
    if compatibility:
        return {
            "status": "success",
            "compatible": compatibility["compatible"],
            "notes": compatibility["notes"],
            "requirements": compatibility["requirements"]
        }
    else:
        return {
            "status": "success",
            "compatible": True,  # Assume compatible unless explicitly incompatible
            "notes": "No specific compatibility issues identified",
            "requirements": []
        }
