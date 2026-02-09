import csv
import numpy as np
from pathlib import Path

def load_matrix(csv_path):
    matrix = {}
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.pop('Artifact')
            vector = np.array([float(v) for v in row.values()])
            matrix[name] = vector
    return matrix

def calculate_distances(matrix, target='Voynich'):
    v_target = matrix[target]
    distances = {}
    for name, vector in matrix.items():
        if name != target:
            dist = np.linalg.norm(v_target - vector)
            distances[name] = dist
    return distances

def run_analysis():
    # Adjust path to handle execution from root
    csv_path = Path('reports/comparative/COMPARATIVE_MATRIX.csv')
    if not csv_path.exists():
        csv_path = Path(__file__).resolve().parent.parent.parent / 'reports/comparative/COMPARATIVE_MATRIX.csv'
        
    matrix = load_matrix(csv_path)
    distances = calculate_distances(matrix)
    
    # Sort by distance
    sorted_dist = sorted(distances.items(), key=lambda x: x[1])
    
    report_path = Path('reports/comparative/PROXIMITY_ANALYSIS.md')
    if not report_path.parent.exists():
         report_path = Path(__file__).resolve().parent.parent.parent / 'reports/comparative/PROXIMITY_ANALYSIS.md'

    with open(report_path, 'w') as f:
        f.write("# PROXIMITY_ANALYSIS.md\n")
        f.write("## Phase B: Comparative and Contextual Classification\n\n")
        f.write("### Euclidean Distances from Voynich Manuscript\n\n")
        f.write("| Artifact | Distance | Proximity |\n")
        f.write("| :--- | :---: | :--- |\n")
        
        for name, dist in sorted_dist:
            prox = "Close" if dist < 5 else "Moderate" if dist < 8 else "Distant"
            f.write(f"| {name} | {dist:.4f} | {prox} |\n")
            
        f.write("\n### Clustering Insights\n\n")
        closest = sorted_dist[0][0]
        f.write(f"- **Nearest Neighbor:** {closest}\n")
        f.write(f"- **Structural Isolation:** Voynich distance to nearest neighbor is {sorted_dist[0][1]:.4f}.\n")
        
if __name__ == "__main__":
    run_analysis()