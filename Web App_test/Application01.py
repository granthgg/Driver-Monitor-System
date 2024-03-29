from urllib import request

from flask import Flask, render_template, Response, jsonify
import cv2
import dlib
import numpy as np
import math
from scipy.spatial import distance as dist
from imutils import face_utils
import argparse
from ultralytics import YOLO
import time

from flask_socketio import SocketIO, emit


app = Flask(__name__)
socketio = SocketIO(app)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

model1 = YOLO('best_mobile.pt')
threshold_m = 0.8

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

def get_pupil_direction(eye_center, pupil_position):
    """Determine the direction of the pupil."""
    relative_x = pupil_position[0] - eye_center[0]
    relative_y = pupil_position[1] - eye_center[1]

    # Calculate angle (in radians)
    angle = math.atan2(relative_y, relative_x)
    if abs(angle) <= math.pi / 8:
        p_direction = "Center"
    elif angle > math.pi / 4:
        p_direction = "Up-Right"
    elif angle > 0:
        p_direction = "Right"
    elif angle > -math.pi / 4:
        p_direction = "Down-Right"
    elif angle > -math.pi / 2:
        p_direction = "Down"
    elif angle > -3 * math.pi / 4:
        p_direction = "Down-Left"
    elif angle > -math.pi:
        p_direction = "Left"
    else:
        p_direction = "Up-Left"

    return p_direction

WEIGHTS = {
                "Using_Phone": -0.3,
                "Eyes_Open": 0.1,
                "Mouth_Opened": -0.1,
                "Yawning": -0.5,
                "Talking": -0.3,
                "Sleeping": -0.9
            }

def calculate_alertness(metrics):
    alertness_score = 1
    if metrics["Using_Phone"] == "Yes":
        alertness_score += WEIGHTS["Using_Phone"]
    if metrics["left_eye"] == "Closed":
        alertness_score += WEIGHTS["Eyes_Open"]
    if metrics["right_eye"] == "Closed":
        alertness_score += WEIGHTS["Eyes_Open"]
    if metrics["mouth"] == "Open":
        if metrics["Yawning"] == "Yes":
            alertness_score += WEIGHTS["Yawning"]
        elif metrics["Talking"] == "Yes":
            alertness_score += WEIGHTS["Talking"]
    else:
        alertness_score += WEIGHTS["Mouth_Opened"]
    if metrics["State"] == "Sleeping":
        alertness_score += WEIGHTS["Sleeping"]

    alertness_score = min(max(alertness_score, 0), 1)

    return alertness_score


ap = argparse.ArgumentParser()
ap.add_argument("-p", "--shape-predictor", default="shape_predictor_68_face_landmarks.dat",
                help="path to facial landmark predictor")
args = vars(ap.parse_args())

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(args["shape_predictor"])

EYE_CLOSED_THRESH = 0.19
MOUTH_CLOSED_THRESH = 0.40
MOUTH_CLOSE_THRESH = 0.35
SLEEP_THRESHOLD = 8
YAWN_THRESHOLD = 0.55
YAWN_COUNT_THRESHOLD = 8
TALKING_SEQ_THRESHOLD = 4


talking_seq_count = 0
sleep_counter = 0
yawn_counter = 0

mar_values = []
yawn_detected = False


metrics = {"left_eye": "Open", "right_eye": "Open", "mouth": "Open", "direction": "Front", "Using_Phone": "No",
           "Pupil_direction": "Center", "Talking": "No", "Yawning": "No", "State": "Awake"}

direction = "Front"




def generate_frames():
    global phone_usage_start, ear_history, sleep_counter, yawn_counter, talking_seq_count
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()

    direction = "Front"

    def pixelReader(img, center_x, center_y, size=10):
        """Scan the eye region for dark pixels that might indicate the pupil."""
        black_pixels = []
        for y in range(center_y - size, center_y + size):
            for x in range(center_x - size, center_x + size):
                if img[y, x] < 80:  #
                    black_pixels.append((x, y))
        return black_pixels

    def getPupilPoint(frame, black_pixels):
        """Find the most central dark pixel, assuming it to be the pupil."""
        if black_pixels:
            radius = 5  # Adjust as needed
            center = black_pixels[0]  # Initial darkest pixel
            nearby_pixels = [p for p in black_pixels if dist.euclidean(p, center) <= radius]

            pupil_x = sum([p[0] for p in black_pixels]) // len(black_pixels)
            pupil_y = sum([p[1] for p in black_pixels]) // len(black_pixels)
            return (pupil_x, pupil_y)
        return None

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

            if leftEAR > EYE_CLOSED_THRESH and rightEAR > EYE_CLOSED_THRESH:
                leftBlackPixels = pixelReader(gray, leftEyeCenter[0], leftEyeCenter[1], size=10)
                rightBlackPixels = pixelReader(gray, rightEyeCenter[0], rightEyeCenter[1], size=10)

                leftPupil = getPupilPoint(gray, leftBlackPixels)
                rightPupil = getPupilPoint(gray, rightBlackPixels)

                if leftPupil:
                    cv2.circle(blank_image, leftPupil, 3, (255, 255, 0), -1)
                    left_pupil_direction = get_pupil_direction(leftEyeCenter, leftPupil)
                else:
                    left_pupil_direction = "Unknown"

                if rightPupil:
                    cv2.circle(blank_image, rightPupil, 3, (255, 255, 0), -1)
                    right_pupil_direction = get_pupil_direction(rightEyeCenter, rightPupil)
                else:
                    right_pupil_direction = "Unknown"

                metrics["Pupil_direction"] = left_pupil_direction + " , " + right_pupil_direction

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

            # Determine Sleeping
            if metrics["left_eye"] == "Closed" and metrics["right_eye"] == "Closed" and metrics["mouth"] == "Closed":
                sleep_counter += 1
            else:
                sleep_counter = 0

            if sleep_counter > SLEEP_THRESHOLD:
                metrics["State"] = "Sleeping"
            else:
                metrics["State"] = "Awake"

            # Determine Yawn
            if metrics["mouth"] == "Open" and mar > YAWN_THRESHOLD:
                yawn_counter += 1
            else:
                yawn_counter = 0

            if yawn_counter > YAWN_COUNT_THRESHOLD:
                metrics["Yawning"] = "Yes"
                yawn_detected = True
            else:
                metrics["Yawning"] = "No"
                yawn_detected = False

            # Talking detection logic
            mar_values.append(mar)
            if len(mar_values) > 10:
                mar_values.pop(0)

                talking_sequence_count = 0  # Reset the count for each window of analysis
                for i in range(1, len(mar_values)):
                    # Detect sequences of opening and closing
                    if mar_values[i] > MOUTH_CLOSE_THRESH > mar_values[i - 1]:
                        talking_sequence_count += 1

                # Update metrics based on the detected sequences
                if talking_sequence_count >= TALKING_SEQ_THRESHOLD and not yawn_detected:
                    metrics["Talking"] = "Yes"
                else:
                    metrics["Talking"] = "No"


            data = {
                'metrics': metrics,
                'latitude': '30.7654865',
                'longitude': '76.6105031',

            }
            socketio.emit('metrics_update', data)
            time.sleep(0.4)


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

        yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n'


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



@app.route('/get_alertness')
def get_alertness():
    score = calculate_alertness(metrics)
    return jsonify({'alertness_score': score})


@app.route('/update_location', methods=['POST'])
def update_location():
    if request.method == 'POST':
        location_data = request.get_json()
        latitude = location_data['latitude']
        longitude = location_data['longitude']
        return jsonify(success=True)


if __name__ == '__main__':
    app.run(debug=True, threaded=True, port=5000, host='0.0.0.0')
