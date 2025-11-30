"""
Orchestrator

Main orchestrator for the Terraform Generator multi-agent system.
Manages the message passing sequence between agents.
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from google.genai import types
from google.adk.runners import InMemoryRunner

# Load environment variables from .env file
load_dotenv()

# Import agent creators
from src.agents.requirements_agent import create_requirements_agent, parse_requirements
from src.agents.architecture_agent import create_architecture_agent, parse_architecture
from src.agents.generator_agent import create_generator_agent, parse_generated_terraform
from src.agents.validator_agent import (
    create_validator_agent,
    parse_validation_results,
    should_regenerate,
    get_feedback_for_regeneration
)
from src.agents.documentation_agent import (
    create_documentation_agent,
    parse_documentation,
    save_documentation_to_files
)


class TerraformGeneratorOrchestrator:
    """
    Orchestrates the multi-agent system for Terraform code generation.
    
    Implements the message passing sequence:
    User → Requirements → Architecture → Generator → Validator → (loop) → Documentation
    """
    
    def __init__(self, output_dir: str = "./output", max_validation_iterations: int = 3):
        """
        Initialize the orchestrator.
        
        Args:
            output_dir: Directory to save generated files
            max_validation_iterations: Maximum number of validation/regeneration cycles
        """
        self.output_dir = output_dir
        self.max_validation_iterations = max_validation_iterations
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Configure retry options for all agents
        self.retry_config = types.HttpRetryOptions(
            attempts=5,
            exp_base=7,
            initial_delay=1,
            http_status_codes=[429, 500, 503, 504]
        )
        
        # Initialize agents
        print("🤖 Initializing agents...")
        self.requirements_agent = create_requirements_agent(self.retry_config)
        self.architecture_agent = create_architecture_agent(self.retry_config)
        self.generator_agent = create_generator_agent(self.retry_config)
        self.validator_agent = create_validator_agent(self.retry_config)
        self.documentation_agent = create_documentation_agent(self.retry_config)
        print("✅ All agents initialized\n")
    
    async def run(self, user_input: str) -> Dict[str, Any]:
        """
        Run the complete orchestration process.
        
        Args:
            user_input: Natural language description of the infrastructure
            
        Returns:
            Dictionary containing all outputs and metadata
        """
        print("=" * 80)
        print("🚀 TERRAFORM GENERATOR MULTI-AGENT SYSTEM")
        print("=" * 80)
        print(f"\n📝 User Input:\n{user_input}\n")
        
        # Step 1: Requirements Extraction
        print("-" * 80)
        print("STEP 1: Requirements Extraction")
        print("-" * 80)
        requirements = await self._extract_requirements(user_input)
        print(f"✅ Requirements extracted: {requirements.get('application_name', 'N/A')}")
        print(f"   Components: {len(requirements.get('components', []))}")
        self._save_json(requirements, "requirements.json")
        
        # Step 2: Architecture Design
        print("\n" + "-" * 80)
        print("STEP 2: Architecture Design")
        print("-" * 80)
        architecture = await self._design_architecture(requirements)
        print(f"✅ Architecture designed: {architecture.get('architecture_name', 'N/A')}")
        print(f"   Modules: {len(architecture.get('modules', []))}")
        self._save_json(architecture, "architecture.json")
        
        # Step 3: Terraform Generation
        print("\n" + "-" * 80)
        print("STEP 3: Terraform Code Generation")
        print("-" * 80)
        terraform_code = await self._generate_terraform(architecture)
        print(f"✅ Terraform code generated")
        print(f"   Files: {len(terraform_code.get('files', []))}")
        
        # Step 4: Validation Loop
        print("\n" + "-" * 80)
        print("STEP 4: Validation Loop")
        print("-" * 80)
        validated_code, validation_results = await self._validation_loop(
            terraform_code, architecture
        )
        
        if validation_results.get("validation_status") == "passed":
            print("✅ Validation PASSED")
        elif validation_results.get("validation_status") == "warning":
            print("⚠️  Validation passed with WARNINGS")
        else:
            print("❌ Validation FAILED (proceeding with documentation anyway)")
        
        # Step 5: Documentation
        print("\n" + "-" * 80)
        print("STEP 5: Documentation Generation")
        print("-" * 80)
        documentation = await self._generate_documentation(
            architecture, validated_code, validation_results
        )
        print("✅ Documentation generated")
        
        # Save all outputs
        self._save_terraform_files(validated_code)
        saved_docs = save_documentation_to_files(documentation, self.output_dir)
        
        # Count module and environment files
        # Final summary
        print("\n" + "=" * 80)
        print("🎉 GENERATION COMPLETE")
        print("=" * 80)
        print(f"📁 Output directory: {self.output_dir}")
        
        module_count = len(validated_code.get("modules", []))
        env_count = len(validated_code.get("environments", {}))
        
        if module_count > 0:
            print(f"\n📦 Module Structure:")
            print(f"   - Reusable modules: {module_count}")
            for module in validated_code.get("modules", []):
                module_name = module.get("module_name", "unknown")
                print(f"     • modules/{module_name}/")
        
        if env_count > 0:
            print(f"\n🌍 Environments:")
            for env_name in validated_code.get("environments", {}).keys():
                print(f"   - environments/{env_name}/")
        
        print(f"\n📄 Documentation: {len(saved_docs)} files")
        print(f"📋 Metadata: 2 files (requirements.json, architecture.json)")
        print("=" * 80)
        
        # Final summary
        print("\n" + "=" * 80)
        print("🎉 GENERATION COMPLETE")
        print("=" * 80)
        print(f"📁 Output directory: {self.output_dir}")
        print(f"   - Terraform files: {len(validated_code.get('files', []))}")
        print(f"   - Documentation files: {len(saved_docs)}")
        print(f"   - Metadata files: 2 (requirements.json, architecture.json)")
        print("=" * 80)
        
        return {
            "requirements": requirements,
            "architecture": architecture,
            "terraform_code": validated_code,
            "validation_results": validation_results,
            "documentation": documentation,
            "output_dir": self.output_dir
        }
    
    async def _extract_requirements(self, user_input: str) -> Dict[str, Any]:
        """Extract requirements from user input."""
        runner = InMemoryRunner(agent=self.requirements_agent)
        response = await runner.run_debug(user_input)
        
        # Extract text from response
        response_text = self._extract_response_text(response)
        return parse_requirements(response_text)
    
    async def _design_architecture(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Design architecture from requirements."""
        prompt = f"""Design a GCP infrastructure architecture based on these requirements:

{json.dumps(requirements, indent=2)}

Use the available tools to validate service availability and compatibility.
Output the complete architecture specification in JSON format."""
        
        runner = InMemoryRunner(agent=self.architecture_agent)
        response = await runner.run_debug(prompt)
        
        response_text = self._extract_response_text(response)
        return parse_architecture(response_text)
    
    async def _generate_terraform(self, architecture: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Terraform code from architecture."""
        prompt = f"""Generate complete Terraform code for this architecture:

{json.dumps(architecture, indent=2)}

Use terraform_fmt to format the code and check_terraform_syntax to validate.
Output all Terraform files in JSON format."""
        
        runner = InMemoryRunner(agent=self.generator_agent)
        response = await runner.run_debug(prompt)
        
        response_text = self._extract_response_text(response)
        return parse_generated_terraform(response_text)
    
    async def _validation_loop(
        self, 
        terraform_code: Dict[str, Any],
        architecture: Dict[str, Any]
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Validation loop with feedback and regeneration.
        
        Returns:
            Tuple of (validated_code, validation_results)
        """
        current_code = terraform_code
        iteration = 0
        
        while iteration < self.max_validation_iterations:
            iteration += 1
            print(f"\n🔍 Validation iteration {iteration}/{self.max_validation_iterations}")
            
            # Validate current code
            validation_results = await self._validate_terraform(current_code)
            
            # Check if we should regenerate
            if not should_regenerate(validation_results):
                print(f"✅ Validation successful on iteration {iteration}")
                return current_code, validation_results
            
            # If this was the last iteration, return anyway
            if iteration >= self.max_validation_iterations:
                print(f"⚠️  Max iterations reached. Returning current code.")
                return current_code, validation_results
            
            # Generate feedback and regenerate
            print(f"❌ Validation failed. Generating feedback for regeneration...")
            feedback = get_feedback_for_regeneration(validation_results)
            
            regenerate_prompt = f"""The previous Terraform code had validation errors. Please fix them.

ORIGINAL ARCHITECTURE:
{json.dumps(architecture, indent=2)}

PREVIOUS CODE:
{json.dumps(current_code, indent=2)}

VALIDATION FEEDBACK:
{feedback}

Generate corrected Terraform code that addresses all the issues above.
Use terraform_fmt and check_terraform_syntax to validate the new code.
Output the corrected code in JSON format."""
            
            runner = InMemoryRunner(agent=self.generator_agent)
            response = await runner.run_debug(regenerate_prompt)
            response_text = self._extract_response_text(response)
            current_code = parse_generated_terraform(response_text)
        
        # Should not reach here, but just in case
        return current_code, validation_results
    
    async def _validate_terraform(self, terraform_code: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Terraform code."""
        prompt = f"""Validate this Terraform code thoroughly:

{json.dumps(terraform_code, indent=2)}

Use all available validation tools:
- check_terraform_syntax for syntax validation
- terraform_validate for configuration validation
- terraform_plan for deployment simulation

Provide detailed feedback in JSON format."""
        
        runner = InMemoryRunner(agent=self.validator_agent)
        response = await runner.run_debug(prompt)
        
        response_text = self._extract_response_text(response)
        return parse_validation_results(response_text)
    
    async def _generate_documentation(
        self,
        architecture: Dict[str, Any],
        terraform_code: Dict[str, Any],
        validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate documentation."""
        prompt = f"""Generate comprehensive documentation for this Terraform infrastructure:

ARCHITECTURE:
{json.dumps(architecture, indent=2)}

TERRAFORM CODE:
{json.dumps(terraform_code, indent=2)}

VALIDATION RESULTS:
{json.dumps(validation_results, indent=2)}

Create complete documentation including README, deployment guide, architecture diagrams, and troubleshooting.
Output in JSON format."""
        
        runner = InMemoryRunner(agent=self.documentation_agent)
        response = await runner.run_debug(prompt)
        
        response_text = self._extract_response_text(response)
        return parse_documentation(response_text)
    
    def _extract_response_text(self, response) -> str:
        """Extract text content from agent response."""
        if isinstance(response, str):
            return response
        
        # Handle list of response events
        if isinstance(response, list):
            text_parts = []
            for event in response:
                if hasattr(event, 'content') and event.content:
                    # Check if parts exists and is not None
                    if hasattr(event.content, 'parts') and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
            
            # If we found text parts, join them
            if text_parts:
                combined = '\n'.join(text_parts)
                
                # Try to extract JSON from markdown code blocks
                if '```json' in combined:
                    json_start = combined.find('```json') + 7
                    json_end = combined.find('```', json_start)
                    if json_end > json_start:
                        return combined[json_start:json_end].strip()
                elif '```' in combined:
                    # Try generic code block
                    json_start = combined.find('```') + 3
                    json_end = combined.find('```', json_start)
                    if json_end > json_start:
                        potential_json = combined[json_start:json_end].strip()
                        # Check if it looks like JSON
                        if potential_json.startswith('{') or potential_json.startswith('['):
                            return potential_json
                
                return combined
            
            return ""
        
        return str(response)
    
    def _save_json(self, data: Dict[str, Any], filename: str):
        """Save JSON data to file."""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_terraform_files(self, terraform_code: Dict[str, Any]):
        """Save Terraform files to disk with modular structure."""
        
        # Save modules
        for module in terraform_code.get("modules", []):
            module_name = module.get("module_name", "unknown")
            module_path = os.path.join(self.output_dir, "modules", module_name)
            os.makedirs(module_path, exist_ok=True)
            
            for file_info in module.get("files", []):
                filename = file_info.get("filename", "unknown.tf")
                content = file_info.get("content", "")
                filepath = os.path.join(module_path, filename)
                with open(filepath, 'w') as f:
                    f.write(content)
        
        # Save environment configurations
        environments = terraform_code.get("environments", {})
        for env_name, env_config in environments.items():
            env_path = os.path.join(self.output_dir, "environments", env_name)
            os.makedirs(env_path, exist_ok=True)
            
            # Save each environment file
            file_mappings = {
                "main_tf": "main.tf",
                "variables_tf": "variables.tf",
                "outputs_tf": "outputs.tf",
                "provider_tf": "provider.tf",
                "terraform_tfvars_example": "terraform.tfvars.example"
            }
            
            for key, filename in file_mappings.items():
                if key in env_config:
                    filepath = os.path.join(env_path, filename)
                    with open(filepath, 'w') as f:
                        f.write(env_config[key])
        
        # Also save to root for backward compatibility (optional)
        # Save old format files if they exist
        for file_info in terraform_code.get("files", []):
            filename = file_info.get("filename", "unknown.tf")
            content = file_info.get("content", "")
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, 'w') as f:
                f.write(content)
        
        # Save provider file
        if "provider_file" in terraform_code:
            provider = terraform_code["provider_file"]
            filepath = os.path.join(self.output_dir, provider.get("filename", "provider.tf"))
            with open(filepath, 'w') as f:
                f.write(provider.get("content", ""))
        
        # Save variables file
        if "variables_file" in terraform_code:
            variables = terraform_code["variables_file"]
            filepath = os.path.join(self.output_dir, variables.get("filename", "variables.tf"))
            with open(filepath, 'w') as f:
                f.write(variables.get("content", ""))
        
        # Save outputs file
        if "outputs_file" in terraform_code:
            outputs = terraform_code["outputs_file"]
            filepath = os.path.join(self.output_dir, outputs.get("filename", "outputs.tf"))
            with open(filepath, 'w') as f:
                f.write(outputs.get("content", ""))


async def main(user_input: str, output_dir: str = "./output"):
    """
    Main entry point for the orchestrator.
    
    Args:
        user_input: Natural language description of infrastructure
        output_dir: Directory to save outputs
        
    Returns:
        Dictionary containing all outputs
    """
    orchestrator = TerraformGeneratorOrchestrator(output_dir=output_dir)
    return await orchestrator.run(user_input)


if __name__ == "__main__":
    # Example usage
    example_input = """
    Create a web application with the following components:
    - Cloud Run service for the backend API
    - Cloud SQL PostgreSQL database for application data
    - Cloud Storage bucket for user uploads
    - VPC network for secure connectivity
    - IAM service account with least privilege access
    
    The application should be production-ready with proper security and monitoring.
    """
    
    asyncio.run(main(example_input))
