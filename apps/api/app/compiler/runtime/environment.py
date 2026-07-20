import sys
import os
from typing import Dict, Any


def get_execution_environment() -> Dict[str, str]:
    """Build environment variables dictionary for running generated scripts."""
    env = os.environ.copy()
    # Ensure current python path includes packages and apps/api
    pythonpath = env.get("PYTHONPATH", "")
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    packages_dir = os.path.join(root_dir, "packages", "flowweaver_sdk")
    api_dir = os.path.join(root_dir, "apps", "api")

    paths = [packages_dir, api_dir]
    if pythonpath:
        paths.append(pythonpath)

    env["PYTHONPATH"] = os.path.pathsep.join(paths)
    return env
