import pathlib
import math
import cv2



from EFscanAlgo import Scanner, ef_get_tilt
from core.object_detection import Detection
from core.models import load_model
from utils.data_classes import FloatBoundingBox
from checks import CONTINUE_ON_FAIL

class FirstStageScanner(Scanner):
    
    def __init__(self, test_type : str) -> None:
        super().__init__(test_type)
        # For cpf_box detection
        self.yolo = load_model("YoloV8", "PS", "first_stage.pt")
    
    def detect(self, img):
        img_raw = img.raw
        detections = list()
        detections.extend(self.__get_question_blocks(img_raw))
        detections.extend(self.__get_cpf_blocks(img_raw))

        img.detections = detections
        img.draw_bounding_boxes()
        img.save

        return detections


    def __get_question_blocks(self, img_raw):
        # Get the relevant points for the bounding boxes
        def __get_blocks(intersec, img_):
            # Get the relevant constants
            n_boxes = self._get_test_data('n_boxes')
            boxes_per_row = self._get_test_data('n_boxes_per_row')
            nv = self._get_test_data('n_v_lines')
            # Break condition
            bc = 2*n_boxes + (n_boxes//boxes_per_row)*nv

            # Find the bounding boxes
            detections = []
            cont = 0
            while True:
                # Get the indexes
                j = cont % nv
                if j == 0 and cont != 0: 
                    cont += nv
                k = cont // nv
                # Break
                if cont >= bc: break
                # Append the bounding box
                detections.append(Detection(
                    FloatBoundingBox.from_floats(
                        *intersec[j + nv*k],
                        *intersec[j+1 + nv*(k+1)],
                    ),
                    1,
                    1,
                    img_.shape[1],
                    img_.shape[0],
                    ))
                cont += 2
            
            return detections

        # Copy the image
        img = img_raw.copy()
        # Get the image tilt
        tilt = ef_get_tilt(img)
        assert tilt != None, "Failed to get tilt from image."
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Rotate the image
        M = cv2.getRotationMatrix2D((img.shape[1] / 2, img.shape[0] / 2), (-1 * tilt), 1.0)
        img = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]))
        # Use Canny to detect edges
        edges = cv2.Canny(img, 50, 200, L2gradient=True)
        # Extract the lines
        lines = [l[0] for l in cv2.HoughLinesP(edges, 1, math.pi / 90, 50, None, 70, 5)]
        # Filter the lines
        h_lines, v_lines = self.__first_filter_lines(lines, img)
        h_lines, v_lines = self.__strip_outer_lines(h_lines, v_lines)


        # Merge the lines
        h_lines = self.__merge_lines(h_lines, 'h', img)
        v_lines = self.__merge_lines(v_lines, 'v', img)
        # Filter the lines again
        h_lines, v_lines = self.__strip_outer_lines(h_lines, v_lines, img)  
        h_lines = self.__second_filter_lines(h_lines, 'h', img)
        v_lines = self.__second_filter_lines(v_lines, 'v', img)
        # Merge the lines again
        h_lines = self.__merge_lines(h_lines, 'h', img, const=10)
        v_lines = self.__merge_lines(v_lines, 'v', img, const=10)
        # Assert if the number of lines is correct TODO: define wrapper for this
        try:
            assert len(h_lines) == self._get_test_data('n_h_lines')
            assert len(v_lines) == self._get_test_data('n_v_lines')
        except AssertionError:
            if CONTINUE_ON_FAIL:
                return []
            else:
                raise AssertionError("Failed to find the correct number of lines.")
        # find the intersection of the lines
        img_h, img_w = img.shape[:2]
        intersec = []
        for h_line in h_lines:
            for v_line in v_lines:
                intersec.append((v_line[0]/img_w, h_line[1]/img_h))
        # sort the intersections
        intersec = sorted(intersec, key=lambda x: (x[1], x[0]))
        # Get the bounding boxes from the intersections
        detections = __get_blocks(intersec, img)
        # Apply the tilt back to the bounding boxes
        for detection in detections:
            detection.rotate(tilt)
        # Return the detections
        return detections


    def __get_cpf_blocks(self, img_raw):
        # Calls the yolo model to detect the cpf blocks
        detections = self.yolo.detect(img_raw)
        CPFBlocks = []
        # Filter the detections to get only the CPF blocks 
        for detection in detections:
            if detection.class_id == 0:
                CPFBlocks.append(detection)
        return CPFBlocks


    def __first_filter_lines(self, lines, img):
        h_lines = []
        v_lines = []
        HEIGHT, WIDTH = img.shape[:2]
        for l in lines:
            # Filter lines with a slope between -88 and -2 or 2 and 88
            if l[2] - l[0] == 0:
                tg = 90.0
            else:
                tg = math.degrees(math.atan((l[3] - l[1]) / (l[2] - l[0])))
            if tg > 2 and tg < 88 or tg < -2 and tg > -88:
                continue
            # filter lines that are above some threshold
            if l[1] > HEIGHT*0.9 or l[1] < HEIGHT*0.36 or \
            l[0] > WIDTH*0.95 or l[2] < WIDTH*0.05:
                continue

            if tg < 45 and tg >= -2:
                h_lines.append(l)
            else:
                v_lines.append(l)
            
        return h_lines, v_lines


    def __second_filter_lines(self, lines, axis, img):
        # Define variables
        if axis == 'h':
            lines.sort(key=lambda x: x[1])
            n = 1
            # 3 times the normal spacing
            spacing_c = self._get_test_data('h_line_spacing') * 3 * img.shape[0]
        elif axis == 'v':
            lines.sort(key=lambda x: x[0])
            n = 0
            # 3 times the normal spacing
            spacing_c = self._get_test_data('v_line_spacing') * 3 * img.shape[1]
        # Group the lines
        # This time the groupping is more spaced appart
        groups = []
        for i in range(0, len(lines)):
            if i == 0:
                groups.append([lines[i]])
            elif abs(lines[i][n] - lines[i-1][n]) < spacing_c:
                groups[-1].append(lines[i])
            else:
                groups.append([lines[i]])
        # Check first and last group
        # If they have more than one line, remove the extra lines
        fg = groups[0]
        if len(fg) > 1:
            [fg.pop(0) for _ in range(len(fg)-1)]
        lg = groups[-1]
        if len(groups[-1]) > 1:
            [lg.pop(-1) for _ in range(len(lg)-1)]
        # TODO: get rid of the magic number 5
        lower_bound = fg[0][n] - 5
        upper_bound = lg[0][n] + 5
        # Return the lines
        return [line for group in groups for line in group if line[n] > lower_bound and line[n] < upper_bound]


    def __merge_lines(self, lines, axis, img, const = 5):
        # Get variables set
        height, width = img.shape[:2]
        if axis == 'h':
            lines.sort(key=lambda x: x[1])
            n = 1
        elif axis == 'v':
            lines.sort(key=lambda x: x[0])
            n = 0
        # Cluster lines together
        groups = []
        for i in range(0, len(lines)):
            if i == 0:
                groups.append([lines[i]])
            elif abs(lines[i][n] - lines[i-1][n]) < const:
                groups[-1].append(lines[i])
            else:
                groups.append([lines[i]])
        # Get a form of average of the lines
        avg_lines = []
        for group in groups:
            avg = [0, 0]
            for line in group:
                avg[0] += line[n]
                avg[1] += line[n+2]
            avg = [int(x/len(group)) for x in avg]
            avg_lines.append(avg)

        # Extend the lines to the limits of the image
        for line in avg_lines:
            if axis == 'h':
                line[:] = [0, line[0], width, line[1]]
            elif axis == 'v':
                line[:] = [line[0], 0, line[1], height]

        return avg_lines
    

    def __strip_outer_lines(self, h_lines, v_lines, img = None):
        if img is not None:
            img_h, img_w = img.shape[:2]
            v_spacing = self._get_test_data('h_line_spacing')
            h_spacing = self._get_test_data('v_line_spacing')
        # Get variables set
        bounds = [(None,None), (None, None)] # (h_bounds, v_bounds)
        # get the upper and lower bounds for each axis
        for lines in [h_lines, v_lines]: 
            if lines == h_lines:
                lines.sort(key=lambda x: x[1])
                n = 1
                constant = 5 if img is None else img_h*v_spacing*5
            elif lines == v_lines:
                lines.sort(key=lambda x: x[0])
                n = 0
                constant = 5 if img is None else img_w*h_spacing*3
            # Cluster lines together
            groups = []
            for i in range(0, len(lines)):
                if i == 0:
                    groups.append([lines[i]])
                elif abs(lines[i][n] - lines[i-1][n]) < constant:
                    groups[-1].append(lines[i])
                else:
                    groups.append([lines[i]])
            # Get the first and last group
            first_group = groups[0]
            last_group = groups[-1]
            # Get the bound coordinates TODO: get reed of the magic number 10
            lower_bound = sum(
                [(line[n] + line[n+2])/2 for line in first_group]) / len(first_group) - 10
            upper_bound = sum(
                [(line[n] + line[n+2])/2 for line in last_group]) / len(last_group) + 10
            # Set the bounds
            bounds[n] = (lower_bound, upper_bound)
        # Filter the outer lines
        h_lines = [line for line in h_lines if (line[0]+line[2])/2 > bounds[0][0]
                    and (line[0]+line[2])/2 < bounds[0][1] 
                    and (line[1]+line[3])/2 > bounds[1][0]
                    and (line[1]+line[3])/2 < bounds[1][1]
                ]
        v_lines = [line for line in v_lines if (line[1]+line[3])/2 > bounds[1][0]
                    and (line[1]+line[3])/2 < bounds[1][1] 
                    and (line[0]+line[2])/2 > bounds[0][0]
                    and (line[0]+line[2])/2 < bounds[0][1]
                ]
        # Return the filtered lines
        return h_lines, v_lines
