"""
Requirements Extraction Agent Module
=====================================

This agent is the first in the sequential pipeline. It parses natural language
descriptions of infrastructure needs and extracts structured requirements.

ADK Features Demonstrated:
--------------------------
1. LlmAgent - Agent powered by an LLM (Gemini 2.5 Flash Lite)
2. Custom instruction prompt engineering for structured JSON output
3. Pure LLM reasoning without tools (tools=[])

Agent Role in Pipeline:
-----------------------
    User Input (Natural Language) -> [Requirements Agent] -> Requirements JSON
    
Example:
    Input:  "Create a web application with Cloud Run and PostgreSQL"
    Output: {
        "application_name": "web-app",
        "components": [
            {"type": "compute", "service": "cloud_run", ...},
            {"type": "database", "service": "cloud_sql", ...}
        ],
        "environment": "prod",
        ...
    }

Design Decisions:
-----------------
- Uses structured JSON output for reliable parsing
- Infers reasonable defaults for unspecified requirements
- Extracts both explicit and implicit infrastructure needs
- Validates output format with parse_requirements() function
"""

import json
from typing import Dict, Any
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types
import logging

logger = logging.getLogger(__name__)



def create_requirements_agent(retry_config: types.HttpRetryOptions) -> LlmAgent:
    """
    Create and configure the Requirements Extraction Agent.
    
    This function creates an LlmAgent specialized in parsing natural language
    infrastructure descriptions and extracting structured requirements.
    
    ADK Features Used:
    ------------------
    - LlmAgent: Core ADK agent class powered by an LLM
    - Gemini model: Uses Gemini 2.5 Flash Lite for fast, cost-effective inference
    - HttpRetryOptions: Automatic retry with exponential backoff for API resilience
    - Pure reasoning: No tools needed - agent uses LLM reasoning to parse text
    
    Agent Behavior:
    ---------------
    1. Receives natural language description (e.g., "Create a web app...")
    2. Parses text to identify infrastructure components
    3. Infers reasonable defaults for unspecified requirements
    4. Outputs structured JSON specification
    
    Prompt Engineering:
    -------------------
    The instruction prompt is carefully crafted to:
    - Enforce JSON-only output (no explanatory text)
    - Provide clear schema with examples
    - Guide the LLM to infer missing details
    - Ensure consistent output format
    
    Args:
        retry_config: HttpRetryOptions for API retry configuration
        
    Returns:
        Configured LlmAgent instance for requirements extraction
    
    Example:
        agent = create_requirements_agent(retry_config)
        # Agent will parse: "Create a web app with Cloud Run"
        # Into structured JSON with compute, networking requirements
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

**CRITICAL: You MUST output ONLY valid JSON in the exact format specified below. Do NOT output explanations or plans. Output the final JSON result immediately.**

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
    
    This function handles the extraction and validation of JSON from the
    LLM's response, which may include markdown code blocks or other formatting.
    
    JSON Extraction Strategy:
    -------------------------
    1. Check for ```json code blocks (preferred LLM output format)
    2. Check for generic ``` code blocks
    3. Fall back to raw text parsing
    
    Error Handling:
    ---------------
    If JSON parsing fails, raises ValueError with the first 500 characters
    of the response for debugging.
    
    Args:
        agent_response: The raw text response from the agent
        
    Returns:
        Parsed requirements dictionary with keys:
        - application_name: str
        - components: List[dict]
        - environment: str
        - regions: List[str]
        - estimated_scale: dict
        
    Raises:
        ValueError: If the response cannot be parsed as valid JSON
    """
    # Try to extract JSON from the response
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
        raise ValueError(f"Failed to parse requirements JSON: {e}\nResponse: {response[:500]}...")
