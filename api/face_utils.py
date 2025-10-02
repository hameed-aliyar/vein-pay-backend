# api/face_utils.py

import cv2
import numpy as np

# This is the confidence threshold. A score higher than this will be considered a match.
# You can tune this value. 0.8 means an 80% confidence.
MATCH_THRESHOLD = 0.8

def compare_faces(stored_template_path, live_image_data) -> bool:
    """
    Compares a stored face template with a live image from the webcam.

    :param stored_template_path: The file path to the stored reference image.
    :param live_image_data: The image data from the live capture (in memory).
    :return: True if it's a match, False otherwise.
    """
    try:
        # Load the stored template image from its file path in grayscale
        template_img = cv2.imread(stored_template_path, 0)
        if template_img is None:
            print(f"Error: Could not read stored template from {stored_template_path}")
            return False

        # Load the live image from the in-memory data
        # Convert the file data to a numpy array
        np_arr = np.frombuffer(live_image_data.read(), np.uint8)
        # Decode the array into an image, in grayscale
        live_img = cv2.imdecode(np_arr, cv2.IMREAD_GRAYSCALE)
        if live_img is None:
            print("Error: Could not decode live image data.")
            return False

        # --- Template Matching using Normalized Cross-Correlation ---
        # This method slides the template over the live image and finds the best match
        result = cv2.matchTemplate(live_img, template_img, cv2.TM_CCOEFF_NORMED)
        
        # Get the score of the best match
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        best_match_score = max_val

        print(f"Face match score: {best_match_score}")

        # If the best match score is above our threshold, it's a success
        if best_match_score > MATCH_THRESHOLD:
            return True
        else:
            return False

    except Exception as e:
        print(f"An error occurred during face comparison: {e}")
        return False