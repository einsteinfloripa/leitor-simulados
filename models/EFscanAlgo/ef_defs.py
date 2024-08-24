### SOME BASIC DEFINITIONS ###
import enum
class Axis(enum.Enum):
    VERTICAL = 0
    HORIZONTAL = 1

    @property
    def counterAxis(self):
        return Axis.HORIZONTAL if self == Axis.VERTICAL else Axis.VERTICAL


class Line():
    def __init__(self, init_as = [0, 0, 0, 0]):
        self.x1 = init_as[0]
        self.y1 = init_as[1]
        self.x2 = init_as[2]
        self.y2 = init_as[3]
    
    def __getitem__(self, index):
        if index == 0:
            return self.x1
        elif index == 1:
            return self.y1
        elif index == 2:
            return self.x2
        elif index == 3:
            return self.y2
        else:
            raise IndexError("Index out of range")

    def __setitem__(self, index, value):
        if index == 0:
            self.x1 = value
        elif index == 1:
            self.y1 = value
        elif index == 2:
            self.x2 = value
        elif index == 3:
            self.y2 = value
        else:
            raise IndexError("Index out of range")    

    def __repr__(self):
        return f"({self.x1}-{self.y1})({self.x2}-{self.y2})"

### EINSTEIN FLORIPA TEST IMAGES DATA AND DEFINITIONS ###

class SimufscData:
    n_boxes = 40                # Number of boxes in the test
    n_rows = 3                  # Number of rows
    n_boxes_per_row = 14        # Number of boxes per row
    n_h_lines = 6               # Number of horizontal lines
    n_v_lines = 28              # Number of vertical lines
    v_line_spacing = 0.0040     # Vertical line spacing (% of height)
    h_line_spacing = 0.007     # Horizontal line spacing (% of width)
    box_width =  0.05646        # Question Block box width (% of width)
    box_height = 0.1584         # Question Block box height (% of height)
    # Question Block
    qb_rows = 10
    qb_cols = 2

class SimuenemData:
    n_boxes = 9                 # Number of boxes in the test
    n_boxes_per_row = 5         # Number of boxes per row
    n_h_lines = 4               # Number of horizontal lines
    n_v_lines = 10              # Number of vertical lines
    v_line_spacing = 0.05       # Vertical line spacing (% of height)
    h_line_spacing = 0.016      # Horizontal line spacing (% of width)

class SimulinhoData:
    n_boxes = 5                 # Number of boxes in the test
    n_boxes_per_row = 3         # Number of boxes per row
    n_h_lines = 4               # Number of horizontal lines
    n_v_lines = 6               # Number of vertical lines
    v_line_spacing = 0.0285     # Vertical line spacing (% of height)
    h_line_spacing = 0.1        # Horizontal line spacing (% of width)

class PSData:
    n_boxes = 6                 # Number of boxes in the test
    n_boxes_per_row = 3         # Number of boxes per row
    n_h_lines = 4               # Number of horizontal lines
    n_v_lines = 6               # Number of vertical lines
    v_line_spacing = 0.0285     # Vertical line spacing (% of height)
    h_line_spacing = 0.1        # Horizontal line spacing (% of width)