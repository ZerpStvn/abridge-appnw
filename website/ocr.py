import os
import io
import base64
import numpy as np
from PIL import Image, ImageEnhance
import cv2 as cv
import pytesseract as pt
from PyPDF2 import PdfReader

async def test_ocr_engine():
    try:
        img_path = os.path.join(os.path.dirname(__file__), 'assets', 'ok.jpg')
        img = cv.imread(img_path)
        img = preprocess_image_for_ocr(img)
        text = pt.image_to_string(img)
        return "Working", None, text
    except Exception as e:
        return "NOT working", str(e), None

async def multi_ocr(b64_images: list):
    results = []
    for b64_image in b64_images:
        try:
            image = base64.b64decode(b64_image["image"])
            image = Image.open(io.BytesIO(image))
            image = preprocess_image_for_ocr(np.array(image))
            text = pt.image_to_string(image)
            results.append({"name": b64_image["name"], "text": " ".join(text.split())})
        except Exception as e:
            results.append({"name": b64_image["name"], "error": str(e)})
    return results

def preprocess_image_for_ocr(img):
    # Convert to grayscale
    img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    # Apply thresholding
    _, img = cv.threshold(img, 128, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
    return img

def extract_text_from_image(image_path):
    img = Image.open(image_path)
    img = preprocess_image_for_ocr(np.array(img))
    text = pt.image_to_string(img)
    return text

def extract_text_from_pdf(pdf_path):
    text = ''
    try:
        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)
            for page in reader.pages:
                text_elements = page.extract_text()
                if text_elements:
                    text += ' '.join(text_elements) if isinstance(text_elements, list) else text_elements
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    return text