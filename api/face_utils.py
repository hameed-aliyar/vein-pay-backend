import cv2
import numpy as np
from django.conf import settings
import os
from io import BytesIO # Needed for handling processed image data

# Initialize the LBPH Face Recognizer globally.
RECOGNIZER = cv2.face.LBPHFaceRecognizer_create(
    radius=1,
    neighbors=8,
    grid_x=8,
    grid_y=8
)

# Define the acceptable distance for LBPH.
# This threshold (e.g., 60-80) is an empirical measure of dissimilarity (distance)
# calculated by the LBPH algorithm. It is NOT the SAD score.
LBPH_DISTANCE_THRESHOLD = 150 
FACE_SIZE = (100, 100) 

# Haar Cascade is initialized globally
CASCADE_PATH = os.path.join(
    settings.BASE_DIR, "api", "haarcascade_frontalface_default.xml"
)
if not os.path.exists(CASCADE_PATH):
    raise FileNotFoundError(f"Haar Cascade model not found at {CASCADE_PATH}")

face_cascade = cv2.CascadeClassifier(CASCADE_PATH)


def preprocess_image_for_comparison(image_data, is_file_path=False):
    """
    Decodes the image, converts to grayscale, detects the face, crops, and resizes to 100x100.
    Returns the preprocessed grayscale face crop, or None if no face is detected.
    """
    if is_file_path:
        # Load stored template directly as grayscale
        img = cv2.imread(image_data, cv2.IMREAD_GRAYSCALE)
    else:
        # For live image (from request)
        img_array = np.frombuffer(image_data.read(), np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    if img is None:
        return None

    # Ensure it's grayscale for processing (necessary for LBPH)
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    # Apply Histogram Equalization to normalize brightness (key for LBPH)
    equalized_gray = cv2.equalizeHist(gray)

    # Detect face (using cascade as before)
    faces = face_cascade.detectMultiScale(equalized_gray, scaleFactor=1.1, minNeighbors=5)

    if len(faces) == 0:
        return None  # No face detected

    # Use the first detected face
    x, y, w, h = faces[0]
    face_crop = equalized_gray[y : y + h, x : x + w]

    # Resize to the standard size (100x100)
    return cv2.resize(face_crop, FACE_SIZE)


def compare_faces(stored_template_path, live_image_data):
    """
    Compares two faces using the Local Binary Patterns Histogram (LBPH) method.
    """
    stored_face = preprocess_image_for_comparison(
        stored_template_path, is_file_path=True
    )
    live_face = preprocess_image_for_comparison(live_image_data, is_file_path=False)

    if stored_face is None or live_face is None:
        print("Debug: No face detected in one or both images after pre-processing.")
        return False

    # LBPH requires training on the known face before prediction
    faces = [stored_face]
    labels = np.array([1])  # Training with a dummy label

    try:
        # Train the model with the stored template
        RECOGNIZER.train(faces, labels)

        # Predict the label and get the confidence (distance) for the live face
        predicted_label, distance = RECOGNIZER.predict(live_face)

        print(
            f"Debug: LBPH Distance = {distance:.2f} (Threshold: < {LBPH_DISTANCE_THRESHOLD})"
        )

        # FIX: Remove the 'predicted_label == 1' check. Trust the distance score alone.
        # This prevents false rejections when the distance is good but the label check fails.
        if distance < LBPH_DISTANCE_THRESHOLD:
            return True

    except cv2.error as e:
        print(f"OpenCV Error during prediction: {e}")
        return False

    return False


def validate_face_present(uploaded_file):
    """
    Checks if a face is present in the uploaded file without saving the result.
    Raises ValueError if no face is detected.
    """
    # This logic is correct for validation and is kept.
    uploaded_file.seek(0)
    # ... (rest of validate_face_present logic from previous step, ensuring seek(0) is at the end) ...
    # NOTE: You should ensure the logic inside this function uses the new 'preprocess_image_for_comparison' 
    # logic up to the face detection part to maintain consistency.
    
    # Simple check for now: just attempt to preprocess and check for None
    temp_file = uploaded_file # Temporary alias
    temp_file.seek(0)
    
    # We need a new function for registration since this one is now complex
    # Let's keep the old logic but use the new preprocessing parts
    img_array = np.frombuffer(temp_file.read(), np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Failed to decode image data.")

    # Ensure it's grayscale for processing
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
        
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    if len(faces) == 0:
        raise ValueError("No face detected in the live image.")
    
    # Reset file pointer after reading so it can be read again in PaymentView
    uploaded_file.seek(0)
    return True


def process_and_validate_face_for_registration(uploaded_file):
    """
    Validates face detection and returns the processed 100x100 grayscale face
    as a Django ContentFile, or raises an exception.
    """
    
    # Read the content of the uploaded file
    uploaded_file.seek(0) # Ensure we read from the start
    img_array = np.frombuffer(uploaded_file.read(), np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Failed to decode image data.")

    # Get the processed face using the common function
    # Note: We must re-read the file if the above logic is used. A cleaner way
    # is to pass the decoded array, but for now, we use the simpler I/O path.
    uploaded_file.seek(0) # Reset pointer again for the preprocess function
    processed_face = preprocess_image_for_comparison(uploaded_file, is_file_path=False)
    
    if processed_face is None:
        raise ValueError("No face detected in the uploaded image. Please try again.")

    # Encode the processed face back into a JPEG byte stream
    is_success, buffer = cv2.imencode(".jpg", processed_face)
    
    if not is_success:
        raise ValueError("Failed to encode processed face image.")
        
    # Create a Django ContentFile to be saved by the model
    from django.core.files.base import ContentFile
    content_file = ContentFile(buffer.tobytes(), name=f'template_{uploaded_file.name}.jpg')
    
    return content_file
