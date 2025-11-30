# Security

## Overview

This project is designed to be **safe by default** - it generates Terraform code but **never executes infrastructure changes** on your behalf.

## What This System Does

✅ **Safe Operations:**
- Parses natural language descriptions
- Generates Terraform `.tf` files
- Validates code syntax and structure
- Creates documentation

❌ **What It NEVER Does:**
- Execute `terraform apply` (no actual infrastructure deployment)
- Access your GCP account or credentials
- Make any changes to your cloud infrastructure
- Store or transmit sensitive data

## Credentials

### What You Need

- **Gemini API Key** (`GOOGLE_API_KEY`) - For LLM agents ([Get from Google AI Studio](https://aistudio.google.com/app/api-keys))
- **GCP Project ID** (`GOOGLE_CLOUD_PROJECT`) - Used in generated Terraform code

### What You DON'T Need

- ❌ GCP service account keys
- ❌ GCP application default credentials
- ❌ Terraform backend credentials

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

```bash
# Only set what's needed for generation
export GOOGLE_API_KEY="your-gemini-api-key"
export GOOGLE_CLOUD_PROJECT="test-project-123"
```
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

## Reporting Security Issues

If you discover a security issue:

1. **Do NOT** open a public GitHub issue
2. Email the maintainers privately
3. Include reproduction steps and impact assessment

## Additional Resources

- [Terraform Security Best Practices](https://developer.hashicorp.com/terraform/tutorials/configuration-language/sensitive-variables)
- [GCP Security Best Practices](https://cloud.google.com/security/best-practices)
- [Least Privilege IAM](https://cloud.google.com/iam/docs/using-iam-securely)
