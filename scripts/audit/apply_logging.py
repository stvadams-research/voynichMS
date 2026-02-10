import os
from pathlib import Path

def apply_logging():
    src_root = Path("src")
    count = 0
    
    for py_file in src_root.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
            
        with open(py_file, "r") as f:
            content = f.read()
            
        if "import logging" in content or "logger =" in content:
            continue
            
        # Basic injection strategy: add after last import or at top
        lines = content.splitlines()
        import_index = -1
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                import_index = i
        
        if import_index != -1:
            lines.insert(import_index + 1, "import logging")
            lines.insert(import_index + 2, "logger = logging.getLogger(__name__)")
            count += 1
            
            with open(py_file, "w") as f:
                f.write("\n".join(lines) + "\n")
                
    print(f"Applied logging to {count} files.")

if __name__ == "__main__":
    apply_logging()
