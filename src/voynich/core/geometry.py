from typing import List, Tuple, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
import math

class Point(BaseModel):
    """
    A point in normalized 2D space (0.0 to 1.0).
    Origin (0,0) is top-left.
    """
    x: float = Field(..., ge=0.0, le=1.0)
    y: float = Field(..., ge=0.0, le=1.0)

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)

class Box(BaseModel):
    """
    A bounding box in normalized coordinates.
    """
    x_min: float = Field(..., ge=0.0, le=1.0)
    y_min: float = Field(..., ge=0.0, le=1.0)
    x_max: float = Field(..., ge=0.0, le=1.0)
    y_max: float = Field(..., ge=0.0, le=1.0)

    @model_validator(mode='after')
    def check_dimensions(self) -> 'Box':
        if self.x_max < self.x_min:
            raise ValueError(f"x_max ({self.x_max}) must be >= x_min ({self.x_min})")
        if self.y_max < self.y_min:
            raise ValueError(f"y_max ({self.y_max}) must be >= y_min ({self.y_min})")
        return self

    @property
    def width(self) -> float:
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        return self.y_max - self.y_min

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def centroid(self) -> Point:
        return Point(
            x=(self.x_min + self.x_max) / 2.0,
            y=(self.y_min + self.y_max) / 2.0
        )

    def intersection(self, other: 'Box') -> Optional['Box']:
        """
        Calculate the intersection of this box with another.
        Returns None if they do not intersect.
        """
        x_min = max(self.x_min, other.x_min)
        y_min = max(self.y_min, other.y_min)
        x_max = min(self.x_max, other.x_max)
        y_max = min(self.y_max, other.y_max)

        if x_max < x_min or y_max < y_min:
            return None

        return Box(x_min=x_min, y_min=y_min, x_max=x_max, y_max=y_max)

    def iou(self, other: 'Box') -> float:
        """
        Calculate Intersection over Union (IoU).
        """
        inter = self.intersection(other)
        if inter is None:
            return 0.0
        
        inter_area = inter.area
        union_area = self.area + other.area - inter_area
        
        if union_area == 0:
            return 0.0
            
        return inter_area / union_area

    def clip(self, bounds: 'Box') -> 'Box':
        """
        Clip this box to be within the bounds of another box.
        """
        x_min = max(self.x_min, bounds.x_min)
        y_min = max(self.y_min, bounds.y_min)
        x_max = min(self.x_max, bounds.x_max)
        y_max = min(self.y_max, bounds.y_max)
        
        # Ensure we don't return an invalid box if completely outside
        x_max = max(x_min, x_max)
        y_max = max(y_min, y_max)
        
        return Box(x_min=x_min, y_min=y_min, x_max=x_max, y_max=y_max)

    def contains(self, other: 'Box') -> bool:
        """
        Check if this box completely contains another box.
        """
        return (
            self.x_min <= other.x_min and
            self.y_min <= other.y_min and
            self.x_max >= other.x_max and
            self.y_max >= other.y_max
        )

    def distance(self, other: 'Box') -> float:
        """
        Calculate Euclidean distance between centroids.
        """
        c1 = self.centroid
        c2 = other.centroid
        return math.sqrt((c1.x - c2.x)**2 + (c1.y - c2.y)**2)

class Polygon(BaseModel):
    """
    A closed polygon defined by a list of normalized points.
    """
    points: List[Point]

    @field_validator("points")
    @classmethod
    def validate_points(cls, v: List[Point]) -> List[Point]:
        if len(v) < 3:
            raise ValueError("Polygon must have at least 3 points")
        return v

    @property
    def bounding_box(self) -> Box:
        xs = [p.x for p in self.points]
        ys = [p.y for p in self.points]
        return Box(
            x_min=min(xs),
            y_min=min(ys),
            x_max=max(xs),
            y_max=max(ys)
        )

class Transform(BaseModel):
    """
    A 2D affine transform.
    matrix is [a, b, c, d, tx, ty] representing:
    | a  b  tx |
    | c  d  ty |
    | 0  0  1  |
    """
    matrix: Tuple[float, float, float, float, float, float] = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)

    def apply(self, point: Point) -> Point:
        a, b, c, d, tx, ty = self.matrix
        new_x = a * point.x + b * point.y + tx
        new_y = c * point.x + d * point.y + ty
        # Clamp to 0-1 range to ensure valid Point
        return Point(
            x=max(0.0, min(1.0, new_x)),
            y=max(0.0, min(1.0, new_y))
        )

    def invert(self) -> 'Transform':
        a, b, c, d, tx, ty = self.matrix
        det = a * d - b * c
        if det == 0:
            raise ValueError("Transform is not invertible (determinant is 0)")
        
        inv_det = 1.0 / det
        
        new_a = d * inv_det
        new_b = -b * inv_det
        new_c = -c * inv_det
        new_d = a * inv_det
        new_tx = (b * ty - d * tx) * inv_det
        new_ty = (c * tx - a * ty) * inv_det
        
        return Transform(matrix=(new_a, new_b, new_c, new_d, new_tx, new_ty))

    def compose(self, other: 'Transform') -> 'Transform':
        """
        Apply this transform, then the other transform.
        Result = Other * This
        """
        a1, b1, c1, d1, tx1, ty1 = self.matrix
        a2, b2, c2, d2, tx2, ty2 = other.matrix
        
        new_a = a2 * a1 + b2 * c1
        new_b = a2 * b1 + b2 * d1
        new_c = c2 * a1 + d2 * c1
        new_d = c2 * b1 + d2 * d1
        new_tx = a2 * tx1 + b2 * ty1 + tx2
        new_ty = c2 * tx1 + d2 * ty1 + ty2
        
        return Transform(matrix=(new_a, new_b, new_c, new_d, new_tx, new_ty))
