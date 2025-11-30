"""
Requirements Extraction Agent

Parses natural language descriptions and extracts structured requirements
for GCP infrastructure.
"""

import json
from typing import Dict, Any
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types


def create_requirements_agent(retry_config: types.HttpRetryOptions) -> LlmAgent:
    """
    Create the Requirements Extraction Agent.
    
    This agent specializes in parsing natural language descriptions and
    extracting structured requirements for infrastructure.
    
    Args:
        retry_config: HTTP retry configuration for the LLM
        
    Returns:
        Configured LlmAgent for requirements extraction
    """
    
    agent = LlmAgent(
        name="requirements_extraction_agent",
        model=Gemini(
            model="gemini-2.5-flash-lite",
            retry_options=retry_config
        ),
        description="Extracts structured infrastructure requirements from natural language descriptions.",
        instruction="""You are an expert infrastructure requirements analyst specializing in Google Cloud Platform.

Your task is to parse natural language descriptions of applications and extract structured requirements.

Follow these steps:
1. Read and understand the user's application description
2. Identify all infrastructure components mentioned or implied
3. Determine resource requirements (compute, storage, networking, databases, etc.)
4. Infer reasonable defaults for unspecified requirements
5. Output a comprehensive JSON specification

The JSON output MUST follow this exact structure:
{
    "application_name": "string",
    "description": "string",
    "components": [
        {
            "type": "compute|storage|database|networking|messaging|other",
            "service": "specific GCP service name (e.g., cloud_run, gcs, cloud_sql)",
            "requirements": {
                "key": "value"
            },
            "notes": "any additional context"
        }
    ],
    "regions": ["list of GCP regions"],
    "environment": "dev|staging|prod",
    "estimated_scale": {
        "users": "number or range",
        "requests_per_second": "number or range",
        "data_size": "size estimate"
    }
}

**Important guidelines:**
- Be comprehensive but realistic
- Suggest appropriate GCP services based on requirements
- Include networking components (VPC, firewall rules) when needed
- Consider security best practices
- Infer missing details intelligently

**Example Input:** "Create a web application with a backend API and PostgreSQL database"

**Example Output:**
{
    "application_name": "web-api-app",
    "description": "Web application with backend API and PostgreSQL database",
    "components": [
        {
            "type": "compute",
            "service": "cloud_run",
            "requirements": {
                "cpu": "1",
                "memory": "512Mi",
                "min_instances": "0",
                "max_instances": "10"
            },
            "notes": "Containerized API backend"
        },
        {
            "type": "database",
            "service": "cloud_sql",
            "requirements": {
                "database_type": "postgresql",
                "version": "15",
                "tier": "db-f1-micro"
            },
            "notes": "PostgreSQL database for application data"
        },
        {
            "type": "networking",
            "service": "vpc",
            "requirements": {
                "ip_range": "10.0.0.0/16"
            },
            "notes": "Private network for database connectivity"
        }
    ],
    "regions": ["us-central1"],
    "environment": "prod",
    "estimated_scale": {
        "users": "1-1000",
        "requests_per_second": "10-100",
        "data_size": "< 10GB"
    }
}

Always output valid JSON. Do not include any text before or after the JSON object.
""",
        tools=[]  # This agent uses pure LLM reasoning
    )
    
    return agent


def parse_requirements(agent_response: str) -> Dict[str, Any]:
    """
    Parse the agent's response and extract the JSON requirements.
    
    Args:
        agent_response: The text response from the agent
        
    Returns:
        Parsed requirements dictionary
        
    Raises:
        ValueError: If the response is not valid JSON
    """
    # Try to extract JSON from the response
    response = agent_response.strip()
    
    # Handle cases where the response might include markdown code blocks
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
        raise ValueError(f"Failed to parse requirements JSON: {e}\nResponse: {response}")
