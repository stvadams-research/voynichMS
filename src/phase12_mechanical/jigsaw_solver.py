"""
Jigsaw Solver Tools

Reconstructs physical tool geometry from mechanical slips.
"""

from typing import List, Dict, Any, Tuple
from collections import Counter, defaultdict
import networkx as nx

class JigsawAdjacencyMapper:
    """
    Builds a physical adjacency graph from mechanical slips.
    """
    def build_adjacency_graph(self, slips: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Edge: (Word_Actual, Word_Slip)
        edges = Counter()
        
        for s in slips:
            pair = tuple(sorted([s['word'], s['actual_context'][0]]))
            edges[pair] += 1
            
        G = nx.Graph()
        for (u, v), weight in edges.items():
            G.add_edge(u, v, weight=weight)
            
        centrality = nx.degree_centrality(G)
        top_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:20]
        
        return {
            "total_physical_edges": len(edges),
            "total_physical_nodes": G.number_of_nodes(),
            "top_physical_anchors": top_nodes,
            "frequent_adjacencies": [{"pair": k, "count": v} for k, v in edges.most_common(20)]
        }

class ColumnarReconstructor:
    """
    Reconstructs the vertical stacks of words for each horizontal position (column).
    """
    def reconstruct_columns(self, slips: List[Dict[str, Any]]) -> Dict[int, List[Tuple[str, int]]]:
        # Position -> Word Counter
        columns = defaultdict(Counter)
        
        for s in slips:
            pos = s['token_index']
            word = s['word']
            columns[pos][word] += 1
            
        reconstructed = {}
        for pos, counts in columns.items():
            reconstructed[pos] = counts.most_common(10)
            
        return reconstructed

class BlueprintSynthesizer:
    """
    Synthesizes columnar data into a 2D blueprint of the physical tool.
    """
    def synthesize_blueprint(self, columns: Dict[int, List[Tuple[str, int]]], max_rows: int = 10) -> List[List[str]]:
        max_pos = max(columns.keys()) if columns else 0
        blueprint = []
        
        for r in range(max_rows):
            row = []
            for p in range(1, max_pos + 1):
                stack = columns.get(p, [])
                if r < len(stack):
                    row.append(stack[r][0])
                else:
                    row.append("-")
            blueprint.append(row)
            
        return blueprint
