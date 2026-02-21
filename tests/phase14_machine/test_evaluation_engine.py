from phase14_machine.evaluation_engine import EvaluationEngine


def test_calculate_coverage():
    vocab = {"word1", "word2", "word3"}
    engine = EvaluationEngine(vocab)
    
    tokens = ["word1", "word2", "unknown", "word3"]
    assert engine.calculate_coverage(tokens) == 0.75

def test_calculate_admissibility():
    vocab = {"a", "b", "c", "d"}
    engine = EvaluationEngine(vocab)
    
    # K=4 windows. No drift allowed in this simplified view if we use 0, 2 jumps.
    # Simple lattice: a -> window 2, c -> window 0
    lattice_map = {"a": 2, "b": 0, "c": 0}
    window_contents = {0: ["a", "b"], 1: [], 2: ["c"], 3: ["d"]}
    
    # Path: a (start in win 0) -> c (in win 2) -> b (in win 0)
    # 1. 'a' in win 0. Valid. current_window -> 2.
    # 2. 'c' in win 2. Valid. current_window -> 0.
    # 3. 'b' in win 0. Valid. current_window -> 0.
    lines = [["a", "c", "b"]]
    res = engine.calculate_admissibility(lines, lattice_map, window_contents)
    assert res["admissibility_rate"] == 1.0
    
    # Failing path: a -> d (d is in window 3)
    # current_window=0. 'a' valid. current_window -> 2.
    # next word 'd'. check_win: 1, 2, 3.
    # 3 is a neighbor of 2 (drift +1). so it IS valid.
    # Let's use window 1 which is empty.
    # Failing path: a -> b (b is in window 0)
    # current_window=0. 'a' valid. current_window -> 2.
    # next word 'b'. check_win: 1, 2, 3. None have 'b'.
    lines = [["a", "b"]]
    res = engine.calculate_admissibility(lines, lattice_map, window_contents)
    # first 'a' is valid. 'b' is not in neighborhood of win 2.
    assert res["admissibility_rate"] == 0.5

def test_calculate_overgeneration():
    vocab = {"a", "b", "c"}
    engine = EvaluationEngine(vocab)
    
    real_lines = [["a", "b", "c"]]
    syn_lines = [["a", "b", "c"], ["a", "c", "b"]]
    
    res = engine.calculate_overgeneration(syn_lines, real_lines)
    # real bigrams: (a,b), (b,c)
    # syn bigrams: (a,b), (b,c), (a,c), (c,b)
    # unattested: (a,c), (c,b)
    assert res["BUR"]["unattested_count"] == 2
    assert res["BUR"]["rate"] == 0.5
