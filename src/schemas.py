"""
Data schemas for agent communication using Pydantic models.

This eliminates JSON parsing errors by using structured Python objects.
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


# ============================================================================
# Requirements Agent Output
# ============================================================================

class RequirementsOutput(BaseModel):
    """Structured output from requirements agent."""
    project_name: str = Field(description="Name of the project")
    infrastructure_type: str = Field(description="Type of infrastructure")
    services: List[str] = Field(description="List of GCP services needed")
    environment: str = Field(description="Target environment (dev/staging/prod)")
    region: str = Field(default="us-central1", description="GCP region")
    additional_requirements: Optional[List[str]] = Field(default=None, description="Extra requirements")


# ============================================================================
# Architecture Agent Output
# ============================================================================

class ArchitectureModule(BaseModel):
    """A single Terraform module in the architecture."""
    module_name: str
    purpose: str
    resources: List[Dict[str, Any]]
    outputs: List[str]
    dependencies: List[str]


class ArchitectureOutput(BaseModel):
    """Structured output from architecture agent."""
    architecture_name: str
    description: str
    modules: List[ArchitectureModule]
    deployment_order: List[str]


# ============================================================================
# Generator Agent Output
# ============================================================================

class TerraformFile(BaseModel):
    """A single Terraform file."""
    filename: str
    content: str


class TerraformModule(BaseModel):
    """A Terraform module with its files."""
    module_name: str
    path: str
    files: List[TerraformFile]


class EnvironmentConfig(BaseModel):
    """Environment-specific Terraform configuration."""
    main_tf: str
    variables_tf: str
    outputs_tf: str
    provider_tf: str
    terraform_tfvars_example: str


class GeneratorOutput(BaseModel):
    """Structured output from generator agent."""
    terraform_version: str
    modules: List[TerraformModule]
    environments: Dict[str, EnvironmentConfig]


# ============================================================================
# Validator Agent Output
# ============================================================================

class ValidationError(BaseModel):
    """A single validation error."""
    severity: Literal["error", "warning", "info"]
    file: str
    message: str = Field(max_length=100, description="Short error description")
    fix: str = Field(max_length=100, description="Short fix suggestion")


class ValidatorOutput(BaseModel):
    """Structured output from validator agent."""
    validation_status: Literal["passed", "failed"]
    syntax_valid: bool
    configuration_valid: bool
    errors: List[ValidationError] = Field(default_factory=list, max_length=10)
    error_count: int
    summary: str = Field(max_length=200, description="One sentence assessment")


# ============================================================================
# Documentation Agent Output
# ============================================================================

class DocumentationFile(BaseModel):
    """A single documentation file."""
    filename: str
    content: str = Field(description="Full file content - can be long")


class DocumentationOutput(BaseModel):
    """Structured output from documentation agent."""
    readme: str = Field(description="Complete README.md content with all sections including deployment")
    deployment_guide: Optional[str] = Field(default=None, description="Optional separate deployment guide")
    architecture_diagram: Optional[str] = Field(default=None, description="Mermaid diagram")
    security_guide: Optional[str] = Field(default=None, description="Security best practices")
    troubleshooting: Optional[str] = Field(default=None, description="Troubleshooting guide")
