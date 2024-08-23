from PIL import Image
import pytesseract
import cv2
import numpy as np
import os
from openai import OpenAI

client = OpenAI(api_key='SECRET_KEY')

# Set your OpenAI API key

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

def summarize_text_with_openai(text):
    # Call the OpenAI API to summarize the text
    response = client.completions.create(engine="gpt-4",  # or use any other GPT-3 model
    prompt=f"Summarize the following text:\n\n{text}",
    max_tokens=150,  # Adjust the token count based on your needs
    n=1,
    stop=None,
    temperature=0.5)
    summary = response.choices[0].text.strip()
    return summary

def extract_text_from_file(file_path):
    # Check if the file is an image
    if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif')):
        extracted_text = extract_text_from_image(file_path)
        # Clean the extracted text
        cleaned_text = clean_sentence(extracted_text)
        # Summarize the cleaned text using OpenAI
        summarized_text = summarize_text_with_openai(cleaned_text)
        return summarized_text
    else:
        return "Unsupported file type. Please provide an image file."
