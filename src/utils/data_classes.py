from dataclasses import dataclass, field


@dataclass
class IntPoint():
    x: int = field(default=0)
    y: int = field(default=0)

    def __iter__(self):
        return iter((self.x, self.y))


@dataclass
class IntPoint():
    x: int = field(default=0)
    y: int = field(default=0)

    def __iter__(self):
        return iter((self.x, self.y))
    
    def __eq__(self, value):
        return self.x == value.x and self.y == value.y


@dataclass
class FloatPoint():
    x: float = field(default=0)
    y: float = field(default=0)

    def __iter__(self):
        return iter((self.x, self.y))
    
    def __eq__(self, value):
        return self.x == value.x and self.y == value.y


@dataclass
class FloatBoundingBox():
    p_min: FloatPoint = field(default_factory=FloatPoint)
    p_max: FloatPoint = field(default_factory=FloatPoint)

    #Constructors
    @classmethod
    def from_floats(cls, x_min, y_min, x_max, y_max):
        return cls(
            p_min = FloatPoint(x_min, y_min),
            p_max = FloatPoint(x_max, y_max),
        )
    @classmethod
    def from_yolo(cls, x_center, y_center, width, height):
        x_min = x_center - width / 2
        y_min = y_center - height / 2
        x_max = x_center + width / 2
        y_max = y_center + height / 2
        return cls.from_floats(x_min, y_min, x_max, y_max)

    def __iter__(self):
        return iter((*self.p_min, *self.p_max))
    
    def __eq__(self, value):
        return self.p_min == value.p_min and self.p_max == value.p_max
    
    def __hash__(self):
        return hash((*self.p_min, *self.p_max))


@dataclass
class IntBoundingBox():
    p_min: IntPoint = field(default_factory=IntPoint)
    p_max: IntPoint = field(default_factory=IntPoint)

    #Constructors
    @classmethod
    def from_ints(cls, x_min, y_min, x_max, y_max):
        return cls(
            p_min = IntPoint(x_min, y_min),
            p_max = IntPoint(x_max, y_max),
        )

    def __iter__(self):
        return iter((*self.p_min, *self.p_max))
    
    def __eq__(self, value):
        return self.p_min == value.p_min and self.p_max == value.p_max
    
    def __hash__(self):
        return hash((*self.p_min, *self.p_max))
