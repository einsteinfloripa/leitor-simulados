from dataclasses import dataclass, field

@dataclass
class FloatPoint():
    x: float = field(default=0)
    y: float = field(default=0)

    def __iter__(self):
        return iter((self.x, self.y))

@dataclass
class FloatBoundingBox():
    ponto_min: FloatPoint = field(default=FloatPoint())
    ponto_max: FloatPoint = field(default=FloatPoint())

    #Constructors
    @classmethod
    def from_floats(cls, x_min, y_min, x_max, y_max):
        return cls(
            ponto_min = FloatPoint(x_min, y_min),
            ponto_max = FloatPoint(x_max, y_max),
        )

    def __iter__(self):
        return iter((*self.ponto_min, *self.ponto_max))



