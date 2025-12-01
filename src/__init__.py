"""
TerraformAI - Multi-Agent Infrastructure as Code Generator
============================================================

A sophisticated multi-agent system built with Google's Agent Development Kit (ADK)
that transforms natural language descriptions into production-ready GCP Terraform code.

Key Features:
-------------
- 5-agent sequential pipeline with validation loop
- Session-based memory for iterative improvement
- Type-safe agent communication with Pydantic
- Comprehensive observability and logging
- Modular Terraform output structure

Architecture:
-------------
    User Input -> Requirements -> Architecture -> Generator <-> Validator -> Documentation
                                                     ↑__feedback loop__↓

ADK Features Demonstrated:
--------------------------
1. Multi-Agent System: 5 specialized LLM-powered agents
2. Sequential Agents: Pipeline from input to output
3. Loop Agents: Generator-Validator feedback cycle
4. Sessions & Memory: InMemorySessionService for context
5. State Management: Shared session for iterative learning
6. Observability: Comprehensive logging throughout

Quick Start:
------------
    from src.orchestrator import TerraformGeneratorOrchestrator
    
    orchestrator = TerraformGeneratorOrchestrator(output_dir=\"./output\")
    result = await orchestrator.run(\"Create a web app with Cloud Run\")
"""

__version__ = "0.1.0"
__author__ = "TerraformAI Team"

from .orchestrator import TerraformGeneratorOrchestrator, main
from .schemas import (
    RequirementsOutput,
    ArchitectureOutput,
    ArchitectureModule,
    GeneratorOutput,
    TerraformFile,
    TerraformModule,
    EnvironmentConfig,
    ValidatorOutput,
    ValidationError,
    DocumentationOutput,
)

__all__ = [
    # Main orchestrator
    "TerraformGeneratorOrchestrator",
    "main",
    # Schemas
    "RequirementsOutput",
    "ArchitectureOutput",
    "ArchitectureModule",
    "GeneratorOutput",
    "TerraformFile",
    "TerraformModule",
    "EnvironmentConfig",
    "ValidatorOutput",
    "ValidationError",
    "DocumentationOutput",
]