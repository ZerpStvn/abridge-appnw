from PIL import Image
import pytesseract
import cv2
import numpy as np
import os
from .nlp import clean_sentence, summarize

# Assume clean_sentence function is defined here or imported

def extract_text_from_image(image_path):
    # Load the image
    img = cv2.imread(image_path)
    # Preprocess the image for OCR
    img_preprocessed = preprocess_image_for_ocr(img)
    # Convert the image to string
    text = pytesseract.image_to_string(img_preprocessed)
    return text

def preprocess_image_for_ocr(img):
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Apply thresholding
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

def extract_text_from_file(file_path):
    # Check if the file is an image
    if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif')):
        extracted_text = extract_text_from_image(file_path)
        # Clean the extracted text
        cleaned_text = clean_sentence(extracted_text)
        summarized_text = summarize(cleaned_text)
        return summarized_text  # Change to summarized_text if summarization is applied
    else:
        return "Unsupported file type. Please provide an image file."