import pytest

from ..models import BaseShape
from ..shapes import (
    Rectangle,
    ShapeNotAvailable,
    _Shape,
    avg_rectangles,
    bbox_iou,
    get_shape_by_type,
    group_rectangles,
)


class DummyShape(_Shape):
    def get_area(self):
        return 0

    def as_polygon(self):
        return [0, 0]


###############################


class TestDummyShape:
    def test_points_must_be_defined(self):
        with pytest.raises(TypeError):
            DummyShape()

    def test_get_bbox_return_x_y_w_h(self):
        first_point = [10, 20]
        second_point = [30, 50]
        third_point = [20, 10]

        obj = DummyShape(points=[first_point, second_point, third_point])
        assert obj.get_bbox() == (10, 10, 20, 40)

    def test__eq__(self):
        obj1 = DummyShape(points=[[10, 10], [20, 20]])
        obj2 = DummyShape(points=[[10, 10], [20, 20]])
        obj3 = DummyShape(points=[[10, 10], [21, 21]])

        assert obj1 == obj2
        assert not obj1 == obj3
        assert not obj1 == "str"

    def test__hash__(self):
        obj = DummyShape(points=[[10, 10], [20, 20]])

        assert obj.__hash__() == id(obj)


class TestRectangle:
    def test_shape_type_is_RECTANGLE(self):
        assert Rectangle.shape_type == BaseShape.ShapeType.RECTANGLE

    def test_xywh2xyxy(self):
        xywh = (10, 10, 20, 40)

        assert Rectangle.xywh2xyxy(*xywh) == ((10, 10), (30, 50))

    def test_from_xywh(self):
        obj = Rectangle.from_xywh(x=1, y=1, w=10, h=10)

        assert obj.points == ((1, 1), (11, 11))

    def test_x(self):
        assert Rectangle(points=[(0, 1), (20, 30)]).x == 0

    def test_y(self):
        assert Rectangle(points=[(0, 1), (20, 30)]).y == 1

    def test_w(self):
        assert Rectangle(points=[(0, 1), (20, 30)]).w == 20

    def test_h(self):
        assert Rectangle(points=[(0, 1), (20, 30)]).h == 29

    def test_get_area(self):
        assert Rectangle(points=[(0, 0), (10, 10)]).get_area() == 100

    def test_get_bbox(self):
        assert Rectangle(points=[(10, 20), (100, 80)]).get_bbox() == (10, 20, 90, 60)

    def test_as_polygon(self):
        assert Rectangle(points=[(10, 20), (100, 80)]).as_polygon() == [(10, 20), (100, 20), (100, 80), (10, 80)]

    @pytest.mark.parametrize(
        "rectangle, expected_value",
        [
            (Rectangle(points=[(0, 0), (10, 10)]), 1),
            (Rectangle(points=[(11, 11), (100, 100)]), 0),
            (Rectangle(points=[(5, 5), (15, 15)]), 25 / 175),
        ],
    )
    def test_iou(self, rectangle, expected_value):
        rect1 = Rectangle(points=[(0, 0), (10, 10)])

        assert rect1.iou(rectangle) == expected_value


# FUNCTIONS


@pytest.mark.parametrize("shape_type, expected_return", [(BaseShape.ShapeType.RECTANGLE, Rectangle)])
def test_get_shape_by_type(shape_type, expected_return):
    assert get_shape_by_type(shape_type=shape_type) == expected_return


def test_get_shape_by_type_raise_ShapeNotAvailable_if_not_found():
    with pytest.raises(ShapeNotAvailable):
        get_shape_by_type(shape_type="this_does_not_exist")


@pytest.mark.parametrize(
    "shape_a, expected_result",
    [
        (Rectangle(points=[(0, 0), (10, 10)]), 1),
        (Rectangle(points=[(11, 11), (100, 100)]), 0),
        (Rectangle(points=[(5, 5), (15, 15)]), 25 / 175),
    ],
)
def test_bbox_iou(shape_a, expected_result):
    shape_b = Rectangle(points=[(0, 0), (10, 10)])

    assert bbox_iou(shape_a, shape_b) == expected_result


def test_avg_rectangles():
    rectangle1 = Rectangle(points=[(0, 0), (10, 10)])
    rectangle2 = Rectangle(points=[(2.5, 2.5), (12.5, 12.5)])
    rectangle3 = Rectangle(points=[(7.5, 7.5), (17.5, 17.5)])
    rectangle4 = Rectangle(points=[(10, 10), (20, 20)])

    expected_result = Rectangle(points=[(5, 5), (15, 15)])
    result = avg_rectangles(rectangles=[rectangle1, rectangle2, rectangle3, rectangle4])

    assert result == expected_result


def test_group_rectangles():
    rectangle1 = Rectangle(points=[(0, 0), (10, 10)])
    rectangle2 = Rectangle(points=[(0.5, 0.5), (9.5, 9.5)])
    rectangle3 = Rectangle(points=[(9.5, 9.5), (19.5, 19.5)])
    rectangle4 = Rectangle(points=[(10, 10), (20, 20)])

    expected_result = [[rectangle4, rectangle3], [rectangle1, rectangle2]]

    result = group_rectangles(rectangles=[rectangle4, rectangle1, rectangle3, rectangle2], min_iou=0.5)

    assert result == expected_result
