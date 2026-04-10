import os

SAFE_DIR = os.path.abspath("d:\\Synapse_Core")

def _is_safe_path(filepath: str) -> bool:
    try:
        target_path = os.path.abspath(filepath)
        return target_path.lower().startswith(SAFE_DIR.lower())
    except Exception:
        return False

def read_local_file(filepath: str) -> str:
    if not _is_safe_path(filepath):
        return "Access Denied"
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def write_local_file(filepath: str, content: str) -> str:
    if not _is_safe_path(filepath):
        return "Access Denied"
    
    try:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return "Success"
    except Exception as e:
        return f"Error writing file: {str(e)}"
