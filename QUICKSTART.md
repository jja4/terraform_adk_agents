# Quick Start Guide

Get started with the Terraform Generator Multi-Agent System in 5 minutes!

## Prerequisites

1. **Python 3.10+** installed
2. **[uv](https://docs.astral.sh/uv/)** - Fast Python package installer
3. **Gemini API Key** - Get one from [Google AI Studio](https://aistudio.google.com/app/api-keys)
4. **Google Cloud Project ID** - Create a new project for testing at [Google Cloud Console](https://console.cloud.google.com/)
5. **Terminal access**

## Installation

```bash
# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Navigate to the project
cd /Users/macos/Code/terraform-generator-agents

# Install dependencies (creates .venv automatically)
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

## Run the Demo

```bash
uv run src/demo.py
```

The interactive demo will guide you through:
1. Selecting a pre-built scenario or entering your own
2. Watching the agents work together
3. Generating complete Terraform infrastructure code
4. Reviewing the output files

## Example: Generate a Web App

```python
# Or run directly with Python
import asyncio
from orchestrator import main

user_input = """
Create a web application with:
- Cloud Run service for the backend API
- Cloud SQL PostgreSQL database
- Cloud Storage bucket for uploads
"""

asyncio.run(main(user_input))
```

## What You'll Get

After running the demo, check the `output/` directory:

```
output/demo_TIMESTAMP/
├── modules/                    # Reusable Terraform modules
│   ├── vpc/
│   ├── cloud_run/
│   └── cloud_sql/
│
├── environments/prod/          # Environment configuration
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── provider.tf
│   └── terraform.tfvars.example
│
└── README.md                   # Generated documentation
```

## Deploy Your Infrastructure

```bash
cd output/demo_TIMESTAMP/environments/prod

# Copy and edit variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your GCP project values

# Initialize and deploy
terraform init
terraform plan
terraform apply
```

## Common Issues

### API Key Not Set
```
⚠️  Warning: GOOGLE_API_KEY environment variable not set.
```
**Solution**: 
```bash
# Option 1: Add to .env file (recommended)
echo "GOOGLE_API_KEY=your-key-here" >> .env

# Option 2: Export in terminal
export GOOGLE_API_KEY="your-key"
```

### Terraform Not Found
```
terraform CLI not found
```
**Solution**: Install Terraform from [terraform.io](https://www.terraform.io/downloads)

### Rate Limits
If you hit API rate limits, the agents will automatically retry with exponential backoff.

## Architecture Overview

The system uses 5 specialized agents:

```
User Input → Requirements Agent → Architecture Agent → 
Generator Agent → Validator Agent → Documentation Agent
                         ↑              ↓
                         └──── feedback loop
```

## Learn More

- [Full README](README.md) - Complete project documentation
- [Google ADK Docs](https://google.github.io/adk-docs/) - ADK reference

---

**Ready to generate infrastructure? Run `uv run src/demo.py`!** 🚀
