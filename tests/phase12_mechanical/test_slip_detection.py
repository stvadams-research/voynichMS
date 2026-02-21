import pytest
from phase12_mechanical.slip_detection import MechanicalSlipDetector

def test_slip_detection():
    detector = MechanicalSlipDetector(min_transition_count=1)
    
    # Training lines to define 'legal' transitions
    # (a, 1) -> b  (Word 'b' is legal if preceded by 'a' at position 1)
    # (x, 1) -> c  (Word 'c' is legal if preceded by 'x' at position 1)
    train_lines = [
        ["a", "b"],
        ["x", "c"]
    ]
    detector.build_model(train_lines)
    
    # Test lines
    # Line 0: a c (valid start for pos 0)
    # Line 1: x b 
    #   - word 'b' at pos 1.
    #   - actual context: ('x', 1) -> word 'b' is NOT legal for 'x'
    #   - vertical context: ('a', 1) -> word 'b' IS legal for 'a'
    test_lines = [
        ["a", "c"],
        ["x", "b"]
    ]
    
    slips = detector.detect_slips(test_lines)
    
    assert len(slips) == 1
    assert slips[0]["word"] == "b"
    assert slips[0]["line_index"] == 1
    assert slips[0]["type"] == "vertical_offset_down"
