"""
Categorizes Voynich pages into major sections based on folio ranges.
"""

import argparse

SECTION_RANGES = {
    "herbal": (1, 66),
    "astronomical": (67, 73),
    "biological": (75, 84),
    "cosmological": (85, 86),
    "pharmaceutical": (87, 102),
    "stars": (103, 116)
}

def get_section(folio_id: str) -> str:
    """
    Returns the section name for a given folio ID (e.g. 'f1r').
    """
    try:
        # Extract number from 'f12r'
        num_str = "".join([c for c in folio_id if c.isdigit()])
        if not num_str:
            return "unknown"
        num = int(num_str)

        for name, (start, end) in SECTION_RANGES.items():
            if start <= num <= end:
                return name
        return "unknown"
    except (TypeError, ValueError):
        return "unknown"

def _parse_args():
    parser = argparse.ArgumentParser(description="Categorize Voynich pages into sections")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--output-dir", type=str, default=None, help="Override output directory")
    return parser.parse_args()


if __name__ == "__main__":
    _args = _parse_args()
    # Test
    print(f"f1r: {get_section('f1r')}")
    print(f"f70v: {get_section('f70v')}")
    print(f"f90r: {get_section('f90r')}")
