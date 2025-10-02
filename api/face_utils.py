# api/face_utils.py

import cv2
import numpy as np

# This is the confidence threshold for the final match.
MATCH_THRESHOLD = 0.8
# The standard size we'll resize all detected faces to.
FACE_SIZE = (100, 100)
# Path to the Haar Cascade model file.
CASCADE_PATH = 'haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

def _get_face_crop(image_data_np_array):
    """A helper function to detect, crop, and standardize a face from an image."""
    
    # First, decode the image array into a color image
    img = cv2.imdecode(image_data_np_array, cv2.IMREAD_COLOR)
    if img is None:
        return None
    
    # Convert to grayscale for the detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Detect faces in the image
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )

    # We assume only one face is in the image for this project
    if len(faces) == 1:
        x, y, w, h = faces[0]
        # Crop the original grayscale image to just the face
        face_crop = gray[y:y+h, x:x+w]
        # Resize the face to a standard size for consistent comparison
        standardized_face = cv2.resize(face_crop, FACE_SIZE)
        return standardized_face
    
    # Return None if zero or more than one face is found
    return None


def compare_faces(stored_template_path, live_image_data) -> bool:
    """
    Compares a stored face template with a live image from the webcam.
    Now uses Haar Cascade to first detect and crop the faces.
    """
    try:
        # --- Process Stored Template ---
        with open(stored_template_path, "rb") as f:
            stored_np_arr = np.frombuffer(f.read(), np.uint8)
        stored_face = _get_face_crop(stored_np_arr)

        # --- Process Live Image ---
        live_np_arr = np.frombuffer(live_image_data.read(), np.uint8)
        live_face = _get_face_crop(live_np_arr)
        
        # If a face wasn't found in either image, authentication fails
        if stored_face is None or live_face is None:
            print("Could not find a single face in one or both images.")
            return False

        # --- Template Matching on the Cropped Faces ---
        result = cv2.matchTemplate(live_face, stored_face, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        best_match_score = max_val

        print(f"Face match score (cropped): {best_match_score}")

        return best_match_score > MATCH_THRESHOLD

    except Exception as e:
        print(f"An error occurred during face comparison: {e}")
        return False