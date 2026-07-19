#!/usr/bin/env python3
import os
import shutil

def delete_path(path: str):
    """Safely delete a directory or file path."""
    if os.path.exists(path):
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
                print(f"✔ Deleted folder: {path}")
            else:
                os.remove(path)
                print(f"✔ Deleted file: {path}")
        except Exception as e:
            print(f"⚠ Failed to delete: {path} ({e})")

def main():
    print("==================================================")
    print("            FlowWeaver Cache Clean Tool           ")
    print("==================================================")
    
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 1. Clean pycaches & compiled files
    print("Cleaning compiled python caches...")
    for root, dirs, files in os.walk(root_dir):
        # Skip virtual env directories
        if "venv" in root.split(os.sep):
            continue
            
        for d in dirs:
            if d == "__pycache__" or d == ".pytest_cache" or d == ".mypy_cache":
                delete_path(os.path.join(root, d))
        for f in files:
            if f.endswith(".pyc") or f.endswith(".pyo") or f.endswith(".pyd"):
                delete_path(os.path.join(root, f))
                
    # 2. Clean build and lock targets
    print("\\nCleaning build targets and package locks...")
    build_paths = [
        os.path.join(root_dir, "apps/web/dist"),
        os.path.join(root_dir, "apps/web/.output"),
        os.path.join(root_dir, "apps/web/.vinxi"),
        os.path.join(root_dir, "apps/web/.tanstack"),
        os.path.join(root_dir, "packages/flowweaver_sdk/build"),
        os.path.join(root_dir, "packages/flowweaver_sdk/dist"),
        os.path.join(root_dir, "packages/flowweaver_sdk/flowweaver_sdk.egg-info"),
    ]
    
    for path in build_paths:
        delete_path(path)
        
    print("==================================================")
    print("✔ Cache cleanup completed successfully.")
    print("==================================================")

if __name__ == "__main__":
    main()
