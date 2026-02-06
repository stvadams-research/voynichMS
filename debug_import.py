import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    import voynich.core.geometry
    print("Import successful")
except ImportError as e:
    print(f"Import failed: {e}")
    print(f"sys.path: {sys.path}")
