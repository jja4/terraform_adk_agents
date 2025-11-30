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

CRITICAL: Output ONLY valid JSON matching this schema:
{
  "readme": "string (REQUIRED - complete README.md markdown)"
}

The README must include ALL sections:
- Title and overview
- Architecture description
- Prerequisites
- Deployment steps (terraform init, plan, apply)
- Configuration guide
- Usage examples
- Security notes
- Troubleshooting tips

Rules:
- Output ONLY a JSON object with a "readme" field
- Use proper markdown formatting in the readme string
- Keep it comprehensive but under 2000 words
- Properly escape quotes, newlines, and special characters in JSON
- Wrap output in ```json code block

Example output:
```json
{
  "readme": "# Infrastructure Name\\n\\n## Overview\\n...\\n## Deployment\\n..."
}
```

Now generate the documentation.""",
        tools=[]  # Pure LLM reasoning for documentation
    )
    
    return agent


def parse_documentation(agent_response: str) -> DocumentationOutput:
    """
    Parse documentation from agent response using Pydantic validation.
    
    Args:
        agent_response: Raw response from documentation agent
        
    Returns:
        Validated DocumentationOutput object
        
    Raises:
        ValueError: If the response cannot be parsed or validated
    """
    response = agent_response.strip()
    
    print(f"\n[DEBUG] Raw response length: {len(response)} chars")
    print(f"[DEBUG] First 300 chars: {response[:300]}")
    
    # Extract JSON from markdown code blocks - find the LAST closing backticks
    # to avoid stopping at code blocks inside the JSON
    if '```json' in response:
        json_start = response.find('```json') + 7
        # Find the last occurrence of ``` to get the closing delimiter
        json_end = response.rfind('```')
        if json_end > json_start:
            response = response[json_start:json_end].strip()
            print(f"[DEBUG] Extracted from ```json block: {len(response)} chars")
    elif '```' in response:
        json_start = response.find('```') + 3
        # Find the last occurrence of ``` to get the closing delimiter
        json_end = response.rfind('```')
        if json_end > json_start:
            potential_json = response[json_start:json_end].strip()
            if potential_json.startswith('{') or potential_json.startswith('['):
                response = potential_json
                print(f"[DEBUG] Extracted from ``` block: {len(response)} chars")
    
    response = response.strip()
    
    # Debug: Show first 200 chars and last 100 chars of what we're trying to parse
    print(f"[DEBUG] Final JSON to parse - Length: {len(response)} chars")
    print(f"[DEBUG] First 200 chars: {response[:200]}...")
    print(f"[DEBUG] Last 100 chars: ...{response[-100:]}")
    
    try:
        # Parse JSON - this will handle escaped strings correctly
        data = json.loads(response)
        # Validate with Pydantic
        doc = DocumentationOutput(**data)
        print(f"✅ Documentation parsed successfully ({len(doc.readme)} chars in README)")
        return doc
    except json.JSONDecodeError as e:
        # Fallback: create minimal documentation
        print(f"❌ JSON parsing failed: {str(e)}")
        print(f"   Attempted to parse: {response[:300]}...")
        return DocumentationOutput(
            readme=f"# Infrastructure Documentation\n\n*Error generating full documentation*\n\nParse error: {str(e)[:200]}\n\nPlease re-run the generator for complete documentation."
        )
    except PydanticValidationError as e:
        # Schema validation failed
        print(f"❌ Pydantic validation failed: {str(e)}")
        return DocumentationOutput(
            readme=f"# Infrastructure Documentation\n\n*Error validating documentation schema*\n\nValidation error: {str(e)[:200]}\n\nPlease re-run the generator for complete documentation."
        )


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
