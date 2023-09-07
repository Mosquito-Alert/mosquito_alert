from abc import ABC, abstractmethod
from statistics import fmean

from .models import BaseShape


class ShapeNotAvailable(Exception):
    pass


# Inspired in datumaro.components.annotation
class _Shape(ABC):
    # NOTE: Top left is x: 0, y: 0
    shape_type = None

    def __init__(self, points: tuple[tuple[float, float]]):
        # Points: ((x1, y1), ..., (xn, yn))
        self.points = tuple(tuple(x) for x in points)

    @abstractmethod
    def get_area(self):
        raise NotImplementedError()

    @abstractmethod
    def as_polygon(self) -> list[tuple[float, float]]:
        raise NotImplementedError()

    def get_bbox(self) -> tuple[float, float, float, float]:
        "Returns (x, y, w, h)"

        points = self.points
        if not points:
            return None

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        x0 = min(xs)
        x1 = max(xs)
        y0 = min(ys)
        y1 = max(ys)
        return (x0, y0, x1 - x0, y1 - y0)

    def __str__(self):
        return f"{self.__class__}(points={self.points})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return id(self)


class Rectangle(_Shape):
    shape_type = BaseShape.ShapeType.RECTANGLE

    @staticmethod
    def xywh2xyxy(x: float, y: float, w: float, h: float) -> tuple[tuple[float, float], tuple[float, float]]:
        # Convert boxes from [x, y, w, h] to ((x1, y1), (x2, y2))
        # where xy1=top-left, xy2=bottom-right
        return ((x, y), (x + w, y + h))

    @classmethod
    def from_xywh(cls, x, y, w, h):
        return cls(points=cls.xywh2xyxy(x=x, y=y, w=w, h=h))

    def __init__(self, points: tuple[tuple[float, float], tuple[float, float]]):
        if len(points) != 2:
            raise ValueError(
                "points in Rectangle by must be ((x1, y1), (x2, y2)) where xy1=top-left, xy2=bottom-right."
            )

        super().__init__(points=tuple(points))

    @property
    def x(self) -> float:
        # Top left x
        return min(self.points[0][0], self.points[1][0])

    @property
    def y(self) -> float:
        # Top left y
        return min(self.points[0][1], self.points[0][1])

    @property
    def w(self) -> float:
        return max(self.points[0][0], self.points[1][0]) - self.x

    @property
    def h(self) -> float:
        return max(self.points[0][1], self.points[1][1]) - self.y

    def get_area(self) -> float:
        return self.w * self.h

    def as_polygon(self) -> list[tuple[float, float]]:
        x, y, w, h = self.get_bbox()
        return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]

    def iou(self, other: _Shape) -> float:
        return bbox_iou(self, other)


def get_shape_by_type(shape_type) -> _Shape:
    all_shapes = [Rectangle]

    try:
        result = list(filter(lambda x: x.shape_type == shape_type, all_shapes))[0]
    except IndexError:
        raise ShapeNotAvailable

    return result


def bbox_iou(a: _Shape, b: _Shape) -> float:
    """
    IoU computations for simple cases with bounding boxes
    """
    bbox_a = a.get_bbox()
    bbox_b = b.get_bbox()

    # determine the (x, y)-coordinates of the intersection rectangle
    aX, aY, aW, aH = bbox_a
    bX, bY, bW, bH = bbox_b
    in_right = min(aX + aW, bX + bW)
    in_left = max(aX, bX)
    in_top = max(aY, bY)
    in_bottom = min(aY + aH, bY + bH)

    # compute the area of intersection rectangle
    in_w = max(0, in_right - in_left)
    in_h = max(0, in_bottom - in_top)
    intersection = in_w * in_h

    # compute the area of both rectangles
    a_area = aW * aH
    b_area = bW * bH
    union = a_area + b_area - intersection

    return intersection / union


def avg_rectangles(rectangles: list[Rectangle]) -> Rectangle:
    # Averaging top-left points and bottom-right points.
    avg_topleft_point = (
        fmean([item.x for item in rectangles]),
        fmean([item.y for item in rectangles]),
    )
    avg_bottomright_point = (
        fmean([item.x + item.w for item in rectangles]),
        fmean([item.y + item.h for item in rectangles]),
    )

    return Rectangle(points=(avg_topleft_point, avg_bottomright_point))


def group_rectangles(rectangles: list[Rectangle], min_iou: float = 0.6) -> list[list[Rectangle]]:
    result = []

    # Ensure 'rectangles' is a list (e.g: not tuple)
    # Neede for the .pop method.
    rectangles = list(rectangles)

    candidates = rectangles
    while candidates:
        current_candidate = candidates.pop(0)  # Get first element in list
        new_group = [current_candidate]

        for c in candidates:
            if bbox_iou(current_candidate, c) >= min_iou:
                new_group.append(c)
                candidates.remove(c)

        result.append(new_group)

    return result
