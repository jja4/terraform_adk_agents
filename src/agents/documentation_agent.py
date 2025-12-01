"""
Documentation Agent Module
===========================

This agent is the fifth and final in the sequential pipeline. It receives
validated Terraform code and generates comprehensive documentation.

ADK Features Demonstrated:
--------------------------
1. LlmAgent - Agent powered by an LLM (Gemini 2.5 Flash Lite)
2. Sequential agent pattern - receives output from Validator
3. Structured output with DocumentationOutput Pydantic model

Agent Role in Pipeline:
-----------------------
    Validated Terraform -> [Documentation Agent] -> README.md + Guides
    
The Documentation Agent acts as a technical writer, producing:
- README.md with architecture overview
- Deployment instructions
- Configuration guide
- Variable documentation

Output Structure:
-----------------
DocumentationOutput:
- readme: Complete README.md content (required)
- deployment_guide: Optional separate deployment doc
- architecture_diagram: Optional Mermaid diagram
- security_guide: Optional security best practices
- troubleshooting: Optional troubleshooting guide

Design Decisions:
-----------------
- Outputs raw markdown (no JSON wrapping)
- Keeps README concise (< 500 words)
- Includes essential sections: Overview, Architecture, Prerequisites, Deployment
- Uses pure LLM reasoning (no external tools)
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
    Create and configure the Documentation Agent.
    
    This function creates an LlmAgent specialized in generating comprehensive
    documentation for Terraform infrastructure projects.
    
    ADK Features Used:
    ------------------
    - LlmAgent: Core ADK agent class for documentation generation
    - Gemini model: Uses Gemini 2.5 Flash Lite for fast generation
    - Pure reasoning: No tools needed (tools=[])
    
    Documentation Responsibilities:
    -------------------------------
    1. Generate README.md with architecture overview
    2. Create deployment instructions (terraform init, plan, apply)
    3. Document prerequisites (Terraform, GCP CLI, permissions)
    4. List key configuration variables
    5. Provide brief troubleshooting guidance
    
    Output Format:
    --------------
    The agent outputs raw markdown content (no JSON wrapping).
    This simplifies parsing and allows direct file writing.
    
    Content Guidelines:
    -------------------
    - README under 500 words for readability
    - Essential sections: Overview, Architecture, Prerequisites, Deployment
    - Practical focus: what users need to deploy
    - Clear variable documentation
    
    Args:
        retry_config: HttpRetryOptions for API retry configuration
        
    Returns:
        Configured LlmAgent instance for documentation generation
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
    
    This function handles the extraction of markdown content from the
    agent's response, which should be raw markdown (not JSON).
    
    Parsing Strategy:
    -----------------
    1. Strip whitespace and code block markers
    2. Extract content from ```markdown blocks if present
    3. Validate content starts with # (markdown header)
    4. Add default header if missing
    
    Unlike other agents that output JSON, the Documentation Agent
    outputs raw markdown for easier file writing.
    
    Args:
        agent_response: Raw markdown response from documentation agent
        
    Returns:
        DocumentationOutput with readme field containing markdown
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
    Save documentation to actual files in the output directory.
    
    This function writes the generated documentation to disk, creating
    the output directory if needed and saving each documentation file.
    
    File Mapping:
    -------------
    - readme -> README.md (always saved)
    - deployment_guide -> DEPLOYMENT.md (optional)
    - security_guide -> SECURITY.md (optional)
    - troubleshooting -> TROUBLESHOOTING.md (optional)
    - architecture_diagram -> architecture.mmd (optional, Mermaid format)
    
    Args:
        documentation: DocumentationOutput with generated content
        output_dir: Directory path to save files
        
    Returns:
        Dictionary mapping file types to their saved file paths
        Example: {"readme": "/output/README.md", ...}
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
