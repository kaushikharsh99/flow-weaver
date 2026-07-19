#!/usr/bin/env python3
import os
import sys
import subprocess
import threading
import platform

def run_command(cmd, prefix, cwd=None, env=None):
    """Run a subprocess and print its output prefixed for clarity."""
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=cwd,
        env=env,
        text=True,
        bufsize=1
    )
    
    try:
        for line in iter(process.stdout.readline, ''):
            print(f"{prefix} {line.strip()}")
    except Exception as e:
        print(f"{prefix} Error reading output: {e}")
    finally:
        process.stdout.close()
        process.wait()

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    api_dir = os.path.join(root_dir, "apps/api")
    venv_dir = os.path.join(api_dir, "venv")
    
    # Verify setup is complete first
    if not os.path.exists(venv_dir):
        print("❌ Error: Virtual environment not found. Please run project setup onboarding script first:")
        print("  python scripts/install.py")
        sys.exit(1)
        
    if platform.system() == "Windows":
        python_path = os.path.join(venv_dir, "Scripts", "python")
    else:
        python_path = os.path.join(venv_dir, "bin", "python")
        
    print("==================================================")
    print("🚀 Starting FlowWeaver Development Servers...")
    print("==================================================")
    print("   - [Backend API] will run on: http://localhost:8000")
    print("   - [Backend API Docs] will run on: http://localhost:8000/api/docs")
    print("   - [Frontend UI] will run on: http://localhost:8080")
    print("Press Ctrl+C to terminate both servers.\\n")

    backend_cmd = f"{python_path} -m uvicorn main:app --reload --port 8000"
    frontend_cmd = "npm run dev --workspace=apps/web"

    # Concurrently launch server threads
    t_backend = threading.Thread(
        target=run_command, 
        args=(backend_cmd, "[API]", api_dir), 
        daemon=True
    )
    t_frontend = threading.Thread(
        target=run_command, 
        args=(frontend_cmd, "[WEB]", root_dir), 
        daemon=True
    )
    
    t_backend.start()
    t_frontend.start()
    
    try:
        while t_backend.is_alive() or t_frontend.is_alive():
            t_backend.join(timeout=1.0)
            t_frontend.join(timeout=1.0)
    except KeyboardInterrupt:
        print("\\n👋 Terminating dev run loops. Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
