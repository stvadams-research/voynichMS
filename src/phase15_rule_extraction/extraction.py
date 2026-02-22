from pathlib import Path

class RuleExtractor:
    """Extracts declarative rules from the implicit lattice-map and window-contents."""

    def __init__(self, lattice_map, window_contents):
        """
        Args:
            lattice_map (dict): Word -> Next Window ID mapping.
            window_contents (dict): Window ID -> list of words mapping.
        """
        self.lattice_map = lattice_map
        self.window_contents = window_contents

    def extract_rules(self):
        """
        Extracts implicit grammar into a declarative list.
        
        Returns:
            list: List of dicts with 'from_window', 'token', and 'to_window'.
        """
        rules = []
        for word, target_win in sorted(self.lattice_map.items()):
            # Find which window word belongs to
            found_win = None
            for wid, contents in self.window_contents.items():
                if word in contents:
                    found_win = wid
                    break

            if found_win is not None:
                rules.append({
                    "from_window": found_win,
                    "token": word,
                    "to_window": target_win
                })
        return rules

    def generate_markdown_report(self, rules, output_path, limit=100):
        """
        Generates a human-readable Markdown report of the rules.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            f.write("# Phase 15: Declarative Rule Table (Voynich Engine)

")
            f.write(
                "This document defines the explicit transition logic "
                "of the reconstructed mechanical generator. "
            )
            f.write(
                "A third party can reproduce the manuscript's structure "
                "by following these rules.

"
            )

            f.write("## 1. Physical Transition Table
")
            f.write("| Current Window | Chosen Token | Next Window |
")
            f.write("| :--- | :--- | :--- |
")

            # Limit to top N rules for readability in report
            for r in rules[:limit]:
                f.write(f"| {r['from_window']} | `{r['token']}` | {r['to_window']} |
")

            if len(rules) > limit:
                f.write(
                    f"
... [Table Truncated for Readability. "
                    f"Showing {limit} of {len(rules)} rules. "
                    "Full CSV available in logic export] ...

"
                )

            f.write("## 2. Global State Invariants
")
            f.write(
                "- **Deterministic Reset:** Every line returns the "
                "carriage to a start position (Window 0).
"
            )
            f.write(
                "- **Window Adjacency:** Scribe selection is restricted "
                "to the window exposed by the previous token's "
                "transition rule.
"
            )
