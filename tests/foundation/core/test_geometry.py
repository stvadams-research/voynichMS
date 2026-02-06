import pytest
from foundation.core.geometry import Point, Box, Polygon

def test_point_valid():
    p = Point(x=0.5, y=0.5)
    assert p.x == 0.5
    assert p.y == 0.5

def test_point_invalid():
    with pytest.raises(ValueError):
        Point(x=1.1, y=0.5)
    with pytest.raises(ValueError):
        Point(x=-0.1, y=0.5)

def test_box_valid():
    b = Box(x_min=0.1, y_min=0.1, x_max=0.9, y_max=0.9)
    assert b.width == 0.8
    assert b.height == 0.8

def test_box_invalid_coords():
    with pytest.raises(ValueError):
        Box(x_min=1.1, y_min=0.1, x_max=0.9, y_max=0.9)

def test_box_invalid_dimensions():
    with pytest.raises(ValueError):
        Box(x_min=0.9, y_min=0.1, x_max=0.1, y_max=0.9)

def test_polygon_valid():
    points = [
        Point(x=0.1, y=0.1),
        Point(x=0.9, y=0.1),
        Point(x=0.5, y=0.9)
    ]
    poly = Polygon(points=points)
    assert len(poly.points) == 3
    
    bbox = poly.bounding_box
    assert bbox.x_min == 0.1
    assert bbox.x_max == 0.9
    assert bbox.y_min == 0.1
    assert bbox.y_max == 0.9

def test_polygon_invalid():
    points = [
        Point(x=0.1, y=0.1),
        Point(x=0.9, y=0.1)
    ]
    with pytest.raises(ValueError):
        Polygon(points=points)
