HEADER_TEMPLATE = '''"""
FlowWeaver Generated Preprocessing Script
Pipeline: {pipeline_name}
Generated: Auto-compiled visual DAG script

DO NOT EDIT DIRECTLY — Changes will be overwritten upon compiler re-generation.
"""
'''


def get_header(pipeline_name: str = "Untitled Pipeline") -> str:
    return HEADER_TEMPLATE.format(pipeline_name=pipeline_name)
