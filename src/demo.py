"""
Demo Script

Interactive demonstration of the Terraform Generator Multi-Agent System.
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file BEFORE importing anything else
load_dotenv()

from src.orchestrator import TerraformGeneratorOrchestrator


# Example scenarios for demonstration
EXAMPLE_SCENARIOS = {
    "1": {
        "name": "Simple Web App",
        "description": """
Create a simple web application with:
- Cloud Run service for a containerized API
- Cloud SQL PostgreSQL database
- Cloud Storage for static assets
Deploy in us-central1 region.
"""
    },
    "2": {
        "name": "Microservices Application",
        "description": """
Create a microservices architecture with:
- GKE cluster for container orchestration
- Cloud SQL for the main database
- Cloud Memorystore (Redis) for caching
- Cloud Pub/Sub for message queuing
- Load balancer for external traffic
- VPC with private subnets
Deploy across multiple zones for high availability.
"""
    },
    "3": {
        "name": "Data Pipeline",
        "description": """
Create a data processing pipeline with:
- Cloud Storage buckets for raw data input and processed output
- Cloud Functions for data transformation
- BigQuery for data warehousing
- Cloud Scheduler for scheduled jobs
- Pub/Sub for event-driven processing
Include proper IAM roles for service accounts.
"""
    },
    "4": {
        "name": "ML Training Platform",
        "description": """
Create an ML training platform with:
- Vertex AI Workbench for development
- Cloud Storage for datasets and models
- Compute Engine GPU instances for training
- Cloud SQL for metadata storage
- VPC with firewall rules
Include Cloud Monitoring for resource tracking.
"""
    },
    "5": {
        "name": "Custom (Enter your own)",
        "description": None  # User will provide their own
    }
}


def print_banner():
    """Print welcome banner."""
    print("\n" + "=" * 80)
    print("🚀 TERRAFORM GENERATOR MULTI-AGENT SYSTEM - DEMO")
    print("=" * 80)
    print("\nThis demo showcases a sophisticated multi-agent system that generates")
    print("production-ready Terraform code for Google Cloud Platform infrastructure")
    print("from natural language descriptions.")
    print("\n🤖 Agent Architecture:")
    print("  1. Requirements Extraction Agent - Parses user requirements")
    print("  2. Architecture Design Agent - Designs GCP infrastructure")
    print("  3. Terraform Generator Agent - Generates Terraform code")
    print("  4. Validator/Critic Agent - Validates and provides feedback")
    print("  5. Documentation Agent - Creates comprehensive documentation")
    print("=" * 80 + "\n")


def display_scenarios():
    """Display available scenarios."""
    print("\n📋 Available Scenarios:")
    print("-" * 80)
    for key, scenario in EXAMPLE_SCENARIOS.items():
        if scenario['description']:
            # Clean up description and show all bullet points
            description = scenario['description'].strip()
            lines = description.split('\n')
            print(f"{key}. {scenario['name']}")
            for line in lines:
                line = line.strip()
                if line:
                    print(f"   {line}")
        else:
            # For custom option with no description
            print(f"{key}. {scenario['name']}")
        print()  # Add blank line between scenarios
    print("-" * 80)


def get_user_input() -> str:
    """Get infrastructure description from user."""
    display_scenarios()
    
    while True:
        choice = input("\n👉 Select a scenario (1-5) or 'q' to quit: ").strip()
        
        if choice.lower() == 'q':
            print("👋 Goodbye!")
            exit(0)
        
        if choice in EXAMPLE_SCENARIOS:
            scenario = EXAMPLE_SCENARIOS[choice]
            print(f"\n✅ Selected: {scenario['name']}")
            
            if scenario['description'] is None:
                # Custom scenario
                print("\n📝 Enter your infrastructure description:")
                print("(Press Enter twice when done)\n")
                lines = []
                while True:
                    line = input()
                    if line == "" and len(lines) > 0 and lines[-1] == "":
                        break
                    lines.append(line)
                description = '\n'.join(lines[:-1])  # Remove last empty line
            else:
                description = scenario['description']
                print(f"\n📝 Description:\n{description}")
            
            # Confirm
            confirm = input("\n👉 Proceed with this scenario? (y/n): ").strip().lower()
            if confirm == 'y':
                return description
            else:
                print("↩️  Let's try again...")
                continue
        else:
            print("❌ Invalid choice. Please select 1-5 or 'q' to quit.")


async def run_demo():
    """Run the interactive demo."""
    print_banner()
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  Warning: GOOGLE_API_KEY environment variable not set.")
        print("Please set your Gemini API key:")
        print("  export GOOGLE_API_KEY='your-api-key-here'")
        print("\nYou can get an API key from: https://aistudio.google.com/app/api-keys")
        return
    
    # Get user input
    user_description = get_user_input()
    
    # Create output directory with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"./output/output_{timestamp}"
    
    print(f"\n📁 Output directory: {output_dir}")
    print("\n🚀 Starting generation process...\n")
    
    # Run the orchestrator
    try:
        orchestrator = TerraformGeneratorOrchestrator(
            output_dir=output_dir,
            max_validation_iterations=20
        )
        results = await orchestrator.run(user_description)
        
        # Display summary
        print("\n" + "=" * 80)
        print("📊 GENERATION SUMMARY")
        print("=" * 80)
        
        # Requirements summary
        req = results['requirements']
        print(f"\n✅ Requirements:")
        print(f"   Application: {req.get('application_name', 'N/A')}")
        print(f"   Components: {len(req.get('components', []))}")
        print(f"   Environment: {req.get('environment', 'N/A')}")
        
        # Architecture summary
        arch = results['architecture']
        print(f"\n✅ Architecture:")
        print(f"   Name: {arch.get('architecture_name', 'N/A')}")
        print(f"   Modules: {len(arch.get('modules', []))}")
        
        # Terraform summary
        tf = results['terraform_code']
        print(f"\n✅ Terraform Code:")
        # Count modules and environment files
        module_count = len(tf.get('modules', []))
        env_count = len(tf.get('environments', {}))
        # Count total .tf files
        total_files = 0
        for module in tf.get('modules', []):
            total_files += len(module.get('files', []))
        for env_config in tf.get('environments', {}).values():
            # Count each environment config file (main, variables, outputs, provider)
            total_files += sum(1 for key in ['main_tf', 'variables_tf', 'outputs_tf', 'provider_tf', 'terraform_tfvars_example'] if key in env_config)
        print(f"   Modules: {module_count}")
        print(f"   Environments: {env_count}")
        print(f"   Total .tf files: {total_files}")
        
        # Validation summary
        val = results['validation_results']
        print(f"\n✅ Validation:")
        print(f"   Status: {val.validation_status}")
        print(f"   Errors: {val.error_count}")
        if val.error_count > 0:
            print(f"   Summary: {val.summary}")
        
        # Documentation summary
        print(f"\n✅ Documentation:")
        print(f"   README.md generated")
        if val.error_count > 0:
            print(f"\n⚠️  Warning: Validation found {val.error_count} errors")
            print(f"   Please review the generated code before deploying")
        
        print("\n" + "=" * 80)
        print(f"🎉 Success! All files saved to: {output_dir}")
        print("=" * 80)
        
        # Next steps
        print("\n📋 Next Steps:")
        print(f"   1. Review the generated files in {output_dir}")
        print(f"   2. Read the README.md for deployment instructions")
        print(f"   3. Customize variables in terraform.tfvars")
        print(f"   4. Run 'terraform init' and 'terraform plan'")
        print(f"   5. Deploy with 'terraform apply'")
        
    except Exception as e:
        print(f"\n❌ Error during generation: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point."""
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
