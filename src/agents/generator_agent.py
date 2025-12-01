"""
Terraform Generator Agent Module
=================================

This agent is the third in the sequential pipeline. It receives architecture
specifications and generates complete, production-ready Terraform code.

ADK Features Demonstrated:
--------------------------
1. LlmAgent - Agent powered by an LLM (Gemini 2.5 Flash Lite)
2. Loop Agent Pattern - Participates in validation loop with Validator
3. Session Memory - Shares session with Validator for iterative improvement
4. Structured JSON output containing complete Terraform codebase

Agent Role in Pipeline:
-----------------------
    Architecture Spec -> [Generator Agent] <-> [Validator Agent] -> Validated Code
                              |________________feedback loop________________|

The Generator Agent acts as a senior Terraform developer, producing:
- Reusable modules in modules/ directory
- Environment-specific configurations in environments/ directory
- Provider configuration with version constraints
- Variable definitions with descriptions
- Output definitions for module interconnection

Session Memory Feature (Key Innovation):
----------------------------------------
The Generator and Validator share session_id="validation_loop", enabling:
- Generator remembers its previous code attempts
- Generator sees previous validation errors
- Each iteration builds on learned knowledge
- Avoids repeating the same mistakes

Output Structure:
-----------------
{
    "terraform_version": "1.5",
    "modules": [
        {
            "module_name": "vpc",
            "files": [{"filename": "main.tf", "content": "..."}]
        }
    ],
    "environments": {
        "prod": {"main_tf": "...", "variables_tf": "..."}
    }
}
"""

import json
from typing import Dict, Any
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types
import logging

logger = logging.getLogger(__name__)



def create_generator_agent(retry_config: types.HttpRetryOptions) -> LlmAgent:
    """
    Create and configure the Terraform Generator Agent.
    
    This function creates an LlmAgent that generates production-ready
    Terraform code from architecture specifications.
    
    ADK Features Used:
    ------------------
    - LlmAgent: Core ADK agent class for code generation
    - Gemini model: Uses Gemini 2.5 Flash Lite for fast generation
    - Loop pattern: Works with Validator in feedback loop
    - Session memory: Shares session with Validator (critical feature)
    
    Session Memory (Key Innovation):
    --------------------------------
    This agent participates in the validation loop with shared session:
    
        generator_runner.run_async(session_id=\"validation_loop\")
        validator_runner.run_async(session_id=\"validation_loop\")
    
    Benefits:
    - Remembers previous code attempts in conversation history
    - Sees previous validation errors and feedback
    - Learns from mistakes across iterations
    - Produces increasingly correct code
    
    Without session sharing, the Generator would have no memory of
    what it tried before, leading to repeated mistakes.
    
    Code Generation Responsibilities:
    ---------------------------------
    1. Generate complete Terraform modules (main.tf, variables.tf, outputs.tf)
    2. Create provider configurations with version constraints
    3. Define variables with descriptions and defaults
    4. Include proper resource dependencies
    5. Follow Terraform naming conventions (snake_case)
    6. Apply proper indentation and formatting
    
    Output Structure:
    -----------------
    - modules/: Reusable infrastructure components
    - environments/: Environment-specific configurations (dev/prod)
    - Each module: main.tf, variables.tf, outputs.tf
    - Each environment: main.tf, provider.tf, variables.tf, outputs.tf
    
    Args:
        retry_config: HttpRetryOptions for API retry configuration
        
    Returns:
        Configured LlmAgent instance for Terraform generation
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

**CRITICAL: You MUST output ONLY valid JSON in the exact format specified below. Do NOT output explanations, plans, or Terraform code directly. All Terraform code must be inside JSON strings.**

**Input:** You will receive a JSON architecture specification with modules and resources.

**Your responsibilities:**
1. Generate complete Terraform code for each module
2. Create provider configurations
3. Define variables and outputs
4. Include proper resource dependencies
5. Use Terraform best practices
6. Ensure code follows standard formatting conventions
7. Output structured JSON with all generated files (REQUIRED)

**Terraform Best Practices to Follow:**
1. **Naming Conventions**: Use lowercase with underscores (snake_case)
2. **Variables**: Define all configurable values as variables
3. **Outputs**: Export important resource attributes
4. **Dependencies**: Use depends_on for explicit dependencies
5. **Comments**: Add comments for complex configurations
6. **Labels**: Include labels for resource organization
7. **Modules**: Keep modules focused and reusable
8. **Versions**: Specify provider versions
9. **Formatting**: Use proper indentation (2 spaces) and spacing

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
        "<environment_name>": {
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
# environments/<environment_name>/provider.tf
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
1. **CRITICAL: Use the 'environment' value from the architecture/requirements (e.g., 'dev', 'staging', 'prod') as the key in the environments object**
2. Generate COMPLETE, WORKING Terraform code
3. Create REUSABLE modules in modules/ directory
4. Each module should be self-contained with main.tf, variables.tf, outputs.tf
5. Environment configuration in environments/<environment_name>/ calls the modules
6. Include ALL necessary resources (networking, IAM, etc.)
7. Use realistic default values
8. Format all code with terraform_fmt before outputting
9. Validate syntax with check_terraform_syntax
10. Output valid JSON

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

# environments/<environment_name>/variables.tf
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

# environments/<environment_name>/outputs.tf
output "service_url" {
  description = "Cloud Run service URL"
  value       = module.cloud_run.service_url
}
```

**Important Guidelines:**
1. Generate COMPLETE, WORKING Terraform code
2. Include ALL necessary resources (networking, IAM, etc.)
3. Use realistic default values
4. Output valid JSON immediately - NO tool usage, NO explanations

**CRITICAL: Just output the JSON structure. Do not use any tools.**
""",
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
    
    # Extract JSON from markdown code blocks anywhere in the response
    if '```json' in response:
        json_start = response.find('```json') + 7
        json_end = response.find('```', json_start)
        if json_end > json_start:
            response = response[json_start:json_end].strip()
    elif '```' in response:
        # Try generic code block
        json_start = response.find('```') + 3
        json_end = response.find('```', json_start)
        if json_end > json_start:
            potential_json = response[json_start:json_end].strip()
            # Check if it looks like JSON
            if potential_json.startswith('{') or potential_json.startswith('['):
                response = potential_json
    
    response = response.strip()
    
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        logger.error(f"⚠️  Initial JSON parsing failed at char {e.pos}: {e.msg}")
        logger.error(f"[DEBUG] Error context: ...{response[max(0, e.pos-50):e.pos+50]}...")
        
        # Try to fix common issues
        # 1. Missing comma between array/object elements
        if "Expecting ',' delimiter" in str(e):
            # Find the error position and try to add a comma
            pos = e.pos
            # Look backwards to find the end of the previous item
            if pos > 0 and response[pos-1] in ['}', ']', '"']:
                # Insert comma before the current position
                response = response[:pos] + ',' + response[pos:]
                logger.debug("[DEBUG] Attempted to add missing comma")
                try:
                    return json.loads(response)
                except:
                    pass
        
        # 2. Unterminated string - try to close it
        if "Unterminated string" in str(e):
            # Find unclosed strings and close the JSON
            if response.count('"') % 2 == 1:
                response = response.rstrip() + '"]}]}'
                logger.debug("[DEBUG] Attempted to close unterminated string")
                try:
                    return json.loads(response)
                except:
                    pass
        
        # If all fixes fail, raise with helpful context
        raise ValueError(
            f"Failed to parse generated Terraform JSON: {e}\n"
            f"Error at position {e.pos}: {e.msg}\n"
            f"Context: ...{response[max(0, e.pos-100):min(len(response), e.pos+100)]}...\n"
            f"First 500 chars: {response[:500]}"
        )
