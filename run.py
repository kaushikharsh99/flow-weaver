#!/usr/bin/env python3
import os
import sys
import subprocess
import threading

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
    print("🚀 Starting FlowWeaver Monorepo Setup & Dev Run script...")
    
    # Paths
    root_dir = os.path.dirname(os.path.abspath(__file__))
    api_dir = os.path.join(root_dir, "apps/api")
    venv_dir = os.path.join(api_dir, "venv")
    
    # 1. Setup Python Virtual Environment
    if not os.path.exists(venv_dir):
        print("📦 Python virtual environment not found. Creating venv inside apps/api/venv...")
        subprocess.run(f"{sys.executable} -m venv venv", shell=True, cwd=api_dir)
        
    # Determine pip and python paths in venv
    if os.name == "nt":  # Windows
        pip_path = os.path.join(venv_dir, "Scripts", "pip")
        python_path = os.path.join(venv_dir, "Scripts", "python")
    else:  # Unix/Linux/macOS
        pip_path = os.path.join(venv_dir, "bin", "pip")
        python_path = os.path.join(venv_dir, "bin", "python")
        
    # 2. Install Python dependencies
    print("📥 Installing/updating Python dependencies...")
    subprocess.run(f"{pip_path} install -r requirements.txt", shell=True, cwd=api_dir)
    
    # 3. Install Node dependencies if missing
    if not os.path.exists(os.path.join(root_dir, "node_modules")):
        print("📥 node_modules not found. Installing workspace dependencies...")
        subprocess.run("npm install", shell=True, cwd=root_dir)
        
    # 4. Start servers concurrently
    print("\n🔥 Starting Dev Servers...")
    print("   - [Backend API] will run on: http://localhost:8000")
    print("   - [Backend API Docs] will run on: http://localhost:8000/api/docs")
    print("   - [Frontend UI] will run on Vite dev port (usually http://localhost:5173)")
    print("Press Ctrl+C to stop both servers.\n")
    
    # Command for backend
    backend_cmd = f"{python_path} -m uvicorn main:app --reload --port 8000"
    # Command for frontend
    frontend_cmd = "npm run dev --workspace=apps/web"
    
    # Threading setup to run concurrently
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
        # Block until interrupt
        while t_backend.is_alive() or t_frontend.is_alive():
            t_backend.join(timeout=1.0)
            t_frontend.join(timeout=1.0)
    except KeyboardInterrupt:
        print("\n👋 Stopping both dev servers. Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
