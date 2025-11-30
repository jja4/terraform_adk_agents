# Security

## Overview

This project is designed to be **safe by default** - it generates Terraform code but **never executes infrastructure changes** on your behalf.

## What This System Does

✅ **Safe Operations:**
- Parses natural language descriptions
- Generates Terraform `.tf` files
- Formats code with `terraform fmt` (local operation, no cloud access)
- Validates syntax with `terraform validate` (local operation, no cloud access)  
- Runs `terraform plan` (dry-run only, no infrastructure changes)
- Creates documentation

❌ **What It NEVER Does:**
- Execute `terraform apply` (no actual infrastructure deployment)
- Access your GCP account or credentials
- Make any changes to your cloud infrastructure
- Store or transmit sensitive data

## Tool Safety Analysis

### Terraform Tools (`src/tools/terraform_tools.py`)

| Tool | What It Does | Requires Credentials? | Makes Cloud Changes? |
|------|--------------|----------------------|---------------------|
| `terraform_fmt` | Formats code locally in temp directory | ❌ No | ❌ No |
| `terraform_validate` | Validates syntax locally | ❌ No | ❌ No |
| `terraform_plan` | Dry-run simulation | ❌ No | ❌ No |
| `check_terraform_syntax` | Basic syntax checks in Python | ❌ No | ❌ No |

**All operations use temporary directories that are automatically cleaned up.**

### GCloud Tools (`src/tools/gcloud_tools.py`)

| Tool | What It Does | Requires Credentials? | Makes Cloud Changes? |
|------|--------------|----------------------|---------------------|
| `check_gcp_service_availability` | Returns mock/hardcoded data | ❌ No | ❌ No |
| `list_available_regions` | Returns mock/hardcoded data | ❌ No | ❌ No |
| `validate_service_compatibility` | Returns mock/hardcoded data | ❌ No | ❌ No |

**Note:** The gcloud tools currently return mock data and do NOT make actual API calls. They simulate service checks for the agents to make informed architecture decisions.

## Credentials

### What You Need

- **Gemini API Key** (`GOOGLE_API_KEY`) - For the LLM agents only
[API key in Google AI Studio](https://aistudio.google.com/app/api-keys)

- **GCP Project ID** (`GOOGLE_CLOUD_PROJECT`) - Used in generated Terraform code as a variable

### What You DON'T Need

- ❌ GCP service account keys
- ❌ GCP application default credentials  
- ❌ Terraform backend credentials
- ❌ Cloud SQL passwords (used only in generated code examples)

## Generated Code Safety

The generated Terraform code is **your responsibility** to review and test before deploying:

1. **Review All Generated Files** - Check every `.tf` file for correctness
2. **Verify Variables** - Ensure `terraform.tfvars` contains appropriate values
3. **Run Plan First** - Always run `terraform plan` before `apply`
4. **Test in Isolation** - Deploy to a test GCP project first (see [TESTING.md](TESTING.md))
5. **Understand Resources** - Know what infrastructure will be created
6. **Check Costs** - Review GCP pricing for the resources being created

⚠️ **Important:** The system validates syntax and structure but does NOT test actual deployment. See [TESTING.md](TESTING.md) for recommended testing strategies.

## Deployment Safety Checklist

Before running `terraform apply` on generated code:

- [ ] Reviewed all `.tf` files in `modules/` and `environments/`
- [ ] Checked `terraform.tfvars` values are correct
- [ ] Ran `terraform plan` and reviewed the output
- [ ] **Tested in isolated test GCP project** (strongly recommended - see [TESTING.md](TESTING.md))
- [ ] Understand what resources will be created
- [ ] Verified the GCP project ID is correct
- [ ] Confirmed you have appropriate GCP permissions
- [ ] Considered cost implications
- [ ] Have a rollback plan (`terraform destroy`)

## Best Practices

### Environment Isolation

```bash
# Use separate GCP projects for generated test infrastructure
export GOOGLE_CLOUD_PROJECT="my-test-project-id"  # NOT production!

# Generate code
uv run src/demo.py

# Review before deploying
cd output/demo_TIMESTAMP/environments/prod
terraform plan
```

### Credential Management
[API key in Google AI Studio](https://aistudio.google.com/app/api-keys)

```bash
# Only set what's needed for generation
export GOOGLE_API_KEY="your-gemini-api-key"
export GOOGLE_CLOUD_PROJECT="test-project-123"

# Don't set these (not needed for generation):
# export GOOGLE_APPLICATION_CREDENTIALS="..." 
# export GOOGLE_CREDENTIALS="..."
```
[API key in Google AI Studio](https://aistudio.google.com/app/api-keys)
### Code Review

Always review generated code:

```bash
# Check what modules were created
ls -R output/demo_TIMESTAMP/modules/

# Review the main environment configuration
cat output/demo_TIMESTAMP/environments/prod/main.tf

# Look for sensitive values
grep -r "password\|secret\|key" output/demo_TIMESTAMP/
```

## Limitations

### Mock Data

The gcloud tools currently return **mock data** rather than making real API calls:

- Service availability checks return hardcoded common services
- Region lists return predefined common regions
- Compatibility checks use hardcoded rules

**Why?** This approach is safer and doesn't require GCP credentials during code generation.

**Future Enhancement:** Could be updated to make real `gcloud` API calls if credentials are available, but would remain read-only operations.

### Terraform Commands

Terraform commands run in isolated temporary directories:

- `terraform init` downloads providers locally
- `terraform validate` checks syntax only
- `terraform plan` simulates changes (read-only, no state file needed)

These commands **cannot** make infrastructure changes without:
1. Running `terraform apply` (which this system never does)
2. Having valid GCP credentials configured
3. Having appropriate IAM permissions

## Reporting Security Issues

If you discover a security issue:

1. **Do NOT** open a public GitHub issue
2. Email the maintainers privately
3. Include reproduction steps and impact assessment

## Additional Resources

- [Terraform Security Best Practices](https://developer.hashicorp.com/terraform/tutorials/configuration-language/sensitive-variables)
- [GCP Security Best Practices](https://cloud.google.com/security/best-practices)
- [Least Privilege IAM](https://cloud.google.com/iam/docs/using-iam-securely)
