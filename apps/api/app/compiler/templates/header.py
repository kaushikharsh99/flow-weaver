import time

HEADER_TEMPLATE = '''"""
FlowWeaver Generated Preprocessing Script
Pipeline: {pipeline_name}
Generated: {timestamp}

This script was compiled from a visual FlowWeaver pipeline.
It is fully standalone and can be run with: python {pipeline_name}.py
"""
'''


def get_header(pipeline_name: str = "Untitled Pipeline") -> str:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    return HEADER_TEMPLATE.format(pipeline_name=pipeline_name, timestamp=timestamp)
