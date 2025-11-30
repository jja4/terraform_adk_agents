"""
Validator/Critic Agent

Validates generated Terraform code and provides feedback for improvements.
Uses Pydantic models for type-safe structured output.
"""

import json
from typing import Dict, Any, List
from pydantic import ValidationError as PydanticValidationError
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types
from src.schemas import ValidatorOutput, ValidationError
from src.tools.terraform_tools import (
    terraform_validate,
    terraform_plan,
    check_terraform_syntax
)
import logging

logger = logging.getLogger(__name__)

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
        instruction="""You are a Terraform validation expert. Analyze Terraform code for errors and issues.

CRITICAL: Output ONLY valid JSON that matches the ValidatorOutput schema.

Schema (output must match this exactly):
{
  "validation_status": "passed" or "failed",
  "syntax_valid": true or false,
  "configuration_valid": true or false,
  "errors": [
    {
      "severity": "error" or "warning" or "info",
      "file": "path/to/file",
      "message": "Max 100 chars",
      "fix": "Max 100 chars"
    }
  ],
  "error_count": number,
  "summary": "Max 200 chars"
}

Rules:
- Max 10 errors
- Keep messages under 100 characters
- Keep summary under 200 characters
- No code snippets in messages
- Do NOT use any tools

Check for:
1. Syntax errors
2. Missing required fields  
3. Invalid resource references
4. Security issues (public IPs, open access)
5. Best practices violations

Output JSON immediately in a ```json code block.""",
        # No tools - agent outputs JSON directly without tool usage
        tools=[]
    )
    
    return agent


def parse_validation_results(agent_response: str) -> ValidatorOutput:
    """
    Parse validation results from agent response using Pydantic validation.
    
    Args:
        agent_response: Raw response from validation agent
        
    Returns:
        Validated ValidatorOutput object
        
    Raises:
        ValueError: If the response cannot be parsed or validated
    """
    response = agent_response.strip()
    
    # Extract JSON from markdown code blocks
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
            if potential_json.startswith('{'):
                response = potential_json
    
    response = response.strip()
    
    try:
        # Parse JSON
        data = json.loads(response)
        # Validate with Pydantic - this ensures type safety
        return ValidatorOutput(**data)
    except json.JSONDecodeError as e:
        # Fallback: create minimal valid response
        return ValidatorOutput(
            validation_status="failed",
            syntax_valid=True,
            configuration_valid=False,
            errors=[ValidationError(
                severity="error",
                file="unknown",
                message="JSON parsing failed",
                fix="Check response format"
            )],
            error_count=1,
            summary=f"Parse error: {str(e)[:150]}"
        )
    except PydanticValidationError as e:
        # Pydantic validation failed - return error details
        return ValidatorOutput(
            validation_status="failed",
            syntax_valid=True,
            configuration_valid=False,
            errors=[ValidationError(
                severity="error",
                file="unknown",
                message="Schema validation failed",
                fix="Check ValidatorOutput schema"
            )],
            error_count=1,
            summary=f"Validation error: {str(e)[:150]}"
        )


def should_regenerate(validation_results: ValidatorOutput) -> bool:
    """
    Determine if code should be regenerated based on validation results.
    
    Args:
        validation_results: Validated ValidatorOutput object
        
    Returns:
        True if code has critical errors and should be regenerated
    """
    status = validation_results.validation_status
    
    # Regenerate if validation failed
    if status == "failed":
        return True
    
    # Check if there are any critical errors
    has_critical_errors = any(
        error.severity == "error"
        for error in validation_results.errors
    )
    
    return has_critical_errors


def get_feedback_for_regeneration(validation_results: ValidatorOutput) -> str:
    """
    Extract actionable feedback for code regeneration.
    
    Args:
        validation_results: Validated ValidatorOutput object
        
    Returns:
        Formatted feedback string for the generator agent
    """
    errors = validation_results.errors
    
    feedback_parts = ["The Terraform code has the following issues that need to be fixed:\n"]
    
    # Add critical errors first
    critical_errors = [e for e in errors if e.severity == "error"]
    if critical_errors:
        feedback_parts.append("\n**CRITICAL ERRORS:**")
        for error in critical_errors:
            feedback_parts.append(
                f"- [{error.file}] {error.message}\n"
                f"  Fix: {error.fix}"
            )
    
    # Add warnings
    warnings = [e for e in errors if e.severity == "warning"]
    if warnings:
        feedback_parts.append("\n**WARNINGS:**")
        for warning in warnings:
            feedback_parts.append(
                f"- [{warning.file}] {warning.message}\n"
                f"  Suggestion: {warning.fix}"
            )
    
    return "\n".join(feedback_parts)
