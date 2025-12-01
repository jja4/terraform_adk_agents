"""
Terraform Generator Agents Package
====================================

This package contains five specialized agents that form the multi-agent
pipeline for generating GCP Terraform infrastructure from natural language.

Agent Pipeline:
---------------
    User Input -> Requirements -> Architecture -> Generator <-> Validator -> Documentation
                                                     ↑__feedback loop__↓

Agents:
-------
1. requirements_agent.py
   - Parses natural language descriptions
   - Extracts structured requirements (compute, storage, networking)
   - Outputs JSON specification

2. architecture_agent.py
   - Receives requirements JSON
   - Designs GCP service topology
   - Determines Terraform module structure
   - Plans resource dependencies

3. generator_agent.py
   - Generates complete Terraform code
   - Creates modular structure (modules/ + environments/)
   - Participates in validation loop with shared session

4. validator_agent.py
   - Validates Terraform syntax and configuration
   - Checks for security vulnerabilities
   - Provides structured feedback for regeneration
   - Shares session with Generator for memory

5. documentation_agent.py
   - Creates README.md with architecture overview
   - Generates deployment instructions
   - Documents configuration variables

ADK Features Demonstrated:
--------------------------
- LlmAgent: All agents powered by Gemini 2.5 Flash Lite
- Sequential pattern: Agents pass structured data to next agent
- Loop pattern: Generator-Validator feedback cycle
- Session memory: Shared session for iterative learning
"""

__version__ = "0.1.0"

# Import agent creation functions for convenient access
from .requirements_agent import create_requirements_agent, parse_requirements
from .architecture_agent import create_architecture_agent, parse_architecture
from .generator_agent import create_generator_agent, parse_generated_terraform
from .validator_agent import (
    create_validator_agent,
    parse_validation_results,
    should_regenerate,
    get_feedback_for_regeneration
)
from .documentation_agent import (
    create_documentation_agent,
    parse_documentation,
    save_documentation_to_files
)

__all__ = [
    # Requirements Agent
    "create_requirements_agent",
    "parse_requirements",
    # Architecture Agent
    "create_architecture_agent",
    "parse_architecture",
    # Generator Agent
    "create_generator_agent",
    "parse_generated_terraform",
    # Validator Agent
    "create_validator_agent",
    "parse_validation_results",
    "should_regenerate",
    "get_feedback_for_regeneration",
    # Documentation Agent
    "create_documentation_agent",
    "parse_documentation",
    "save_documentation_to_files",
]
