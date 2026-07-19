#!/usr/bin/env python3
import os
import sys
import socket
import platform
import subprocess

def check_port(port: int) -> bool:
    """Returns True if the port is free, False if occupied."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0

def check_package(python_exec: str, pkg_name: str) -> bool:
    """Checks if a python package can be imported."""
    try:
        subprocess.check_call([python_exec, "-c", f"import {pkg_name}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("==================================================")
    print("           FlowWeaver System Diagnostic           ")
    print("==================================================")
    
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    api_dir = os.path.join(root_dir, "apps/api")
    venv_dir = os.path.join(api_dir, "venv")
    
    if platform.system() == "Windows":
        python_exec = os.path.join(venv_dir, "Scripts", "python")
    else:
        python_exec = os.path.join(venv_dir, "bin", "python")
        
    all_ok = True

    # 1. Check Python
    print(f"Checking Python: {platform.python_version()} ... ", end="")
    if sys.version_info.major >= 3 and sys.version_info.minor >= 8:
        print("✔ OK")
    else:
        print("❌ Error (Python 3.8+ required)")
        all_ok = False

    # 2. Check Node
    print("Checking Node.js ... ", end="")
    try:
        node_ver = subprocess.check_output(["node", "--version"], text=True).strip()
        print(f"✔ OK ({node_ver})")
    except Exception:
        print("❌ Error (Node.js missing)")
        all_ok = False

    # 3. Check Virtual Env
    print("Checking Backend Virtual Env ... ", end="")
    if os.path.exists(python_exec):
        print("✔ OK")
    else:
        print("❌ Error (apps/api/venv missing. Run scripts/install.py)")
        all_ok = False

    # 4. Check Backend Packages imports
    if os.path.exists(python_exec):
        packages = ["fastapi", "uvicorn", "sqlalchemy", "pydantic", "polars", "pyarrow", "duckdb", "flowweaver.sdk"]
        for pkg in packages:
            print(f"Checking module '{pkg}' ... ", end="")
            if check_package(python_exec, pkg):
                print("✔ OK")
            else:
                print("❌ Missing")
                all_ok = False

    # 5. Check Frontend modules
    print("Checking Frontend node_modules ... ", end="")
    if os.path.exists(os.path.join(root_dir, "node_modules")):
        print("✔ OK")
    else:
        print("❌ Missing (Run npm install)")
        all_ok = False

    # 6. Check .env configurations
    print("Checking env configuration file ... ", end="")
    if os.path.exists(os.path.join(root_dir, ".env")):
        print("✔ OK")
    else:
        print("❌ Missing (.env configuration template not found)")
        all_ok = False

    # 7. Check Ports availability
    print("Checking port 8000 (API Server) ... ", end="")
    if check_port(8000):
        print("✔ Free")
    else:
        print("❌ Occupied (Uvicorn or another process running)")
        all_ok = False

    print("Checking port 8080 (Frontend UI) ... ", end="")
    if check_port(8080):
        print("✔ Free")
    else:
        print("❌ Occupied (Vite or another process running)")
        all_ok = False

    # 8. Check database
    db_file = os.path.join(api_dir, "flow_weaver.db")
    print("Checking SQLite database file ... ", end="")
    if os.path.exists(db_file):
        print("✔ Found")
    else:
        print("⚠ Missing (Will be initialized on database schema setup)")

    print("==================================================")
    if all_ok:
        print("✔ FlowWeaver status: healthy! You are ready to go.")
    else:
        print("❌ FlowWeaver status: unresolved issues found. Run python scripts/install.py")
    print("==================================================")

if __name__ == "__main__":
    main()
