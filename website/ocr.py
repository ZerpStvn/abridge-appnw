from PIL import Image
import pytesseract
import cv2
import numpy as np
from transformers import pipeline

summarizer = pipeline("summarization")

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
        return extract_text_from_image(file_path)
    else:
        return "Unsupported file type. Please provide an image file."

def summarize_text(text):
    """
    Summarizes the given text using a pre-trained model.
    
    Args:
    - text: The text to summarize.
    
    Returns:
    - The summarized text.
    """
    summary = summarizer(text, max_length=130, min_length=30, do_sample=False)
    return summary[0]['summary_text']