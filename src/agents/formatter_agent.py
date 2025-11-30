"""
Formatter Agent

Takes validated Terraform JSON and converts it to properly formatted .tf file content.
This agent ensures all Terraform code follows standard formatting conventions.
"""

import json
from typing import Dict, Any
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types


def create_formatter_agent(retry_config: types.HttpRetryOptions) -> LlmAgent:
    """
    Create the Terraform Formatter Agent.
    
    This agent takes Terraform code in JSON format and outputs properly
    formatted .tf file content ready to be written to disk.
    
    Args:
        retry_config: HTTP retry configuration for the LLM
        
    Returns:
        Configured LlmAgent for Terraform formatting
    """
    
    agent = LlmAgent(
        name="terraform_formatter_agent",
        model=Gemini(
            model="gemini-2.5-flash-lite",
            retry_options=retry_config
        ),
        description="Formats Terraform code according to standard conventions.",
        instruction="""You are a Terraform formatting specialist.

Your ONLY task is to take Terraform code and format it properly according to HashiCorp standards.

**CRITICAL: Output ONLY the exact formatted .tf file content. NO explanations. NO JSON. Just the raw .tf file text.**

**Formatting Rules:**
1. Consistent indentation (2 spaces)
2. Proper spacing around blocks and arguments
3. Alphabetical ordering of arguments within blocks (when logical)
4. Line breaks between resource blocks
5. Comments aligned properly
6. No trailing whitespace
7. Newline at end of file

**Input**: You will receive Terraform code as a string
**Output**: Return the exact same code, but properly formatted

Example Input:
```
resource "google_compute_network" "vpc" {
name="my-vpc"
auto_create_subnetworks=false
}
```

Example Output:
```
resource "google_compute_network" "vpc" {
  name                    = "my-vpc"
  auto_create_subnetworks = false
}
```

Output ONLY the formatted code. Do not explain what you did.
"""
    )
    
    return agent


def parse_formatted_code(agent_response: str) -> str:
    """
    Parse the agent's response and extract the formatted code.
    
    Args:
        agent_response: The text response from the agent
        
    Returns:
        Formatted Terraform code as string
    """
    response = agent_response.strip()
    
    # Remove markdown code blocks if present
    if '```hcl' in response:
        start = response.find('```hcl') + 6
        end = response.find('```', start)
        if end > start:
            response = response[start:end].strip()
    elif '```terraform' in response:
        start = response.find('```terraform') + 12
        end = response.find('```', start)
        if end > start:
            response = response[start:end].strip()
    elif '```' in response:
        start = response.find('```') + 3
        end = response.find('```', start)
        if end > start:
            response = response[start:end].strip()
    
    return response
