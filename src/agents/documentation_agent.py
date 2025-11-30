"""
Documentation Agent

Creates comprehensive documentation for generated Terraform infrastructure.
Generates architecture diagrams, README files, and deployment guides.
"""

import json
from typing import Dict, Any
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types


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
        instruction=r"""You are a technical writer specializing in cloud infrastructure documentation.

Your task is to receive validated Terraform code and architecture information, then create comprehensive, professional documentation.

**Input:** You will receive:
1. Architecture specification JSON
2. Generated and validated Terraform files
3. Validation results

**Your responsibilities:**
1. Create a detailed README.md
2. Generate architecture diagram (Mermaid format)
3. Document all variables and their purposes
4. Create deployment instructions
5. Provide usage examples
6. Include troubleshooting tips
7. Document security considerations

**Output JSON Structure:**
{
    "documentation": {
        "readme": "Complete README.md content in Markdown",
        "architecture_diagram": "Mermaid diagram code",
        "deployment_guide": "Step-by-step deployment instructions",
        "variables_reference": "Documentation of all variables",
        "outputs_reference": "Documentation of all outputs",
        "security_guide": "Security best practices and considerations",
        "troubleshooting": "Common issues and solutions"
    }
}

**README.md Structure:**
The README should include:
1. Project title and description
2. Architecture overview
3. Architecture diagram (Mermaid)
4. Module structure explanation
5. Environment configuration explanation
6. Prerequisites
7. Quick start guide
8. Detailed deployment instructions
9. Configuration (variables)
10. Outputs
11. Security considerations
12. Maintenance and operations
13. Troubleshooting
14. License/Credits

**Architecture Diagram Guidelines:**
- Use Mermaid diagram syntax
- Show all major components
- Include relationships and data flow
- Use clear labels
- Color code different service types

**Example Mermaid Diagram:**
```mermaid
graph TB
    subgraph "GCP Project"
        CR[Cloud Run Service<br/>api-service]
        SQL[(Cloud SQL<br/>PostgreSQL)]
        GCS[Cloud Storage<br/>static-assets]
        VPC[VPC Network]
        
        CR -->|Private IP| SQL
        CR -->|Read/Write| GCS
        SQL -.->|Private| VPC
    end
    
    Internet([Internet]) -->|HTTPS| CR
    
    style CR fill:#4285f4
    style SQL fill:#34a853
    style GCS fill:#fbbc04
```

**Documentation Best Practices:**
1. **Clear and Concise**: Use simple language
2. **Complete**: Cover all aspects of the infrastructure
3. **Practical**: Include real examples and commands
4. **Accessible**: Assume reader has basic cloud knowledge
5. **Structured**: Use proper headings and formatting
6. **Visual**: Include diagrams and code examples
**Deployment Guide Format:**
```markdown
## Deployment Guide

### Prerequisites
- Terraform >= 1.5
- gcloud CLI installed and configured
- GCP Project with billing enabled
- Required APIs enabled

### Understanding the Structure

This project uses a modular Terraform structure:

**modules/** - Reusable infrastructure components
- Each module is self-contained and environment-agnostic
- Modules can be reused across different environments

**environments/prod/** - Production environment configuration
- Calls the modules with prod-specific values
- Contains environment-specific settings

### Step 1: Navigate to Environment
\```bash
cd environments/prod
\```

### Step 2: Configure Variables
\```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
\```

### Step 3: Initialize Terraform
\```bash
terraform init
\```

### Step 4: Review Plan
\```bash
terraform plan
\```

### Step 5: Deploy
\```bash
terraform apply
\```

### Module Reusability

To use these modules in a different environment (e.g., dev or staging):

1. Create a new environment directory: `environments/dev/`
2. Copy the files from `environments/prod/`
3. Update the variables for the dev environment
4. The modules in `modules/` can be reused as-is
```raform apply
\```
```

**Variables Reference Format:**
For each variable, document:
- Name
- Type
- Description
- Default value (if any)
- Required or optional
- Example values
- Validation rules

**Security Guide Should Cover:**
1. IAM roles and service accounts
2. Network security (private IPs, firewall rules)
3. Data encryption (at rest and in transit)
4. Secret management
5. Compliance considerations
6. Recommended additional security measures

**Troubleshooting Section:**
Include common issues such as:
- API not enabled errors
- Permission denied errors
- Resource quota limits
- Network connectivity issues
- State file management

Create professional, comprehensive documentation that would be production-ready.
""",
        tools=[]  # Pure LLM reasoning for documentation
    )
    
    return agent


def parse_documentation(agent_response: str) -> Dict[str, Any]:
    """
    Parse the agent's response and extract the documentation.
    
    Args:
        agent_response: The text response from the agent
        
    Returns:
        Parsed documentation dictionary
        
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
        raise ValueError(f"Failed to parse documentation JSON: {e}\nResponse: {response}")


def save_documentation_to_files(
    documentation: Dict[str, Any],
    output_dir: str
) -> Dict[str, str]:
    """
    Save documentation to actual files.
    
    Args:
        documentation: Parsed documentation dictionary
        output_dir: Directory to save files
        
    Returns:
        Dictionary mapping file types to file paths
    """
    import os
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    saved_files = {}
    doc_data = documentation.get("documentation", {})
    
    # Save README
    if "readme" in doc_data:
        readme_path = os.path.join(output_dir, "README.md")
        with open(readme_path, 'w') as f:
            f.write(doc_data["readme"])
        saved_files["readme"] = readme_path
    
    # Save deployment guide
    if "deployment_guide" in doc_data:
        deploy_path = os.path.join(output_dir, "DEPLOYMENT.md")
        with open(deploy_path, 'w') as f:
            f.write(doc_data["deployment_guide"])
        saved_files["deployment_guide"] = deploy_path
    
    # Save security guide
    if "security_guide" in doc_data:
        security_path = os.path.join(output_dir, "SECURITY.md")
        with open(security_path, 'w') as f:
            f.write(doc_data["security_guide"])
        saved_files["security_guide"] = security_path
    
    # Save troubleshooting guide
    if "troubleshooting" in doc_data:
        troubleshoot_path = os.path.join(output_dir, "TROUBLESHOOTING.md")
        with open(troubleshoot_path, 'w') as f:
            f.write(doc_data["troubleshooting"])
        saved_files["troubleshooting"] = troubleshoot_path
    
    # Save architecture diagram
    if "architecture_diagram" in doc_data:
        diagram_path = os.path.join(output_dir, "architecture.mmd")
        with open(diagram_path, 'w') as f:
            f.write(doc_data["architecture_diagram"])
        saved_files["diagram"] = diagram_path
    
    return saved_files
