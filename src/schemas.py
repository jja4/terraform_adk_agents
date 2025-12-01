"""
Data Schemas Module - Type-Safe Agent Communication
====================================================

This module defines Pydantic models for structured data exchange between agents.
Using Pydantic provides:
1. Type safety - Compile-time guarantees about data shapes
2. Validation - Automatic input validation with clear error messages
3. Serialization - Easy conversion to/from JSON for LLM communication
4. Documentation - Self-documenting code with field descriptions

ADK Integration:
----------------
These schemas are used to parse LLM outputs into structured Python objects,
eliminating JSON parsing errors and making the multi-agent system robust.

Schema Hierarchy:
-----------------
1. RequirementsOutput - Parsed requirements from natural language
2. ArchitectureOutput - Infrastructure design with modules and dependencies
3. GeneratorOutput - Complete Terraform code with files and environments
4. ValidatorOutput - Validation results with errors and recommendations
5. DocumentationOutput - Generated README and deployment documentation

Design Rationale:
-----------------
- Each agent has dedicated input/output schemas
- Schemas use descriptive Field() annotations for LLM guidance
- Optional fields allow flexibility in agent responses
- Max lengths on error messages prevent context overflow
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


# ============================================================================
# REQUIREMENTS AGENT OUTPUT
# ============================================================================
# Schema for parsed requirements from natural language input.
# The Requirements Agent extracts structured infrastructure needs from
# user descriptions like "Create a web app with Cloud Run and PostgreSQL".
# ============================================================================

class RequirementsOutput(BaseModel):
    """
    Structured output from the Requirements Extraction Agent.
    
    This schema captures the essential infrastructure requirements parsed
    from natural language descriptions. It serves as the first structured
    data format in the pipeline, providing a foundation for architecture design.
    
    Attributes:
        project_name: Identifier for the infrastructure project
        infrastructure_type: Category of infrastructure (e.g., "web", "data", "ml")
        services: List of GCP services needed (e.g., ["cloud_run", "cloud_sql"])
        environment: Target deployment environment (dev/staging/prod)
        region: GCP region for resource deployment
        additional_requirements: Any extra requirements not captured elsewhere
    """
    project_name: str = Field(description="Name of the project")
    infrastructure_type: str = Field(description="Type of infrastructure")
    services: List[str] = Field(description="List of GCP services needed")
    environment: str = Field(description="Target environment (dev/staging/prod)")
    region: str = Field(default="us-central1", description="GCP region")
    additional_requirements: Optional[List[str]] = Field(default=None, description="Extra requirements")


# ============================================================================
# ARCHITECTURE AGENT OUTPUT
# ============================================================================
# Schema for infrastructure architecture design.
# The Architecture Agent takes requirements and designs the optimal
# GCP service topology and Terraform module structure.
# ============================================================================

class ArchitectureModule(BaseModel):
    """
    Represents a single Terraform module in the architecture.
    
    Each module is a reusable infrastructure component (e.g., vpc, cloud_run)
    that encapsulates related resources and exposes inputs/outputs.
    
    Attributes:
        module_name: Identifier for the module (e.g., "vpc", "cloud_run")
        purpose: Description of what this module provides
        resources: List of Terraform resources in this module
        outputs: Values exposed by this module for other modules to consume
        dependencies: Other modules this module depends on
    """
    module_name: str
    purpose: str
    resources: List[Dict[str, Any]]
    outputs: List[str]
    dependencies: List[str]


class ArchitectureOutput(BaseModel):
    """
    Structured output from the Architecture Design Agent.
    
    This schema defines the complete infrastructure architecture including
    module structure, resource relationships, and deployment ordering.
    
    Attributes:
        architecture_name: Human-readable name for the architecture
        description: Overview of what this architecture provides
        modules: List of Terraform modules to be generated
        deployment_order: Ordered list of module names for deployment sequence
    """
    architecture_name: str
    description: str
    modules: List[ArchitectureModule]
    deployment_order: List[str]


# ============================================================================
# GENERATOR AGENT OUTPUT
# ============================================================================
# Schema for generated Terraform code.
# The Generator Agent produces complete, modular Terraform configurations
# following best practices for structure and conventions.
# ============================================================================

class TerraformFile(BaseModel):
    """
    Represents a single Terraform file.
    
    Attributes:
        filename: Name of the file (e.g., "main.tf", "variables.tf")
        content: Complete HCL content of the file
    """
    filename: str
    content: str


class TerraformModule(BaseModel):
    """
    A Terraform module with its constituent files.
    
    Modules are reusable infrastructure components stored in the modules/
    directory. Each module typically contains main.tf, variables.tf, and outputs.tf.
    
    Attributes:
        module_name: Identifier for the module (e.g., "vpc", "cloud_run")
        path: Relative path to the module directory (e.g., "modules/vpc")
        files: List of Terraform files that make up this module
    """
    module_name: str
    path: str
    files: List[TerraformFile]


class EnvironmentConfig(BaseModel):
    """
    Environment-specific Terraform configuration.
    
    Environments (dev/staging/prod) contain configurations that call
    the reusable modules with environment-specific values.
    
    Attributes:
        main_tf: Main configuration that instantiates modules
        variables_tf: Variable definitions for this environment
        outputs_tf: Output definitions
        provider_tf: GCP provider configuration
        terraform_tfvars_example: Example variable values file
    """
    main_tf: str
    variables_tf: str
    outputs_tf: str
    provider_tf: str
    terraform_tfvars_example: str


class GeneratorOutput(BaseModel):
    """
    Structured output from the Terraform Generator Agent.
    
    This schema captures the complete generated Terraform codebase including
    reusable modules and environment-specific configurations.
    
    Attributes:
        terraform_version: Required Terraform version (e.g., "1.5")
        modules: List of reusable Terraform modules
        environments: Dict mapping environment names to their configurations
    """
    terraform_version: str
    modules: List[TerraformModule]
    environments: Dict[str, EnvironmentConfig]


# ============================================================================
# VALIDATOR AGENT OUTPUT
# ============================================================================
# Schema for validation results.
# The Validator Agent analyzes generated Terraform code for errors,
# security issues, and best practice violations.
#
# IMPORTANT: This schema includes max_length constraints to prevent
# context overflow in the validation loop. Long error messages would
# consume excessive tokens in subsequent iterations.
# ============================================================================

class ValidationError(BaseModel):
    """
    Represents a single validation error or warning.
    
    Design Note: Message and fix fields have max_length constraints
    to ensure the validation feedback fits within LLM context limits
    during the feedback loop.
    
    Attributes:
        severity: Error severity level (error/warning/info)
        file: Path to the file containing the issue
        message: Short description of the issue (max 100 chars)
        fix: Suggested fix for the issue (max 100 chars)
    """
    severity: Literal["error", "warning", "info"]
    file: str
    message: str = Field(max_length=100, description="Short error description")
    fix: str = Field(max_length=100, description="Short fix suggestion")


class ValidatorOutput(BaseModel):
    """
    Structured output from the Validator/Critic Agent.
    
    This schema is central to the validation loop - it provides structured
    feedback that the Generator Agent uses to improve its output.
    
    Design Decisions:
    - validation_status: Simple pass/fail for loop termination
    - errors list capped at 10 to prevent context overflow
    - summary capped at 200 chars for concise feedback
    
    Attributes:
        validation_status: Overall status ("passed" or "failed")
        syntax_valid: Whether Terraform syntax is correct
        configuration_valid: Whether resource configurations are valid
        errors: List of validation errors (max 10 items)
        error_count: Total number of errors found
        summary: Brief assessment of code quality (max 200 chars)
    """
    validation_status: Literal["passed", "failed"]
    syntax_valid: bool
    configuration_valid: bool
    errors: List[ValidationError] = Field(default_factory=list, max_length=10)
    error_count: int
    summary: str = Field(max_length=200, description="One sentence assessment")


# ============================================================================
# DOCUMENTATION AGENT OUTPUT
# ============================================================================
# Schema for generated documentation.
# The Documentation Agent creates README files and deployment guides
# for the generated Terraform infrastructure.
# ============================================================================

class DocumentationFile(BaseModel):
    """
    Represents a single documentation file.
    
    Attributes:
        filename: Name of the documentation file
        content: Full content of the file (can be long markdown)
    """
    filename: str
    content: str = Field(description="Full file content - can be long")


class DocumentationOutput(BaseModel):
    """
    Structured output from the Documentation Agent.
    
    This schema captures all generated documentation files including
    the main README and optional supplementary guides.
    
    Attributes:
        readme: Complete README.md content with all sections
        deployment_guide: Optional separate deployment instructions
        architecture_diagram: Optional Mermaid diagram source
        security_guide: Optional security best practices document
        troubleshooting: Optional troubleshooting guide
    """
    readme: str = Field(description="Complete README.md content with all sections including deployment")
    deployment_guide: Optional[str] = Field(default=None, description="Optional separate deployment guide")
    architecture_diagram: Optional[str] = Field(default=None, description="Mermaid diagram")
    security_guide: Optional[str] = Field(default=None, description="Security best practices")
    troubleshooting: Optional[str] = Field(default=None, description="Troubleshooting guide")
