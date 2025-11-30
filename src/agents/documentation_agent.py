"""
Documentation Agent

Creates comprehensive documentation for generated Terraform infrastructure.
Uses Pydantic models for structured output.
"""

import json
from typing import Dict, Any
from pydantic import ValidationError as PydanticValidationError
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types
from src.schemas import DocumentationOutput
import logging

logger = logging.getLogger(__name__)



def create_documentation_agent(retry_config: types.HttpRetryOptions) -> LlmAgent:
    """
    Create the Documentation Agent.
    
    This agent specializes in creating comprehensive documentation
    for Terraform infrastructure projects.
    
    Args:
        retry_config: HTTP retry configuration for the LLM
        
    Returns:
        Configured LlmAgent for documentation generation
    """
    
    agent = LlmAgent(
        name="documentation_agent",
        model=Gemini(
            model="gemini-2.5-flash-lite",
            retry_options=retry_config
        ),
        description="Creates comprehensive documentation including diagrams, README, and deployment guides.",
        instruction=r"""You are a technical writer for cloud infrastructure documentation.

Generate a complete README.md in markdown format for Terraform infrastructure.

Output ONLY the raw markdown content - NO JSON, NO code blocks, NO explanations.
Start directly with the markdown title.

Include these sections (keep brief):
1. # Title (infrastructure name)
2. ## Overview (2-3 sentences)
3. ## Architecture (bullet list of modules/services)
4. ## Prerequisites (Terraform, GCP CLI, permissions)
5. ## Deployment Steps (terraform init, plan, apply)
6. ## Configuration (mention key variables and terraform.tfvars)
7. ## Variables (list 3-5 key variables)

Keep the entire README under 500 words.
Output ONLY markdown - start with # title.""",
        tools=[]  # Pure LLM reasoning for documentation
    )
    
    return agent


def parse_documentation(agent_response: str) -> DocumentationOutput:
    """
    Parse documentation from agent response.
    
    Args:
        agent_response: Raw markdown response from documentation agent
        
    Returns:
        Validated DocumentationOutput object
    """
    response = agent_response.strip()
    
    logger.debug(f"\n[DEBUG] Raw response length: {len(response)} chars")
    logger.debug(f"[DEBUG] First 200 chars: {response[:200]}")
    
    # Remove any markdown code blocks if present
    if '```markdown' in response:
        start = response.find('```markdown') + 11
        end = response.find('```', start)
        if end > start:
            response = response[start:end].strip()
            logger.debug(f"[DEBUG] Extracted from markdown block")
    elif response.startswith('```') and '```' in response[3:]:
        # Generic code block
        start = response.find('```') + 3
        end = response.rfind('```')
        if end > start:
            response = response[start:end].strip()
            logger.debug(f"[DEBUG] Extracted from code block")
    
    # Clean up the response
    response = response.strip()
    
    # Validate it looks like markdown (starts with # or has markdown headers)
    if not response.startswith('#') and '\n#' not in response:
        logger.warning(f"⚠️  Response doesn't look like markdown, adding header")
        response = "# Infrastructure Documentation\n\n" + response
    
    # Create DocumentationOutput with the markdown content
    doc = DocumentationOutput(readme=response)
    logger.info(f"✅ Documentation parsed successfully ({len(doc.readme)} chars in README)")
    return doc


def save_documentation_to_files(
    documentation: DocumentationOutput,
    output_dir: str
) -> Dict[str, str]:
    """
    Save documentation to actual files.
    
    Args:
        documentation: Validated DocumentationOutput object
        output_dir: Directory to save files
        
    Returns:
        Dictionary mapping file types to file paths
    """
    import os
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    saved_files = {}
    
    # Save README
    readme_path = os.path.join(output_dir, "README.md")
    with open(readme_path, 'w') as f:
        f.write(documentation.readme)
    saved_files["readme"] = readme_path
    
    # Save optional deployment guide if provided separately
    if documentation.deployment_guide:
        deploy_path = os.path.join(output_dir, "DEPLOYMENT.md")
        with open(deploy_path, 'w') as f:
            f.write(documentation.deployment_guide)
        saved_files["deployment_guide"] = deploy_path
    
    # Save optional files if they exist
    if documentation.security_guide:
        security_path = os.path.join(output_dir, "SECURITY.md")
        with open(security_path, 'w') as f:
            f.write(documentation.security_guide)
        saved_files["security_guide"] = security_path
    
    if documentation.troubleshooting:
        troubleshoot_path = os.path.join(output_dir, "TROUBLESHOOTING.md")
        with open(troubleshoot_path, 'w') as f:
            f.write(documentation.troubleshooting)
        saved_files["troubleshooting"] = troubleshoot_path
    
    if documentation.architecture_diagram:
        diagram_path = os.path.join(output_dir, "architecture.mmd")
        with open(diagram_path, 'w') as f:
            f.write(documentation.architecture_diagram)
        saved_files["diagram"] = diagram_path
    
    return saved_files
