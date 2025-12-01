"""
Validator/Critic Agent Module
==============================

This agent is the fourth in the sequential pipeline and participates in
the validation loop with the Generator. It analyzes Terraform code for
errors, security issues, and best practice violations.

ADK Features Demonstrated:
--------------------------
1. LlmAgent - Agent powered by an LLM (Gemini 2.5 Flash Lite)
2. Loop Agent Pattern - Iterates with Generator until code passes
3. Session Memory - Shares session with Generator for context
4. Pydantic Structured Output - Uses ValidatorOutput schema

Agent Role in Pipeline:
-----------------------
    Generated Code -> [Validator Agent] -> Feedback OR Approved Code
                              ↓                    ↓
                     [Generator Agent]     [Documentation Agent]
                         (retry)               (continue)

The Validator acts as a senior code reviewer, checking for:
- Terraform syntax errors
- Missing required fields
- Invalid resource references
- Security vulnerabilities (public IPs, open access)
- Best practice violations

Validation Loop Behavior:
-------------------------
1. Receive Terraform code from Generator
2. Analyze for errors and issues
3. If errors found: Return structured feedback to Generator
4. If no errors: Pass code to Documentation Agent
5. Loop continues until validation passes or max iterations reached

Session Memory Integration:
---------------------------
The Validator shares session_id=\"validation_loop\" with Generator:
- Remembers previous validation results
- Provides consistent feedback across iterations
- Tracks which errors have been fixed

Structured Output Schema:
-------------------------
ValidatorOutput (Pydantic model):
- validation_status: \"passed\" | \"failed\"
- errors: List of ValidationError with severity, file, message, fix
- summary: Brief assessment of code quality
"""

import json
from typing import Dict, Any, List
from pydantic import ValidationError as PydanticValidationError
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types
from src.schemas import ValidatorOutput, ValidationError
import logging

logger = logging.getLogger(__name__)

def create_validator_agent(retry_config: types.HttpRetryOptions) -> LlmAgent:
    """
    Create and configure the Validator/Critic Agent.
    
    This function creates an LlmAgent that validates Terraform code and
    provides constructive feedback for the Generator to improve.
    
    ADK Features Used:
    ------------------
    - LlmAgent: Core ADK agent class for code analysis
    - Gemini model: Uses Gemini 2.5 Flash Lite for fast validation
    - Loop pattern: Works with Generator in feedback loop
    - Session memory: Shares session with Generator
    - No tools: Pure LLM reasoning for validation (tools=[])
    
    Validation Responsibilities:
    ----------------------------
    1. Check Terraform syntax correctness
    2. Validate required fields are present
    3. Verify resource references are valid
    4. Identify security vulnerabilities
    5. Check best practice compliance
    
    Structured Output:
    ------------------
    Outputs ValidatorOutput Pydantic model with:
    - validation_status: "passed" or "failed"
    - errors: List of ValidationError with max 10 items
    - summary: Brief assessment (max 200 chars)
    
    Context Engineering:
    --------------------
    The instruction prompt limits error messages to 100 chars and
    summary to 200 chars. This prevents context overflow during the
    feedback loop, ensuring the Generator has room for regeneration.
    
    Args:
        retry_config: HttpRetryOptions for API retry configuration
        
    Returns:
        Configured LlmAgent instance for code validation
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
    
    This function is the decision point in the validation loop. It determines
    whether to continue iterating (regenerate) or exit the loop (success).
    
    Decision Logic:
    ---------------
    Returns True (continue loop) if:
    - validation_status is "failed"
    - Any errors have severity="error"
    
    Returns False (exit loop) if:
    - validation_status is "passed"
    - Only warnings/info issues remain
    
    Loop Termination:
    -----------------
    The orchestrator also enforces max_validation_iterations as a safety
    limit, regardless of this function's return value.
    
    Args:
        validation_results: Validated ValidatorOutput from the Validator agent
        
    Returns:
        True if code has critical errors requiring regeneration
        False if code is acceptable
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
    
    This function formats validation errors into a clear, structured prompt
    that the Generator can use to fix issues in the next iteration.
    
    Feedback Structure:
    -------------------
    1. CRITICAL ERRORS: Errors that must be fixed (severity="error")
    2. WARNINGS: Issues that should be addressed (severity="warning")
    
    Each error includes:
    - File location (e.g., "modules/cloud_run/main.tf")
    - Error message (what's wrong)
    - Fix suggestion (how to fix it)
    
    Context Engineering:
    --------------------
    The feedback format is designed to:
    - Be clear and actionable for the LLM
    - Prioritize critical errors
    - Provide specific fix suggestions
    - Fit within context limits
    
    Args:
        validation_results: ValidatorOutput with errors to format
        
    Returns:
        Formatted feedback string for the Generator agent
    
    Example Output:
        The Terraform code has the following issues that need to be fixed:
        
        **CRITICAL ERRORS:**
        - [modules/vpc/main.tf] Missing required variable 'project_id'
          Fix: Add variable declaration for project_id
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
