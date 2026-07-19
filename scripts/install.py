#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import shutil

def check_requirements():
    print("Checking system requirements...")
    
    # Check Python version
    python_ver = sys.version_info
    if python_ver.major < 3 or (python_ver.major == 3 and python_ver.minor < 8):
        print(f"❌ Error: Python 3.8+ is required. Found Python {platform.python_version()}")
        sys.exit(1)
    print(f"✔ Python {platform.python_version()}")

    # Check Node.js version
    try:
        node_ver_raw = subprocess.check_output(["node", "--version"], text=True).strip()
        print(f"✔ Node.js {node_ver_raw}")
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("❌ Error: Node.js is not installed or not in PATH.")
        sys.exit(1)

    # Check npm
    try:
        npm_ver_raw = subprocess.check_output(["npm", "--version"], text=True).strip()
        print(f"✔ npm {npm_ver_raw}")
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("❌ Error: npm is not installed or not in PATH.")
        sys.exit(1)

def setup_venv():
    print("\\nSetting up Python virtual environment...")
    api_dir = "apps/api"
    venv_dir = os.path.join(api_dir, "venv")
    
    if not os.path.exists(venv_dir):
        print("Creating virtual environment...")
        subprocess.check_call([sys.executable, "-m", "venv", venv_dir])
        print("✔ Virtual environment created.")
    else:
        print("✔ Virtual environment already exists.")
        
    # Determine pip path
    if platform.system() == "Windows":
        pip_path = os.path.join(venv_dir, "Scripts", "pip")
    else:
        pip_path = os.path.join(venv_dir, "bin", "pip")
        
    # Upgrade pip and setuptools
    print("Upgrading pip and setuptools...")
    subprocess.check_call([pip_path, "install", "--upgrade", "pip", "setuptools"])
    
    # Install backend dependencies
    req_path = os.path.join(api_dir, "requirements.txt")
    print(f"Installing backend dependencies from {req_path}...")
    subprocess.check_call([pip_path, "install", "-r", req_path])
    print("✔ Backend packages installed.")
    
    # Install SDK package
    sdk_path = "packages/flowweaver_sdk"
    print(f"Installing flowweaver-sdk from {sdk_path} in editable mode...")
    subprocess.check_call([pip_path, "install", "-e", sdk_path])
    print("✔ FlowWeaver SDK installed.")

def setup_frontend():
    print("\\nSetting up frontend workspaces...")
    try:
        print("Running npm install...")
        subprocess.check_call(["npm", "install"])
        print("✔ Frontend package dependencies installed.")
    except Exception as e:
        print(f"❌ Error setting up frontend: {str(e)}")
        sys.exit(1)

def setup_env():
    print("\\nCreating environment configurations...")
    # Add .env placeholder if missing
    env_path = ".env"
    if not os.path.exists(env_path):
        with open(env_path, "w") as f:
            f.write("# Environment configurations\\nVITE_USE_MOCK_API=false\\n")
        print("✔ Created default .env configuration file.")
    else:
        print("✔ .env file already exists.")

def setup_database():
    print("\\nInitializing database tables...")
    # Trigger database schema initialization by running import test on backend DB engine
    api_dir = "apps/api"
    if platform.system() == "Windows":
        python_exec = os.path.abspath(os.path.join(api_dir, "venv", "Scripts", "python"))
    else:
        python_exec = os.path.abspath(os.path.join(api_dir, "venv", "bin", "python"))
        
    try:
        # Run database creation script
        db_init_cmd = "from app.db import engine, Base; Base.metadata.create_all(bind=engine); print('Database initialized successfully.')"
        subprocess.check_call([python_exec, "-c", db_init_cmd], cwd=api_dir)
        print("✔ Database schemas initialized.")
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        sys.exit(1)

def main():
    print("==================================================")
    print("           FlowWeaver Platform Installer          ")
    print("==================================================")
    
    check_requirements()
    setup_venv()
    setup_frontend()
    setup_env()
    setup_database()
    
    print("\\n==================================================")
    print("✔ Onboarding setup complete successfully!")
    print("--------------------------------------------------")
    print("To run the platform development servers, run:")
    print("  python scripts/run.py")
    print("==================================================")

if __name__ == "__main__":
    main()
