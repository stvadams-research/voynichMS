import sys
from pathlib import Path

# Add src to path relative to this script
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root / 'src'))

try:
    import phase1_foundation.core.geometry
    print("Import successful")
except ImportError as e:
    print(f"Import failed: {e}")
    print(f"sys.path: {sys.path}")
