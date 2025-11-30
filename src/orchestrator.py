"""
Orchestrator

Main orchestrator for the Terraform Generator multi-agent system.
Manages the message passing sequence between agents.
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from google.genai import types
from google.adk.runners import Runner

# Suppress ADK debug warnings about unknown agents
logging.getLogger('google.adk').setLevel(logging.ERROR)

# Configure logger for this module
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Import agent creators and Pydantic models
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
from src.schemas import ValidatorOutput, DocumentationOutput


class TerraformGeneratorOrchestrator:
    """
    Orchestrates the multi-agent system for Terraform code generation.
    
    Implements the message passing sequence:
    User → Requirements → Architecture → Generator → Validator → (loop) → Documentation
    """
    
    def __init__(self, output_dir: str = "./output", max_validation_iterations: int = 20):
        """
        Initialize the orchestrator.
        
        Args:
            output_dir: Directory to save generated files
            max_validation_iterations: Maximum number of validation/regeneration cycles (default: 20)
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
        logger.info("Initializing agents...")
        self.requirements_agent = create_requirements_agent(self.retry_config)
        self.architecture_agent = create_architecture_agent(self.retry_config)
        self.generator_agent = create_generator_agent(self.retry_config)
        self.validator_agent = create_validator_agent(self.retry_config)
        self.documentation_agent = create_documentation_agent(self.retry_config)
        
        # Initialize session service for memory persistence
        logger.info("Initializing session service...")
        from google.adk.sessions import InMemorySessionService
        self.session_service = InMemorySessionService()
        
        # Create persistent runners with session service
        # Each runner will maintain conversation history via session_id
        # Using app_name="agents" to match the agent directory structure
        self.requirements_runner = Runner(
            agent=self.requirements_agent,
            app_name="agents",
            session_service=self.session_service
        )
        self.architecture_runner = Runner(
            agent=self.architecture_agent,
            app_name="agents",
            session_service=self.session_service
        )
        self.generator_runner = Runner(
            agent=self.generator_agent,
            app_name="agents",
            session_service=self.session_service
        )
        self.validator_runner = Runner(
            agent=self.validator_agent,
            app_name="agents",
            session_service=self.session_service
        )
        self.documentation_runner = Runner(
            agent=self.documentation_agent,
            app_name="agents",
            session_service=self.session_service
        )
        logger.info("All agents and session service initialized")
    
    async def _initialize_sessions(self):
        """Create all sessions needed for the orchestration."""
        user_id = "user"
        app_name = "agents"
        
        # Create sessions for each agent
        session_ids = ["requirements", "architecture", "validation_loop", "documentation"]
        
        for session_id in session_ids:
            try:
                await self.session_service.create_session(
                    app_name=app_name,
                    user_id=user_id,
                    session_id=session_id
                )
            except Exception as e:
                # Session might already exist, try to get it
                try:
                    await self.session_service.get_session(
                        app_name=app_name,
                        user_id=user_id,
                        session_id=session_id
                    )
                except Exception:
                    pass  # Session will be created on first use
    
    async def run(self, user_input: str) -> Dict[str, Any]:
        """
        Run the complete orchestration process.
        
        Args:
            user_input: Natural language description of the infrastructure
            
        Returns:
            Dictionary containing all outputs and metadata
        """
        # Initialize sessions before running
        await self._initialize_sessions()
        
        logger.info("="*80)
        logger.info("TERRAFORM GENERATOR MULTI-AGENT SYSTEM")
        logger.info("="*80)
        logger.info(f"User Input: {user_input}")
        
        # Step 1: Requirements Extraction
        logger.info("-"*80)
        logger.info("STEP 1: Requirements Extraction")
        logger.info("-"*80)
        requirements = await self._extract_requirements(user_input)
        logger.info(f"Requirements extracted: {requirements.get('application_name', 'N/A')}")
        logger.info(f"Components: {len(requirements.get('components', []))}")
        
        # Step 2: Architecture Design
        logger.info("-"*80)
        logger.info("STEP 2: Architecture Design")
        logger.info("-"*80)
        architecture = await self._design_architecture(requirements)
        logger.info(f"Architecture designed: {architecture.get('architecture_name', 'N/A')}")
        logger.info(f"Modules: {len(architecture.get('modules', []))}")
        
        # Step 3: Terraform Code Generation
        logger.info("-"*80)
        logger.info("STEP 3: Terraform Code Generation")
        logger.info("-"*80)
        terraform_code = await self._generate_terraform(architecture)
        logger.info(f"Terraform code generated")
        logger.info(f"Files: {len(terraform_code.get('files', []))}")
        
        # Step 4: Validation Loop
        logger.info("-"*80)
        logger.info("STEP 4: Validation Loop")
        logger.info("-"*80)
        validated_code, validation_results = await self._validation_loop(
            terraform_code, architecture
        )
        
        if validation_results.validation_status == "passed":
            logger.info("✅ Validation PASSED")
        else:
            logger.error(f"❌ Validation FAILED: {validation_results.error_count} errors")
            logger.error("\nErrors:")
            for error in validation_results.errors[:3]:  # Show first 3
                logger.error(f"  - {error.file}: {error.message}")
            logger.error("\n⚠️  Proceeding with documentation generation despite errors...")
        
        # Step 5: Documentation (even if validation failed - document what we have)
        logger.info("\n" + "-" * 80)
        logger.info("STEP 5: Documentation Generation")
        logger.info("-" * 80)
        documentation = await self._generate_documentation(
            architecture, validated_code, validation_results
        )
        logger.info("✅ Documentation generated")
        
        # Save all outputs
        self._save_terraform_files(validated_code)
        saved_docs = save_documentation_to_files(documentation, self.output_dir)
        
        # Count module and environment files
        # Final summary
        logger.info("\n" + "-" * 80)
        logger.info("🎉 GENERATION COMPLETE")
        logger.info("-" * 80)
        logger.info(f"📁 Output directory: {self.output_dir}")
        
        module_count = len(validated_code.get("modules", []))
        env_count = len(validated_code.get("environments", {}))
        
        if module_count > 0:
            logger.info(f"\n📦 Module Structure:")
            logger.info(f"   - Reusable modules: {module_count}")
            for module in validated_code.get("modules", []):
                module_name = module.get("module_name", "unknown")
                logger.info(f"     • modules/{module_name}/")
        
        if env_count > 0:
            logger.info(f"\n🌍 Environments:")
            for env_name in validated_code.get("environments", {}).keys():
                logger.info(f"   - environments/{env_name}/")
        
        logger.info(f"\n📄 Documentation: {len(saved_docs)} files")
        logger.info("-" * 80)
        
        # Final summary
        logger.info("\n" + "-" * 80)
        logger.info("🎉 GENERATION COMPLETE")
        logger.info("-" * 80)
        logger.info(f"📁 Output directory: {self.output_dir}")
        logger.info(f"   - Terraform modules: {module_count}")
        logger.info(f"   - Terraform environments: {env_count}")
        logger.info(f"   - Documentation files: {len(saved_docs)}")
        logger.info("-" * 80)
        
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
        from google.genai import types
        
        query_content = types.Content(
            role="user",
            parts=[types.Part(text=user_input)]
        )
        
        events = []
        async for event in self.requirements_runner.run_async(
            user_id="user",
            session_id="requirements",
            new_message=query_content
        ):
            events.append(event)
        
        # Extract text from events
        response_text = self._extract_response_text(events)
        return parse_requirements(response_text)
    
    async def _design_architecture(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Design architecture from requirements."""
        prompt = f"""Design a GCP infrastructure architecture based on these requirements:

{json.dumps(requirements, indent=2)}

Output the complete architecture specification in JSON format."""
        
        from google.genai import types
        query_content = types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        )
        
        events = []
        async for event in self.architecture_runner.run_async(
            user_id="user",
            session_id="architecture",
            new_message=query_content
        ):
            events.append(event)
        
        response_text = self._extract_response_text(events)
        return parse_architecture(response_text)
    
    async def _generate_terraform(self, architecture: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Terraform code from architecture."""
        prompt = f"""Generate complete Terraform code for this architecture:

{json.dumps(architecture, indent=2)}

Output all Terraform files in JSON format with proper structure."""
        
        from google.genai import types
        query_content = types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        )
        
        # Use shared session_id with validator for validation loop memory
        events = []
        async for event in self.generator_runner.run_async(
            user_id="user",
            session_id="validation_loop",
            new_message=query_content
        ):
            events.append(event)
        
        response_text = self._extract_response_text(events)
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
        
        logger.info(f"\n{'-'*80}")
        logger.info(f"🔍 VALIDATION LOOP (max {self.max_validation_iterations} iterations)")
        logger.info(f"   🧠 Generator & Validator share session 'validation_loop' for memory")
        logger.info(f"{'-'*80}")
        
        while iteration < self.max_validation_iterations:
            iteration += 1
            logger.info(f"\n🔄 Iteration {iteration}/{self.max_validation_iterations}")
            
            # Validate current code
            validation_results = await self._validate_terraform(current_code)
            
            # Check if we should regenerate
            if not should_regenerate(validation_results):
                logger.info(f"\n✅ Validation PASSED on iteration {iteration}!")
                logger.info(f"{'-'*80}")
                return current_code, validation_results
            
            # If this was the last iteration, return anyway
            if iteration >= self.max_validation_iterations:
                logger.warning(f"\n⚠️  Max iterations ({self.max_validation_iterations}) reached. Stopping validation loop.")
                logger.error(f"   Errors remaining: {len(validation_results.errors)}")
                logger.info(f"{'-'*80}")
                return current_code, validation_results
            
            # Generate feedback and regenerate
            logger.error(f"❌ Validation failed with {len(validation_results.errors)} errors.")
            logger.info(f"   Preparing to regenerate code with feedback...")
            feedback = get_feedback_for_regeneration(validation_results)
            
            # Generator session will remember previous attempts and feedback
            regenerate_prompt = f"""The previous Terraform code had validation errors. Please fix them.

VALIDATION FEEDBACK:
{feedback}

Generate corrected Terraform code that addresses all the issues above.
Output the corrected code in JSON format.

Note: You have session memory of previous attempts - use it to avoid repeating the same mistakes."""
            
            from google.genai import types
            query_content = types.Content(
                role="user",
                parts=[types.Part(text=regenerate_prompt)]
            )
            
            # Use shared session_id - generator will remember previous attempts
            events = []
            async for event in self.generator_runner.run_async(
                user_id="user",
                session_id="validation_loop",
                new_message=query_content
            ):
                events.append(event)
            
            response_text = self._extract_response_text(events)
            current_code = parse_generated_terraform(response_text)
        
        # Should not reach here, but just in case
        return current_code, validation_results
    
    async def _validate_terraform(self, terraform_code: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Terraform code."""
        prompt = f"""Validate this Terraform code thoroughly:

{json.dumps(terraform_code, indent=2)}

Provide detailed feedback in JSON format matching the ValidatorOutput schema."""
        
        from google.genai import types
        query_content = types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        )
        
        # Use shared session_id - validator will remember previous validations
        events = []
        async for event in self.validator_runner.run_async(
            user_id="user",
            session_id="validation_loop",
            new_message=query_content
        ):
            events.append(event)
        
        response_text = self._extract_response_text(events)
        return parse_validation_results(response_text)
    
    async def _generate_documentation(
        self,
        architecture: Dict[str, Any],
        terraform_code: Dict[str, Any],
        validation_results: ValidatorOutput
    ) -> DocumentationOutput:
        """Generate documentation."""
        # Convert Pydantic model to dict for JSON serialization
        validation_dict = validation_results.model_dump()
        
        # Create concise summary for documentation
        arch_summary = {
            "name": architecture.get("architecture_name", "Infrastructure"),
            "modules": [m.get("module_name") for m in architecture.get("modules", [])],
            "environment": architecture.get("environment", "production")
        }
        
        prompt = f"""Generate a README.md for this Terraform infrastructure.

Architecture: {arch_summary['name']}
Modules: {', '.join(arch_summary['modules'])}
Environment: {arch_summary['environment']}

Output ONLY markdown content (no JSON, no code blocks).
Start with # title and include: Overview, Architecture, Prerequisites, Deployment Steps, Configuration.
Keep it under 500 words."""
        
        from google.genai import types
        query_content = types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        )
        
        events = []
        async for event in self.documentation_runner.run_async(
            user_id="user",
            session_id="documentation",
            new_message=query_content
        ):
            events.append(event)
        
        # Extract text from events
        response_text = self._extract_response_text(events)
        
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
                
                # Try to find JSON object anywhere in the text
                json_start_idx = combined.find('{')
                if json_start_idx >= 0:
                    # Find the matching closing brace
                    brace_count = 0
                    for i in range(json_start_idx, len(combined)):
                        if combined[i] == '{':
                            brace_count += 1
                        elif combined[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                potential_json = combined[json_start_idx:i+1]
                                # Quick validation - try to parse it
                                try:
                                    json.loads(potential_json)
                                    return potential_json
                                except:
                                    pass
                                break
                
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
