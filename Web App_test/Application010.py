from flask import Flask, render_template, Response, jsonify
import time
import cv2
import dlib
import numpy as np
import math
from scipy.spatial import distance as dist
from imutils import face_utils
import argparse
from ultralytics import YOLO

app = Flask(__name__)

model1 = YOLO('best_mobile.pt')
threshold_m = 0.7

class EARFilter:
    def __init__(self, window_size=5):
        self.values = []
        self.window_size = window_size

    def update(self, new_value):
        self.values.append(new_value)
        if len(self.values) > self.window_size:
            self.values.pop(0)
        return sum(self.values) / len(self.values)

def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

def mouth_aspect_ratio(mouth):
    X = dist.euclidean(mouth[2], mouth[10])
    Y = dist.euclidean(mouth[4], mouth[8])
    Z = dist.euclidean(mouth[0], mouth[6])

    mar = (X + Y) / (2.0 * Z)
    return mar

def get_eye_center(eye_points):
    """Calculate the center of the eye based on eye landmarks."""
    x = int(eye_points[:, 0].mean())
    y = int(eye_points[:, 1].mean())
    return (x, y)

def track_pupil(eye_frame):
    """Tracks the pupil within the eye frame using adaptive thresholding and Kalman filter."""

    # Adaptive thresholding
    if len(eye_frame.shape) == 3:  # Check if color image
        gray_eye_frame = cv2.cvtColor(eye_frame, cv2.COLOR_BGR2GRAY)
    else:
        gray_eye_frame = eye_frame.copy()  # Already grayscale

    if gray_eye_frame.dtype != np.uint8:
        gray_eye_frame = gray_eye_frame.astype(np.uint8)

        # Adaptive thresholding
    thresh = cv2.adaptiveThreshold(gray_eye_frame, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)

    # Find contours (potential pupil candidates)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Select the most likely pupil contour based on size, circularity, etc.
    pupil_contour = select_pupil_contour(contours)

    # Kalman filter initialization (if not already initialized)
    if not hasattr(track_pupil, "kalman"):
        track_pupil.kalman = cv2.KalmanFilter(4, 2)
        track_pupil.kalman.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
        track_pupil.kalman.transitionMatrix = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32)
        track_pupil.kalman.processNoiseCov = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32) * 0.03

    # Kalman filter prediction and correction
    if pupil_contour is not None:
        M = cv2.moments(pupil_contour)
        pupil_x = int(M['m10'] / M['m00'])
        pupil_y = int(M['m01'] / M['m00'])
        predicted = track_pupil.kalman.predict()
        measured = np.array([[np.float32(pupil_x)], [np.float32(pupil_y)]])
        track_pupil.kalman.correct(measured)
        return predicted[0:2]
    else:
        return None
def select_pupil_contour(contours):
    """Selects the most likely pupil contour based on size and circularity."""

    best_contour = None
    max_area = 0
    max_circularity = 0

    for contour in contours:
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        circularity = 4 * np.pi * area / (perimeter * perimeter)

        if area > max_area and circularity > max_circularity:
            max_area = area
            max_circularity = circularity
            best_contour = contour

    return best_contour

def calculate_gaze_direction(pupil_position, eye_center, calibration_data):
    """Calculates gaze direction based on pupil position, eye center, and calibration data."""
    x_offset = pupil_position[0] - eye_center[0]
    y_offset = pupil_position[1] - eye_center[1]

    gaze_x = calibration_data['x_slope'] * x_offset + calibration_data['x_intercept']
    gaze_y = calibration_data['y_slope'] * y_offset + calibration_data['y_intercept']

    gaze_vector = np.array([gaze_x, gaze_y])
    return gaze_vector

ap = argparse.ArgumentParser()
ap.add_argument("-p", "--shape-predictor", default="shape_predictor_68_face_landmarks.dat",
                help="path to facial landmark predictor")
args = vars(ap.parse_args())

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(args["shape_predictor"])

EYE_CLOSED_THRESH = 0.19
MOUTH_CLOSED_THRESH = 0.55

metrics = {"left_eye": "Open", "right_eye": "Open", "mouth": "Open", "direction": "Front", "Using_Phone": "No", "Pupil_direction": "Center"}
direction = "Front"

def generate_frames():
    global phone_usage_start, ear_history
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()

    direction = "Front"



    ear_filter = EARFilter()

    focal_length = frame.shape[1]
    center = (frame.shape[1] / 2, frame.shape[0] / 2)
    camera_matrix = np.array(
        [[focal_length, 0, center[0]],
         [0, focal_length, center[1]],
         [0, 0, 1]], dtype="double"
    )

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)

        results1 = model1(frame)[0]

        blank_image = gray

        if len(faces) > 0:
            face = faces[0]
            landmarks = predictor(gray, face)
            shape = face_utils.shape_to_np(landmarks)

            for n in range(0, 68):
                x = landmarks.part(n).x
                y = landmarks.part(n).y
                cv2.circle(blank_image, (x, y), 1, (0, 0, 0), -1)

            image_points = np.array([
                (landmarks.part(30).x, landmarks.part(30).y),
                (landmarks.part(8).x, landmarks.part(8).y),
                (landmarks.part(36).x, landmarks.part(36).y),
                (landmarks.part(45).x, landmarks.part(45).y),
                (landmarks.part(48).x, landmarks.part(48).y),
                (landmarks.part(54).x, landmarks.part(54).y)
            ], dtype="double")

            model_points = np.array([
                (0.0, 0.0, 0.0),
                (0.0, -330.0, -65.0),
                (-225.0, 170.0, -135.0),
                (225.0, 170.0, -135.0),
                (-150.0, -150.0, -125.0),
                (150.0, -150.0, -125.0)
            ])

            mouth = shape[48:68]
            mar = mouth_aspect_ratio(mouth)

            dist_coeffs = np.zeros((4, 1))
            (success, rotation_vector, translation_vector) = cv2.solvePnP(model_points, image_points, camera_matrix,
                                                                          dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE)

            rmat, _ = cv2.Rodrigues(rotation_vector)
            _, _, _, _, _, _, euler_angle = cv2.decomposeProjectionMatrix(
                np.concatenate((rmat, translation_vector), axis=1))

            pitch, yaw, roll = [math.radians(_[0]) for _ in euler_angle]
            pitch = math.degrees(math.asin(math.sin(pitch)))
            roll = -math.degrees(math.asin(math.sin(roll)))
            yaw = math.degrees(math.asin(math.sin(yaw)))

            if yaw > 30:
                new_direction = "Right"
            elif yaw < -30:
                new_direction = "Left"
            elif pitch > 15:
                new_direction = "Up"
            elif pitch < -15:
                new_direction = "Down"
            else:
                new_direction = "Front"

            if new_direction != direction:
                direction = new_direction
                metrics["direction"] = new_direction



            leftEye = np.array([(landmarks.part(i).x, landmarks.part(i).y) for i in range(42, 48)])
            rightEye = np.array([(landmarks.part(i).x, landmarks.part(i).y) for i in range(36, 42)])
            leftEAR = eye_aspect_ratio(leftEye)
            rightEAR = eye_aspect_ratio(rightEye)

            leftEye = shape[42:48]
            rightEye = shape[36:42]

            leftEyeCenter = leftEye.mean(axis=0).astype("int")
            rightEyeCenter = rightEye.mean(axis=0).astype("int")

            # Track pupils
            left_pupil = track_pupil(leftEye)
            right_pupil = track_pupil(rightEye)

            # Calculate gaze direction (if pupils are detected)
            if left_pupil is not None and right_pupil is not None:
                left_gaze = calculate_gaze_direction(left_pupil, leftEyeCenter, calibration_data)
                right_gaze = calculate_gaze_direction(right_pupil, rightEyeCenter, calibration_data)

            if left_pupil is not None:
                cv2.circle(blank_image, (int(left_pupil[0]), int(left_pupil[1])), 3, (255, 255, 0), -1)
            if right_pupil is not None:
                cv2.circle(blank_image, (int(right_pupil[0]), int(right_pupil[1])), 3, (255, 255, 0), -1)



            ear = (leftEAR + rightEAR) / 2.0
            ear = ear_filter.update(ear)

            (nose_end_point2D, jacobian) = cv2.projectPoints(np.array([(0.0, 0.0, 800.0)]), rotation_vector,
                                                             translation_vector, camera_matrix, dist_coeffs)

            p1 = (int(image_points[0][0]), int(image_points[0][1]))
            p2 = (int(nose_end_point2D[0][0][0]), int(nose_end_point2D[0][0][1]))

            cv2.line(blank_image, p1, p2, (0, 0, 0), 2)

            def draw_detections(blank_image, x1, y1, x2, y2, score, class_name):
                color = (0, 0, 0)
                cv2.rectangle(blank_image, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)

                cv2.putText(blank_image, class_name, (int(x1), int(y1 - 30)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

                cv2.putText(blank_image, f'Confidence: {score:.2f}', (int(x1), int(y1 - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

                # print(f"Detected: {class_name}, Score: {score}")

            for result in results1.boxes.data.tolist():
                x1, y1, x2, y2, score, class_id = result
                class_name = results1.names[int(class_id)].upper()
                if score > threshold_m:
                    draw_detections(blank_image, x1, y1, x2, y2, score, class_name)

            if "CELL PHONE" in [class_name for result in results1.boxes.data.tolist()]:
                metrics["Using_Phone"] = "Yes"
            else:
                metrics["Using_Phone"] = "No"

            # Determine the state of the eyes
            if leftEAR < EYE_CLOSED_THRESH:
                metrics["left_eye"] = "Closed"
            else:
                metrics["left_eye"] = "Open"

            if rightEAR < EYE_CLOSED_THRESH:
                metrics["right_eye"] = "Closed"
            else:
                metrics["right_eye"] = "Open"

            # Determine the state of the mouth
            if mar < MOUTH_CLOSED_THRESH:
                metrics["mouth"] = "Closed"
            else:
                metrics["mouth"] = "Open"


        else:
            print("No faces detected.")
        # cv2.imshow("Output", blank_image)
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        # break

        # cap.release()
        # cv2.destroyAllWindows()

        (flag, encodedImage) = cv2.imencode(".jpg", blank_image)
        if not flag:
            continue

        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_metrics')
def get_metrics():
    global metrics
    return jsonify(metrics)


if __name__ == '__main__':
    app.run(debug=True, threaded=True)
