#!/usr/bin/env python3
import os
import sys
import subprocess

def run_cmd(args, cwd=None) -> bool:
    """Run command and return True if successful."""
    try:
        subprocess.check_call(args, cwd=cwd)
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("==================================================")
    print("        FlowWeaver Team Onboarding Quality Gate   ")
    print("==================================================")
    
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    api_dir = os.path.join(root_dir, "apps/api")
    plugins_dir = os.path.join(root_dir, "plugins")
    
    # 1. Run core compiler tests
    print("\n[Gate 1] Running core compiler test suite...")
    if not run_cmd(["python3", "scripts/test.py"], cwd=root_dir):
        print("❌ Error: Core compiler tests failed.")
        sys.exit(1)
    print("✔ Core compiler tests passed.")

    # 2. Find and check all local plugins
    print("\n[Gate 2] Scanning local plugins and custom nodes...")
    if os.path.exists(plugins_dir):
        plugin_folders = [
            f for f in os.listdir(plugins_dir) 
            if os.path.isdir(os.path.join(plugins_dir, f)) and f != "__pycache__"
        ]
        
        flowweaver_bin = os.path.join(api_dir, "venv/bin/flowweaver")
        if not os.path.exists(flowweaver_bin):
            flowweaver_bin = "flowweaver"  # Fallback to path
            
        for folder in plugin_folders:
            path = os.path.join(plugins_dir, folder)
            
            # Check if this is a modular node capability package containing node.py
            node_py = os.path.join(path, "node.py")
            if not os.path.exists(node_py):
                print(f"Skipping plugin/folder '{folder}' (does not contain a single-node adapter node.py layout).")
                continue
                
            print(f"\n--- Checking Plugin: {folder} ---")
            
            # Lint
            print("Linting...")
            if not run_cmd([flowweaver_bin, "lint-node", path], cwd=plugins_dir):
                print(f"❌ Error: Lint failed for plugin '{folder}'")
                sys.exit(1)
            print("✔ Lint passed.")
            
            # Unit Tests
            print("Testing...")
            if not run_cmd([flowweaver_bin, "test-node", path], cwd=plugins_dir):
                print(f"❌ Error: Unit tests failed for plugin '{folder}'")
                sys.exit(1)
            print("✔ Tests passed.")

    print("\n==================================================")
    print("✔ All Quality Gates Passed successfully! Ready to push.")
    print("==================================================")

if __name__ == "__main__":
    main()
