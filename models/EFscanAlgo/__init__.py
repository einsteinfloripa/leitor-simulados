import cv2
import math


### FUNCTION USED TO GET THE RIGHT ALGORITHM ###
def get_scanner(test_type : str, stage : str):
    if stage == 'FIRST_STAGE':
        from EFscanAlgo.first_stage import FirstStageScanner
        return FirstStageScanner(test_type)
    elif stage == 'SECOND_STAGE':
        from EFscanAlgo.second_stage import SecondStageScanner
        return SecondStageScanner(test_type)


### EINSTEIN FLORIPA TEST IMAGES DEFINITIONS ###

class SimufscData:
    n_boxes = 40                # Number of boxes in the test
    n_boxes_per_row = 14        # Number of boxes per row
    n_h_lines = 6               # Number of horizontal lines
    n_v_lines = 28              # Number of vertical lines
    v_line_spacing = 0.004705   # Vertical line spacing (% of height)
    h_line_spacing = 0.007259   # Horizontal line spacing (% of width)

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

class Scanner:

    _test_data = None
    
    @classmethod
    def __bind(cls, ef_test):
        cls._test_data = ef_test
    
    @classmethod
    def _get_test_data(cls, key):
        return cls._test_data.__dict__.get(key)
    
    def __init__(self, test_type : str):
        # Get the relevant data
        if test_type.upper() == "SIMUFSC":
            Scanner.__bind(SimufscData)
        elif test_type.upper() == "SIMUENEM":
            Scanner.__bind(SimuenemData)
        elif test_type.upper() == "SIMULINHO":
            Scanner.__bind(SimulinhoData)
        elif test_type.upper() == "PS":
            Scanner.__bind(PSData)
        else:
            raise ValueError("Invalid test type")
        

### AUXILIARY FUNCTIONS ###

def ef_get_tilt(img, draw=False):
    '''Recebe uma prova einsteinfloripa e retorna o ângulo de inclinação da prova.'''
    # Get onlt the top 15% of the image
    img_ = img[0:int(img.shape[0]*0.15), 0:img.shape[1]].copy()
    # Apply a gaussian blur
    img_ = cv2.GaussianBlur(img_, (5, 5), 0)
    # Filter the noise
    img_ = cv2.bilateralFilter(img_, 9, 75, 75)
    # Convert to grayscale
    img_ = cv2.cvtColor(img_, cv2.COLOR_BGR2GRAY)
    # Canny edge detection
    edges = cv2.Canny(img_, 50, 200)
    # Find the contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # Identify the squares
    squares = []
    for cnt in contours:
        # Aproximate the contour to a polygon
        epsilon = 0.02 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        # Check if the aproximation has 4 sides and is convex
        if len(approx) == 4 and cv2.isContourConvex(approx):
            (x, y, w, h) = cv2.boundingRect(approx)
            # Check it is a big enough square
            # The magic numbers were obtained by trial and error
            if w > 0.015 * img_.shape[1] and h > 0.076 * img_.shape[0]:
                # Check if the aspect ratio is close to 1
                aspect_ratio = float(w) / h
                if 0.9 <= aspect_ratio <= 1.1:
                    squares.append(approx)
    # Find the centers of the squares
    centers = []
    for square in squares:
        M = cv2.moments(square)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            centers.append((cX, cY))
    centers.sort(key=lambda x: x[0])
    # Draw the squares and centers if needed
    if draw:
        # convert back to BGR
        img_ = cv2.cvtColor(img_, cv2.COLOR_GRAY2BGR)
        for square in squares:
            print(square)
            cv2.drawContours(img_, [square], -1, (0, 255, 0), 3)
        for center in centers:
            print(center)
            cv2.circle(img_, (cX, cY), 5, (255, 0, 0), -1) 
        cv2.imwrite("debug_tilt.jpg", img_)
    # Finally calculate the tilt using the centers
    tilt = 0
    if len(squares) == 2:
        tilt = - math.degrees(math.atan( # menos porque o eixo y é invertido
            (centers[1][1] - centers[0][1]) / (centers[1][0] - centers[0][0])
        ))
        return tilt
    else:
        print("Could not find only two squares in the image.")
        return