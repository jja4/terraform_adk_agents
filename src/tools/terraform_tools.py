"""
Terraform Tools

Tools for Terraform code formatting, validation, and planning.
"""

import subprocess
import os
import tempfile
from typing import Dict, Optional


def terraform_fmt(code: str) -> Dict:
    """
    Format Terraform code using terraform fmt.
    
    Args:
        code: Raw Terraform code as a string
        
    Returns:
        Dictionary with formatted code and status
    """
    try:
        # Create a temporary directory for the terraform file
        with tempfile.TemporaryDirectory() as tmpdir:
            tf_file = os.path.join(tmpdir, "main.tf")
            
            # Write code to file
            with open(tf_file, 'w') as f:
                f.write(code)
            
            # Run terraform fmt
            result = subprocess.run(
                ["terraform", "fmt", tf_file],
                capture_output=True,
                text=True,
                cwd=tmpdir
            )
            
            # Read formatted code
            with open(tf_file, 'r') as f:
                formatted_code = f.read()
            
            return {
                "status": "success",
                "formatted_code": formatted_code,
                "message": "Code formatted successfully"
            }
            
    except FileNotFoundError:
        return {
            "status": "error",
            "error_message": "terraform CLI not found. Please install Terraform.",
            "formatted_code": code  # Return original code
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Formatting failed: {str(e)}",
            "formatted_code": code  # Return original code
        }


def terraform_validate(code: str, module_name: str = "main") -> Dict:
    """
    Validate Terraform configuration using terraform validate.
    
    Args:
        code: Terraform code as a string
        module_name: Name of the module being validated
        
    Returns:
        Dictionary with validation results
    """
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tf_file = os.path.join(tmpdir, f"{module_name}.tf")
            
            # Write code to file
            with open(tf_file, 'w') as f:
                f.write(code)
            
            # Initialize terraform
            init_result = subprocess.run(
                ["terraform", "init"],
                capture_output=True,
                text=True,
                cwd=tmpdir
            )
            
            if init_result.returncode != 0:
                return {
                    "status": "error",
                    "valid": False,
                    "error_message": f"Terraform init failed: {init_result.stderr}",
                    "errors": [init_result.stderr]
                }
            
            # Validate
            validate_result = subprocess.run(
                ["terraform", "validate", "-json"],
                capture_output=True,
                text=True,
                cwd=tmpdir
            )
            
            if validate_result.returncode == 0:
                return {
                    "status": "success",
                    "valid": True,
                    "message": "Configuration is valid",
                    "errors": []
                }
            else:
                return {
                    "status": "error",
                    "valid": False,
                    "error_message": validate_result.stderr,
                    "errors": [validate_result.stderr]
                }
                
    except FileNotFoundError:
        return {
            "status": "error",
            "valid": False,
            "error_message": "terraform CLI not found. Please install Terraform.",
            "errors": []
        }
    except Exception as e:
        return {
            "status": "error",
            "valid": False,
            "error_message": f"Validation failed: {str(e)}",
            "errors": [str(e)]
        }


def terraform_plan(code: str, var_file: Optional[str] = None) -> Dict:
    """
    Run terraform plan to check what would be created.
    
    Args:
        code: Terraform code as a string
        var_file: Optional variables file content
        
    Returns:
        Dictionary with plan results
    """
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tf_file = os.path.join(tmpdir, "main.tf")
            
            # Write main code
            with open(tf_file, 'w') as f:
                f.write(code)
            
            # Write variables file if provided
            if var_file:
                vars_file = os.path.join(tmpdir, "terraform.tfvars")
                with open(vars_file, 'w') as f:
                    f.write(var_file)
            
            # Initialize
            init_result = subprocess.run(
                ["terraform", "init"],
                capture_output=True,
                text=True,
                cwd=tmpdir
            )
            
            if init_result.returncode != 0:
                return {
                    "status": "error",
                    "plan_success": False,
                    "error_message": f"Terraform init failed: {init_result.stderr}",
                    "plan_output": ""
                }
            
            # Plan (dry-run, no actual infrastructure changes)
            plan_result = subprocess.run(
                ["terraform", "plan", "-no-color"],
                capture_output=True,
                text=True,
                cwd=tmpdir
            )
            
            return {
                "status": "success" if plan_result.returncode == 0 else "error",
                "plan_success": plan_result.returncode == 0,
                "plan_output": plan_result.stdout,
                "error_message": plan_result.stderr if plan_result.returncode != 0 else ""
            }
            
    except FileNotFoundError:
        return {
            "status": "error",
            "plan_success": False,
            "error_message": "terraform CLI not found. Please install Terraform.",
            "plan_output": ""
        }
    except Exception as e:
        return {
            "status": "error",
            "plan_success": False,
            "error_message": f"Plan failed: {str(e)}",
            "plan_output": ""
        }


def check_terraform_syntax(code: str) -> Dict:
    """
    Basic syntax check for Terraform code without running terraform CLI.
    Checks for common syntax errors.
    
    Args:
        code: Terraform code as a string
        
    Returns:
        Dictionary with syntax check results
    """
    errors = []
    
    # Basic syntax checks
    lines = code.split('\n')
    
    # Check for balanced braces
    open_braces = code.count('{')
    close_braces = code.count('}')
    if open_braces != close_braces:
        errors.append(f"Unbalanced braces: {open_braces} opening, {close_braces} closing")
    
    # Check for balanced brackets
    open_brackets = code.count('[')
    close_brackets = code.count(']')
    if open_brackets != close_brackets:
        errors.append(f"Unbalanced brackets: {open_brackets} opening, {close_brackets} closing")
    
    # Check for balanced quotes (simple check)
    quote_count = code.count('"')
    if quote_count % 2 != 0:
        errors.append("Unmatched quotes detected")
    
    # Check for required blocks
    if 'resource' not in code and 'module' not in code and 'data' not in code:
        errors.append("No resource, module, or data blocks found")
    
    if errors:
        return {
            "status": "error",
            "valid": False,
            "errors": errors,
            "message": "Syntax errors detected"
        }
    else:
        return {
            "status": "success",
            "valid": True,
            "errors": [],
            "message": "Basic syntax check passed"
        }
