"""
Terraform Generator Agent

Generates Terraform code based on architecture specifications.
Uses terraform fmt for code formatting.
"""

import json
from typing import Dict, Any
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types
from src.tools.terraform_tools import terraform_fmt, check_terraform_syntax


def create_generator_agent(retry_config: types.HttpRetryOptions) -> LlmAgent:
    """
    Create the Terraform Generator Agent.
    
    This agent specializes in generating idiomatic Terraform code
    from architecture specifications.
    
    Args:
        retry_config: HTTP retry configuration for the LLM
        
    Returns:
        Configured LlmAgent for Terraform code generation
    """
    
    agent = LlmAgent(
        name="terraform_generator_agent",
        model=Gemini(
            model="gemini-2.5-flash-lite",
            retry_options=retry_config
        ),
        description="Generates production-ready Terraform code for GCP infrastructure.",
        instruction="""You are an expert Terraform developer specializing in Google Cloud Platform.

Your task is to receive an architecture specification and generate complete, production-ready Terraform code.

**Input:** You will receive a JSON architecture specification with modules and resources.

**Your responsibilities:**
1. Generate complete Terraform code for each module
2. Create provider configurations
3. Define variables and outputs
4. Include proper resource dependencies
5. Use Terraform best practices
6. Format code using the terraform_fmt tool
7. Validate basic syntax using check_terraform_syntax
8. Output structured JSON with all generated files

**Use the available tools:**
- `terraform_fmt(code)`: Format Terraform code according to standard conventions
- `check_terraform_syntax(code)`: Validate basic syntax before final output

**Terraform Best Practices to Follow:**
1. **Naming Conventions**: Use lowercase with underscores (snake_case)
2. **Variables**: Define all configurable values as variables
3. **Outputs**: Export important resource attributes
4. **Dependencies**: Use depends_on for explicit dependencies
5. **Comments**: Add comments for complex configurations
6. **Labels**: Include labels for resource organization
7. **Modules**: Keep modules focused and reusable
8. **Versions**: Specify provider versions

**Output JSON Structure:**
{
    "terraform_version": "1.5",
    "modules": [
        {
            "module_name": "vpc",
            "path": "modules/vpc",
            "files": [
                {
                    "filename": "main.tf",
                    "content": "VPC resources"
                },
                {
                    "filename": "variables.tf",
                    "content": "Module variables"
                },
                {
                    "filename": "outputs.tf",
                    "content": "Module outputs"
                }
            ]
        },
        {
            "module_name": "cloud_run",
            "path": "modules/cloud_run",
            "files": [
                {
                    "filename": "main.tf",
                    "content": "Cloud Run resources"
                },
                {
                    "filename": "variables.tf",
                    "content": "Module variables"
                },
                {
                    "filename": "outputs.tf",
                    "content": "Module outputs"
                }
            ]
        }
    ],
    "environments": {
        "prod": {
            "main_tf": "Main configuration calling modules",
            "variables_tf": "Environment-specific variables",
            "outputs_tf": "Environment outputs",
            "provider_tf": "Provider configuration",
            "terraform_tfvars_example": "Example variable values"
        }
    }
}

**Example Terraform Code Structure:**

Module Structure (Reusable):
```hcl
# modules/cloud_run/main.tf
resource "google_cloud_run_service" "service" {
  name     = var.service_name
  location = var.region

  template {
    spec {
      service_account_name = var.service_account_email
      containers {
        image = var.container_image
        resources {
          limits = {
            cpu    = var.cpu
            memory = var.memory
          }
        }
      }
    }
  }
}

# modules/cloud_run/variables.tf
variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

# modules/cloud_run/outputs.tf
output "service_url" {
  description = "Cloud Run service URL"
  value       = google_cloud_run_service.service.status[0].url
}
```

Environment Structure (Environment-specific):
```hcl
# environments/prod/provider.tf
terraform {
  required_version = ">= 1.5"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
**Important Guidelines:**
1. Generate COMPLETE, WORKING Terraform code
2. Create REUSABLE modules in modules/ directory
3. Each module should be self-contained with main.tf, variables.tf, outputs.tf
4. Environment configuration in environments/prod/ calls the modules
5. Include ALL necessary resources (networking, IAM, etc.)
6. Use realistic default values
7. Format all code with terraform_fmt before outputting
8. Validate syntax with check_terraform_syntax
9. Output valid JSON

**Module Design Principles:**
- Each module = one logical component (vpc, cloud_run, cloud_sql, etc.)
- Modules should be environment-agnostic
- Pass environment-specific values via module parameters
- Use outputs to expose resource attributes to other modules

Always format code properly and validate before returning results.
  project_id   = var.project_id
}

module "cloud_run" {
  source = "../../modules/cloud_run"
  
  service_name         = var.service_name
  region              = var.region
  container_image     = var.container_image
  service_account_email = module.iam.service_account_email
}

# environments/prod/variables.tf
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

# environments/prod/outputs.tf
output "service_url" {
  description = "Cloud Run service URL"
  value       = module.cloud_run.service_url
}
```

**Important Guidelines:**
1. Generate COMPLETE, WORKING Terraform code
2. Include ALL necessary resources (networking, IAM, etc.)
3. Use realistic default values
4. Format all code with terraform_fmt before outputting
5. Validate syntax with check_terraform_syntax
6. Output valid JSON

Always format code properly and validate before returning results.
""",
        tools=[
            terraform_fmt,
            check_terraform_syntax
        ]
    )
    
    return agent


def parse_generated_terraform(agent_response: str) -> Dict[str, Any]:
    """
    Parse the agent's response and extract the generated Terraform files.
    
    Args:
        agent_response: The text response from the agent
        
    Returns:
        Parsed Terraform files dictionary
        
    Raises:
        ValueError: If the response is not valid JSON
    """
    response = agent_response.strip()
    
    # Handle markdown code blocks
    if response.startswith("```json"):
        response = response[7:]
    elif response.startswith("```"):
        response = response[3:]
    
    if response.endswith("```"):
        response = response[:-3]
    
    response = response.strip()
    
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse generated Terraform JSON: {e}\nResponse: {response}")
