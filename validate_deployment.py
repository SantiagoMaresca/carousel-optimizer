#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pre-deployment validation script for Carousel Optimizer.
Run this before deploying to catch common issues.
"""

import os
import sys
from pathlib import Path
import json

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_mark(success):
    """Return check mark or X based on success."""
    return "[OK]" if success else "[FAIL]"

def check_file_exists(filepath, description):
    """Check if a file exists."""
    exists = Path(filepath).exists()
    print(f"{check_mark(exists)} {description}: {filepath}")
    return exists

def check_env_file(filepath, required_vars):
    """Check if environment file has required variables."""
    if not Path(filepath).exists():
        print(f"[FAIL] Environment file not found: {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    missing = []
    for var in required_vars:
        if var not in content:
            missing.append(var)
    
    if missing:
        print(f"[FAIL] {filepath} missing variables: {', '.join(missing)}")
        return False
    else:
        print(f"[OK] {filepath} has all required variables")
        return True

def check_json_valid(filepath):
    """Check if JSON file is valid."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            json.load(f)
        print(f"[OK] Valid JSON: {filepath}")
        return True
    except json.JSONDecodeError as e:
        print(f"[FAIL] Invalid JSON in {filepath}: {e}")
        return False
    except FileNotFoundError:
        print(f"[FAIL] File not found: {filepath}")
        return False

def main():
    """Run all pre-deployment checks."""
    print("Pre-Deployment Validation for Carousel Optimizer\n")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    all_checks_passed = True
    
    # Check deployment configuration files
    print("\n[Deployment Configuration Files]")
    print("-" * 60)
    
    checks = [
        (base_dir / "render.yaml", "Render configuration"),
        (base_dir / "railway.json", "Railway configuration"),
        (base_dir / "backend" / "Procfile", "Backend Procfile"),
        (base_dir / "backend" / "nixpacks.toml", "Nixpacks configuration"),
        (base_dir / "frontend" / "vercel.json", "Vercel configuration"),
    ]
    
    for filepath, description in checks:
        if not check_file_exists(filepath, description):
            all_checks_passed = False
    
    # Check JSON files are valid
    print("\n[JSON Configuration Validation]")
    print("-" * 60)
    
    json_files = [
        base_dir / "railway.json",
        base_dir / "frontend" / "vercel.json",
        base_dir / "frontend" / "package.json",
    ]
    
    for filepath in json_files:
        if filepath.exists():
            if not check_json_valid(filepath):
                all_checks_passed = False
    
    # Check environment files
    print("\n[Environment Configuration]")
    print("-" * 60)
    
    backend_env_vars = [
        "ENVIRONMENT",
        "DEBUG",
        "UPLOAD_DIRECTORY",
        "CORS_ORIGINS"
    ]
    
    frontend_env_vars = [
        "VITE_API_URL"
    ]
    
    if not check_env_file(base_dir / "backend" / ".env.production", backend_env_vars):
        all_checks_passed = False
    
    if not check_env_file(base_dir / "frontend" / ".env.production", frontend_env_vars):
        all_checks_passed = False
    
    # Check required Python files
    print("\n[Backend Files]")
    print("-" * 60)
    
    backend_files = [
        (base_dir / "backend" / "requirements.txt", "Requirements file"),
        (base_dir / "backend" / "app" / "main.py", "Main application"),
        (base_dir / "backend" / "app" / "config.py", "Configuration"),
        (base_dir / "backend" / "run.py", "Run script"),
    ]
    
    for filepath, description in backend_files:
        if not check_file_exists(filepath, description):
            all_checks_passed = False
    
    # Check frontend files
    print("\n[Frontend Files]")
    print("-" * 60)
    
    frontend_files = [
        (base_dir / "frontend" / "package.json", "Package configuration"),
        (base_dir / "frontend" / "index.html", "HTML entry point"),
        (base_dir / "frontend" / "src" / "main.jsx", "React entry point"),
        (base_dir / "frontend" / "vite.config.js", "Vite configuration"),
    ]
    
    for filepath, description in frontend_files:
        if not check_file_exists(filepath, description):
            all_checks_passed = False
    
    # Check for placeholder URLs that need updating
    print("\n[Configuration Warnings]")
    print("-" * 60)
    
    # Check backend .env.production
    backend_env_path = base_dir / "backend" / ".env.production"
    if backend_env_path.exists():
        with open(backend_env_path, 'r') as f:
            backend_env = f.read()
        
        if "your-frontend.vercel.app" in backend_env:
            print("[WARN] Backend CORS_ORIGINS contains placeholder URL")
            print("       Update after deploying frontend")
        else:
            print("[OK] Backend CORS_ORIGINS updated")
    
    # Check frontend .env.production
    frontend_env_path = base_dir / "frontend" / ".env.production"
    if frontend_env_path.exists():
        with open(frontend_env_path, 'r') as f:
            frontend_env = f.read()
        
        if "your-backend.onrender.com" in frontend_env:
            print("[WARN] Frontend VITE_API_URL contains placeholder URL")
            print("       Update after deploying backend")
        else:
            print("[OK] Frontend VITE_API_URL updated")
    
    # Summary
    print("\n" + "=" * 60)
    if all_checks_passed:
        print("[SUCCESS] All checks passed! Ready to deploy.")
        print("\nNext steps:")
        print("1. Push code to GitHub")
        print("2. Follow DEPLOYMENT_CHECKLIST.md")
        print("3. Deploy backend first (get URL)")
        print("4. Update frontend VITE_API_URL with backend URL")
        print("5. Deploy frontend (get URL)")
        print("6. Update backend CORS_ORIGINS with frontend URL")
        return 0
    else:
        print("[FAILED] Some checks failed. Please fix the issues above.")
        print("\nRefer to DEPLOYMENT_GUIDE_CLOUD.md for help.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
