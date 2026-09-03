import re

def get_olt_from_nas_port(nas_port):
    match = re.search(r"olt(\d+)$", nas_port.lower())

    if not match:
        raise ValueError(
            f"Could not determine OLT from NAS Port ID: {nas_port}"
        )
    return f"OLT{match.group(1)}"