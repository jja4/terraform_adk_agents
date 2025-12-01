"""
Architecture Design Agent Module
=================================

This agent is the second in the sequential pipeline. It receives structured
requirements and designs the optimal GCP infrastructure architecture.

ADK Features Demonstrated:
--------------------------
1. LlmAgent - Agent powered by an LLM (Gemini 2.5 Flash Lite)
2. Sequential agent pattern - receives output from Requirements Agent
3. Structured JSON output for reliable inter-agent communication

Agent Role in Pipeline:
-----------------------
    Requirements JSON -> [Architecture Agent] -> Architecture Specification
    
The Architecture Agent acts as a cloud architect, making decisions about:
- Which GCP services to use for each requirement
- How services should interconnect
- Terraform module structure and organization
- Resource dependencies and deployment order
- Security considerations (VPCs, IAM, private networking)

Example Output Structure:
-------------------------
{
    "architecture_name": "web-api-infrastructure",
    "modules": [
        {"module_name": "vpc", "purpose": "Network infrastructure", ...},
        {"module_name": "cloud_run", "purpose": "API backend", ...}
    ],
    "deployment_order": ["vpc", "iam", "cloud_sql", "cloud_run"]
}

Design Decisions:
-----------------
- Separates infrastructure into reusable Terraform modules
- Considers security best practices (private IPs, minimal IAM)
- Outputs deployment order based on resource dependencies
- Uses pure LLM reasoning (no external tools)
"""

import json
from typing import Dict, Any
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types
import logging
logger = logging.getLogger(__name__)


def create_architecture_agent(retry_config: types.HttpRetryOptions) -> LlmAgent:
    """
    Create and configure the Architecture Design Agent.
    
    This function creates an LlmAgent that acts as a senior cloud architect,
    designing optimal GCP infrastructure from requirements specifications.
    
    ADK Features Used:
    ------------------
    - LlmAgent: Core ADK agent class for LLM-powered reasoning
    - Gemini model: Uses Gemini 2.5 Flash Lite for fast inference
    - Sequential pattern: Receives output from Requirements Agent
    - Structured output: Produces JSON architecture specification
    
    Agent Responsibilities:
    -----------------------
    1. Analyze requirements to identify optimal GCP services
    2. Design module structure for reusable Terraform code
    3. Define resource dependencies and deployment order
    4. Consider networking (VPC, subnets, firewall rules)
    5. Plan IAM (service accounts, roles, permissions)
    
    Best Practices Applied:
    -----------------------
    - Separate concerns into distinct modules (vpc, compute, data)
    - Use module outputs as inputs to dependent modules
    - Include proper resource dependencies
    - Consider security: private IPs, minimal IAM permissions
    - Plan for high availability where appropriate
    
    Args:
        retry_config: HttpRetryOptions for API retry configuration
        
    Returns:
        Configured LlmAgent instance for architecture design
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
1. Design the overall architecture topology
2. Determine Terraform module structure
3. Define resource dependencies
4. Plan network architecture
5. Consider security and IAM requirements
6. Output a detailed architecture plan in JSON format

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

Always output valid JSON immediately. Assume all GCP services are available and compatible.
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
