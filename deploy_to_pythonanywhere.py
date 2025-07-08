#!/usr/bin/env python3
"""
Deployment preparation script for PythonAnywhere
This script helps prepare your Flask app for PythonAnywhere deployment
"""

import os
import shutil
import zipfile
from pathlib import Path

def create_deployment_package():
    """Create a deployment package excluding unnecessary files"""
    
    # Define the source directory
    source_dir = Path(__file__).parent
    
    # Define what to exclude
    exclude_patterns = [
        'kibs-ims',  # Virtual environment
        '__pycache__',
        '*.pyc',
        '.git',
        '.gitignore',
        'node_modules',
        '.env',
        'venv',
        'env',
        '.vscode',
        '.idea',
        'deploy_to_pythonanywhere.py'
    ]
    
    # Define what to include (essential files)
    include_files = [
        'app/',
        'routes/',
        'migrations/',
        'static/',
        'wsgi.py',
        'run.py',
        'requirements.txt',
        'create_tables.sql',
        'migrate_pythonanywhere.py'
    ]
    
    # Create deployment directory
    deploy_dir = source_dir / 'deployment_package'
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)
    deploy_dir.mkdir()
    
    print("Creating deployment package...")
    
    # Copy essential files and directories
    for item in include_files:
        src_path = source_dir / item
        if src_path.exists():
            if src_path.is_dir():
                shutil.copytree(src_path, deploy_dir / item, 
                              ignore=shutil.ignore_patterns(*exclude_patterns))
            else:
                shutil.copy2(src_path, deploy_dir / item)
            print(f"[OK] Copied {item}")
        else:
            print(f"[WARNING] {item} not found")
    
    # Create a zip file for easy upload
    zip_path = source_dir / 'kibs_backend_deployment.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(deploy_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(deploy_dir)
                zipf.write(file_path, arcname)
    
    print(f"\n[OK] Deployment package created: {zip_path}")
    print(f"[OK] Package size: {zip_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    return zip_path

if __name__ == "__main__":
    create_deployment_package()
    print("\nNext steps:")
    print("1. Upload the zip file to PythonAnywhere")
    print("2. Extract it in your home directory")
    print("3. Install requirements: pip3.10 install --user -r requirements.txt")
    print("4. Configure your web app to use wsgi.py")