import re
from docx import Document
import fitz
from openai import OpenAI
import os

# Initialize OpenAI client
client = OpenAI(api_key='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')

def extract_text(filename):
    """
    Extracts text from a file based on its extension.
    """
    try:
        if filename.endswith(".txt"):
            with open(filename, "r") as f:
                return f.read()
        elif filename.endswith((".doc", ".docx")):
            doc = Document(filename)
            full_text = ""
            for paragraph in doc.paragraphs:
                full_text += paragraph.text + "\n"
            return full_text
        elif filename.endswith(".pdf"):
            doc = fitz.open(filename)
            text = ""
            for page in doc:
                text += page.get_text()
            return text
        else:
            return "File format not supported."
    except FileNotFoundError:
        return "File not found."
    except Exception as e:
        return f"An error occurred: {e}"

def clean_text(text):
    """
    Cleans the extracted text for better readability.
    """
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()
    text = re.sub(r'(\n|^)([A-Z][A-Za-z0-9& ]+):', r'\1\n\n\2:', text)
    text = re.sub(r'\n(\d+\.)', r'\n\n\1', text)
    text = re.sub(r'\n(-|\*)', r'\n\n\1', text)
    return text

def extract_definitions(text):
    """
    Extracts key terms and their definitions from a given text.
    """
    lines = text.split("\n")
    definitions = {}
    current_term = None
    for line in lines:
        stripped_line = line.strip()
        if re.match(r"^[A-Z][A-Za-z0-9& ]+(:|\s*$)", stripped_line):
            current_term = stripped_line.rstrip(":").strip()
            definitions[current_term] = ""
        elif current_term:
            definitions[current_term] += stripped_line + " "
    for term in definitions:
        definitions[term] = definitions[term].strip()
        definitions[term] = re.sub(r'•\s*', '\n  • ', definitions[term])
        definitions[term] = re.sub(r'\n\s*\n', '\n', definitions[term]).strip()
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', definitions[term])
        summarized_definition = ' '.join(sentences[:3])
        definitions[term] = summarized_definition
    return definitions

def format_output(definitions):
    """
    Formats the extracted definitions for better readability.
    """
    formatted_output = ""
    for term, definition in definitions.items():
        formatted_output += f"{term}:\n{definition}\n\n"
    return formatted_output.strip()

def summarize_text_with_openai(text):
    """
    Uses OpenAI to summarize the given text.
    """
    try:
        # Create completion request
        response = client.chat.completions.create(model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Summarize the following text and format it as study notes:\n\n{text}"}
        ],
        max_tokens=500,
        temperature=0.5)

        # Extract summary from response
        summary = response.choices[0].message.content.strip()
        return summary

    except Exception as e:
        return f"An error occurred while summarizing with OpenAI: {e}"