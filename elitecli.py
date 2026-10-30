#!/usr/bin/env python3
"""
EliteHosting CLI Tool (elitecli)
Seamlessly deploy your Python, Node.js, and Telegram bots to elitehosting.in
"""

import os
import sys
import zipfile
import argparse
import requests
from pathlib import Path

API_BASE_URL = "https://elitehosting.in/api/v1"
CONFIG_FILE = Path.home() / ".eliteconfig"

def zip_directory(path: Path, output_filename: str) -> str:
    """Compress the current directory into a zip file excluding unnecessary files."""
    exclude_dirs = {'.git', 'node_modules', '__pycache__', 'venv', '.env', 'dist', 'build'}
    exclude_extensions = {'.zip', '.log'}

    print(f"📦 Packaging project directory: {path.resolve()} ...")
    
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(path):
            # Modify dirs in-place to skip unwanted directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in exclude_extensions or file_path.name == output_filename:
                    continue
                
                arcname = file_path.relative_to(path)
                zipf.write(file_path, arcname)
                
    print(f"✅ Successfully packaged into {output_filename}")
    return output_filename

def handle_login(args):
    """Authenticate and save token locally."""
    print(f"🔑 Authenticating with EliteHosting using token: {args.token[:6]}...")
    try:
        response = requests.post(f"{API_BASE_URL}/auth", json={"token": args.token}, timeout=10)
        if response.status_code == 200:
            CONFIG_FILE.write_text(args.token)
            print("🎉 Authentication successful! Credentials saved.")
        else:
            print(f"❌ Authentication failed: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")

def handle_deploy(args):
    """Deploy the current directory project."""
    if not CONFIG_FILE.exists():
        print("❌ Not authenticated. Please run: elite login --token <YOUR_API_TOKEN>")
        sys.exit(1)
        
    api_token = CONFIG_FILE.read_text().strip()
    project_dir = Path.cwd()
    
    zip_filename = "deployment_payload.zip"
    try:
        zip_path = zip_directory(project_dir, zip_filename)
        
        print("🚀 Uploading and deploying to EliteHosting servers...")
        headers = {"Authorization": f"Bearer {api_token}"}
        
        with open(zip_path, 'rb') as f:
            files = {'file': (zip_filename, f, 'application/zip')}
            data = {'app_name': args.name or project_dir.name}
            
            response = requests.post(f"{API_BASE_URL}/deploy", headers=headers, data=data, files=files, timeout=60)
            
        if response.status_code == 200:
            res_data = response.json()
            print("\n✨ Deployment Successful!")
            print(f"🌍 Live URL: {res_data.get('url', 'https://elitehosting.in/dashboard')}")
        else:
            print(f"\n❌ Deployment failed ({response.status_code}): {response.text}")
            
    finally:
        # Clean up temporary zip file
        if os.path.exists(zip_filename):
            os.remove(zip_filename)

def main():
    parser = argparse.ArgumentParser(
        description="EliteHosting CLI - Instant Cloud & Telegram Bot Deployment tool."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Login sub-command
    login_parser = subparsers.add_parser("login", help="Authenticate with your EliteHosting token")
    login_parser.add_argument("--token", required=True, help="Your API access token from elitehosting.in")
    login_parser.add_argument("--token", required=True, help="Your API access token from elitehosting.in")

    # Deploy sub-command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy current folder to EliteHosting")
    deploy_parser.add_argument("--name", help="Custom application or bot name", default=None)

    args = parser.parse_args()

    if args.command == "login":
        handle_login(args)
    elif args.command == "deploy":
        handle_deploy(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
