#!/usr/bin/env python3
import os
import sys
import subprocess

def main():
    # Forward execution to scripts/run.py
    root_dir = os.path.dirname(os.path.abspath(__file__))
    run_script = os.path.join(root_dir, "scripts", "run.py")
    
    try:
        subprocess.check_call([sys.executable, run_script])
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()
