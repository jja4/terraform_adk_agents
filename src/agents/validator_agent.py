"""
Validator/Critic Agent

Validates generated Terraform code and provides feedback for improvements.
Uses terraform validate and terraform plan tools.
"""

import json
from typing import Dict, Any, List
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types
from src.tools.terraform_tools import (
    terraform_validate,
    terraform_plan,
    check_terraform_syntax
)


def create_validator_agent(retry_config: types.HttpRetryOptions) -> LlmAgent:
    """
    Create the Validator/Critic Agent.
    
    This agent specializes in validating Terraform code and providing
    constructive feedback for improvements.
    
    Args:
        retry_config: HTTP retry configuration for the LLM
        
    Returns:
        Configured LlmAgent for validation and critique
    """
    
    agent = LlmAgent(
        name="validator_critic_agent",
        model=Gemini(
            model="gemini-2.5-flash-lite",
            retry_options=retry_config
        ),
        description="Validates Terraform code and provides expert feedback for improvements.",
        instruction="""You are a senior DevOps engineer and Terraform expert specializing in code review and validation.

Your task is to receive generated Terraform code, validate it thoroughly, and provide constructive feedback.

**Input:** You will receive a JSON object containing generated Terraform files.

**Your validation process:**
1. Use check_terraform_syntax to validate basic syntax
2. Use terraform_validate to check configuration validity
3. Use terraform_plan to simulate deployment (dry-run)
4. Analyze the code for best practices and security
5. Provide detailed feedback

**Use the available tools:**
- `check_terraform_syntax(code)`: Basic syntax validation
- `terraform_validate(code, module_name)`: Full Terraform validation
- `terraform_plan(code, var_file)`: Simulate deployment plan

**What to check:**
1. **Syntax Errors**: Unbalanced braces, quotes, brackets
2. **Configuration Errors**: Invalid resource types, missing required fields
3. **Best Practices**:
   - Proper naming conventions
   - Variable usage vs hardcoded values
   - Resource dependencies
   - Security (private IPs, IAM least privilege)
   - Labels and tags
   - Comments and documentation
4. **Security Issues**:
   - Public IP exposure
   - Overly permissive IAM roles
   - Missing encryption
   - Exposed secrets
5. **Performance & Cost**:
   - Resource sizing
   - Unnecessary resources
   - Multi-region considerations

**Output JSON Structure:**
{
    "validation_status": "passed|failed|warning",
    "syntax_valid": true/false,
    "configuration_valid": true/false,
    "plan_successful": true/false,
    "errors": [
        {
            "severity": "error|warning|info",
            "category": "syntax|configuration|security|best_practice",
            "message": "description of the issue",
            "file": "filename where issue occurs",
            "suggestion": "how to fix it"
        }
    ],
    "recommendations": [
        "list of improvement suggestions"
    ],
    "security_score": 0-100,
    "best_practices_score": 0-100,
    "summary": "overall assessment"
}

**Validation Levels:**
- **passed**: No errors, only minor suggestions
- **warning**: No blocking errors but significant warnings
- **failed**: Critical errors that must be fixed

**Error Categories:**
- **syntax**: Code syntax errors
- **configuration**: Invalid Terraform configuration
- **security**: Security vulnerabilities or concerns
- **best_practice**: Code that works but doesn't follow best practices

**Feedback Guidelines:**
1. Be specific about what's wrong
2. Always provide a suggestion for fixing
3. Explain WHY something is a problem
4. Prioritize critical issues first
5. Balance critique with positive feedback
6. Be constructive and educational

**Example Validation Output:**
```json
{
    "validation_status": "warning",
    "syntax_valid": true,
    "configuration_valid": true,
    "plan_successful": true,
    "errors": [
        {
            "severity": "warning",
            "category": "security",
            "message": "Cloud SQL instance is configured with public IP",
            "file": "database.tf",
            "suggestion": "Use private IP and configure VPC peering for secure database access. Set 'ipv4_enabled = false' in ip_configuration block."
        },
        {
            "severity": "info",
            "category": "best_practice",
            "message": "Variable 'project_id' has no description",
            "file": "variables.tf",
            "suggestion": "Add description field: description = \\"GCP Project ID\\""
        }
    ],
    "recommendations": [
        "Consider adding Cloud Armor for DDoS protection",
        "Implement Cloud Monitoring alerts",
        "Add lifecycle policies for stateful resources"
    ],
    "security_score": 75,
    "best_practices_score": 85,
    "summary": "Code is functional and valid. Security can be improved by using private IPs for database. Consider adding the recommended monitoring and protection services."
}
```

Always validate code thoroughly using all available tools before providing feedback.
""",
        tools=[
            check_terraform_syntax,
            terraform_validate,
            terraform_plan
        ]
    )
    
    return agent


def parse_validation_results(agent_response: str) -> Dict[str, Any]:
    """
    Parse the agent's response and extract the validation results.
    
    Args:
        agent_response: The text response from the agent
        
    Returns:
        Parsed validation results dictionary
        
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
        raise ValueError(f"Failed to parse validation results JSON: {e}\nResponse: {response}")


def should_regenerate(validation_results: Dict[str, Any]) -> bool:
    """
    Determine if code should be regenerated based on validation results.
    
    Args:
        validation_results: Parsed validation results
        
    Returns:
        True if code has critical errors and should be regenerated
    """
    status = validation_results.get("validation_status", "failed")
    
    # Regenerate if validation failed
    if status == "failed":
        return True
    
    # Check if there are any critical errors
    errors = validation_results.get("errors", [])
    has_critical_errors = any(
        error.get("severity") == "error" and 
        error.get("category") in ["syntax", "configuration"]
        for error in errors
    )
    
    return has_critical_errors


def get_feedback_for_regeneration(validation_results: Dict[str, Any]) -> str:
    """
    Extract actionable feedback for code regeneration.
    
    Args:
        validation_results: Parsed validation results
        
    Returns:
        Formatted feedback string for the generator agent
    """
    errors = validation_results.get("errors", [])
    recommendations = validation_results.get("recommendations", [])
    
    feedback_parts = ["The Terraform code has the following issues that need to be fixed:\n"]
    
    # Add critical errors first
    critical_errors = [e for e in errors if e.get("severity") == "error"]
    if critical_errors:
        feedback_parts.append("\n**CRITICAL ERRORS:**")
        for error in critical_errors:
            feedback_parts.append(
                f"- [{error.get('file')}] {error.get('message')}\n"
                f"  Fix: {error.get('suggestion')}"
            )
    
    # Add warnings
    warnings = [e for e in errors if e.get("severity") == "warning"]
    if warnings:
        feedback_parts.append("\n**WARNINGS:**")
        for warning in warnings:
            feedback_parts.append(
                f"- [{warning.get('file')}] {warning.get('message')}\n"
                f"  Suggestion: {warning.get('suggestion')}"
            )
    
    # Add recommendations
    if recommendations:
        feedback_parts.append("\n**RECOMMENDATIONS:**")
        for rec in recommendations:
            feedback_parts.append(f"- {rec}")
    
    return "\n".join(feedback_parts)
