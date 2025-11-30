"""
Architecture Design Agent

Designs GCP infrastructure architecture based on requirements.
Uses gcloud tools to validate service compatibility.
"""

import json
from typing import Dict, Any
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types
from src.tools.gcloud_tools import (
    check_gcp_service_availability,
    list_available_regions,
    validate_service_compatibility
)


def create_architecture_agent(retry_config: types.HttpRetryOptions) -> LlmAgent:
    """
    Create the Architecture Design Agent.
    
    This agent specializes in designing GCP infrastructure architecture
    and determining the optimal module structure for Terraform.
    
    Args:
        retry_config: HTTP retry configuration for the LLM
        
    Returns:
        Configured LlmAgent for architecture design
    """
    
    agent = LlmAgent(
        name="architecture_design_agent",
        model=Gemini(
            model="gemini-2.5-flash-lite",
            retry_options=retry_config
        ),
        description="Designs GCP infrastructure architecture and Terraform module structure.",
        instruction="""You are a senior cloud architect specializing in Google Cloud Platform and Terraform best practices.

Your task is to receive infrastructure requirements and design a comprehensive architecture with Terraform module structure.

**CRITICAL: You MUST output ONLY valid JSON in the exact format specified below. Do NOT output explanations or plans. After using any tools, output the final JSON result immediately.**

**Input:** You will receive a JSON requirements specification.

**Your responsibilities:**
1. Validate service compatibility using the check_gcp_service_availability and validate_service_compatibility tools
2. Design the overall architecture topology
3. Determine Terraform module structure
4. Define resource dependencies
5. Plan network architecture
6. Consider security and IAM requirements
7. Output a detailed architecture plan in JSON format

**Use the available tools:**
- `check_gcp_service_availability(service_name, region)`: Check if a service is available in a region
- `list_available_regions(service_type)`: Get list of available regions for a service
- `validate_service_compatibility(primary_service, secondary_service)`: Check if two services work together

**Output JSON structure:**
{
    "architecture_name": "string",
    "description": "string",
    "modules": [
        {
            "module_name": "string",
            "purpose": "string",
            "resources": [
                {
                    "type": "terraform resource type (e.g., google_cloud_run_service)",
                    "name": "resource name",
                    "properties": {
                        "key": "value"
                    }
                }
            ],
            "outputs": ["list of outputs"],
            "dependencies": ["list of module dependencies"]
        }
    ],
    "networking": {
        "vpc_required": true/false,
        "vpc_name": "string",
        "subnets": [],
        "firewall_rules": []
    },
    "iam": {
        "service_accounts": [],
        "roles": []
    },
    "deployment_order": ["ordered list of modules to deploy"]
}

**Best practices to follow:**
- Separate concerns into different modules (networking, compute, data, iam)
- Use module outputs as inputs to other modules
- Include proper dependencies
- Consider security: use private IPs, minimal IAM permissions
- Include monitoring and logging where appropriate
- Use regional resources for high availability

Always output valid JSON immediately. Assume all GCP services are available.

**CRITICAL: Just analyze requirements and output JSON. Do not use any tools.**
"""
    )
    
    return agent


def parse_architecture(agent_response: str) -> Dict[str, Any]:
    """
    Parse the agent's response and extract the architecture JSON.
    
    Args:
        agent_response: The text response from the agent
        
    Returns:
        Parsed architecture dictionary
        
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
        json_start = response.find('```') + 3
        json_end = response.find('```', json_start)
        if json_end > json_start:
            potential_json = response[json_start:json_end].strip()
            if potential_json.startswith('{') or potential_json.startswith('['):
                response = potential_json
    
    response = response.strip()
    
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse architecture JSON: {e}\nResponse: {response[:500]}...")
