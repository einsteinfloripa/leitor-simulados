import pathlib
import math
import cv2



from EFscanAlgo import Scanner, ef_get_tilt
from core.object_detection import Detection
from core.models import load_model
from utils.data_classes import FloatBoundingBox

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
        # Draw the lines and save the image
        # Merge the lines
        h_lines = self.__merge_lines(h_lines, 'h', img)
        v_lines = self.__merge_lines(v_lines, 'v', img)
        # Filter the lines again
        h_lines = self.__second_filter_lines(h_lines, 'h', img)
        v_lines = self.__second_filter_lines(v_lines, 'v', img)
        # Assert if the number of lines is correct
        assert len(h_lines) == self._get_test_data('n_h_lines')
        assert len(v_lines) == self._get_test_data('n_v_lines')
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
            if l[1] > HEIGHT*0.85 or l[1] < HEIGHT*0.38 or \
            l[0] > WIDTH*0.95 or l[2] < WIDTH*0.05:
                continue

            if tg < 45 and tg >= -2:
                h_lines.append(l)
            else:
                v_lines.append(l)
            
        return h_lines, v_lines


    def __second_filter_lines(self, lines, axis, img):
        # Get relevant constants
        n_h_line = self._get_test_data('n_h_lines')
        n_v_line = self._get_test_data('n_v_lines') 
        # Define variables
        if axis == 'h':
            lines.sort(key=lambda x: x[1])
            n = 1
            spacing_c = self._get_test_data('h_line_spacing') * img.shape[0]
        elif axis == 'v':
            lines.sort(key=lambda x: x[0])
            n = 0
            spacing_c = self._get_test_data('v_line_spacing') * img.shape[1]
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
        # Return the lines
        return [line for group in groups for line in group]


    def __merge_lines(self, lines, axis, img):
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
            elif abs(lines[i][n] - lines[i-1][n]) < 5:
                groups[-1].append(lines[i])
            else:
                groups.append([lines[i]])
        # Filter small groups
        groups = [group for group in groups if len(group) > 2]
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