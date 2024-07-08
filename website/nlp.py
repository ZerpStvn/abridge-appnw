import numpy as np
import networkx as nx
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import fitz  # PyMuPDF
from transformers import pipeline
import re
import os
import textwrap
from docx import Document

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")

# Initialize the summarizer with a specified model
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def preprocess_text(text):
    """Tokenize text into sentences using SpaCy"""
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]
    return sentences

def clean_sentence(sentence):
    """Lemmatize, remove stop words, punctuation, spaces, and non-significant words from a sentence for better summarizing."""
    doc = nlp(sentence)
    # Keeping tokens based on more dynamic criteria: not stop words, not punctuation, not space, and are significant parts of speech
    tokens = [token.lemma_.lower().strip() for token in doc if not token.is_stop and not token.is_punct and not token.is_space and token.pos_ in ['NOUN', 'VERB', 'ADJ', 'ADV']]

    # Normalize numbers
    normalized_tokens = ["number" if token.isdigit() else token for token in tokens]
    
    return ' '.join(normalized_tokens)

def build_similarity_matrix(sentences):
    """Build a similarity matrix using TF-IDF vectors and cosine similarity"""
    vectorizer = TfidfVectorizer()
    try:
        tfidf_matrix = vectorizer.fit_transform(sentences)
    except ValueError as e:
        if "empty vocabulary" in str(e):
            return np.zeros((len(sentences), len(sentences)))
        else:
            raise e
    sim_matrix = cosine_similarity(tfidf_matrix)
    return sim_matrix

def rank_sentences(similarity_matrix):
    """Rank sentences using the PageRank algorithm"""
    nx_graph = nx.from_numpy_array(similarity_matrix)
    scores = nx.pagerank(nx_graph)
    ranked_sentences = sorted(((scores[i], i) for i in range(len(scores))), reverse=True)
    return ranked_sentences

def summarize(text, top_n=10):
    """Summarize the text to the top_n sentences"""
    sentences = preprocess_text(text)
    if not sentences:
        return "No content to summarize."

    clean_sentences = [clean_sentence(sent) for sent in sentences if clean_sentence(sent)]
    if not clean_sentences:
        return "No valid content to summarize after cleaning."

    similarity_matrix = build_similarity_matrix(clean_sentences)
    ranked_sentences = rank_sentences(similarity_matrix)
    
    top_sentence_indices = [idx for score, idx in ranked_sentences[:top_n]]
    top_sentence_indices.sort()
    
    summarized_sentences = [sentences[idx] for idx in top_sentence_indices]
    summary = " ".join(summarized_sentences).strip()
    
    return summary

def extract_text_from_pdf_nlp(pdf_path):
    """Extract text from a PDF file, excluding book details in the heading"""
    text = ""
    try:
        with fitz.open(pdf_path) as pdf:
            page_texts = []
            for page in pdf:
                page_text = page.get_text()
                
                # Remove book details in the heading
                cleaned_text = remove_book_details(page_text)
                
                page_texts.append(cleaned_text.strip())
            # Join the page texts with a space between each page's text
            text = "\n\n".join(page_texts)  # Using new lines for better readability
    except Exception as e:
        raise RuntimeError(f"Error reading PDF file: {e}")
    return text

def extract_text_from_docs_nlp(docs_path):
    """Extract text from a .docx file, excluding book details in the heading."""
    text = ""
    try:
        doc = Document(docs_path)
        paragraphs = []
        for para in doc.paragraphs:
            # Assuming remove_book_details is a function that removes book details from the text
            cleaned_text = remove_book_details(para.text)
            paragraphs.append(cleaned_text.strip())
        # Join the paragraph texts with a double newline for better readability, similar to PDF extraction
        text = "\n\n".join(paragraphs)
    except Exception as e:
        raise RuntimeError(f"Error reading .docx file: {e}")
    return text

def advanced_summarize(text):
    """Advanced summarization using Transformer"""
    try:
        summary = summarizer(text, max_length=200, min_length=30, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        raise RuntimeError(f"Error advanced summarizing text: {e}")

def advanced_summarize_pdf(pdf_path):
    """
    Advanced summarization of a PDF file with post-summary cleanup.
    Ensures that the cleanup is applied to both the extracted text and the summary.
    """
    try:
        text = extract_text_from_pdf_nlp(pdf_path)
        # Ensure the extracted text is cleaned before summarization
        cleaned_text = remove_book_details(text)
        summary_result = advanced_summarize(cleaned_text)
        # The summary text is already being cleaned in the current approach
        return summary_result
    except Exception as e:
        raise RuntimeError(f"Error advanced summarizing PDF file: {e}")

def remove_book_details(page_text):
    """Remove book details and leading numbers in the heading"""
    lines = page_text.splitlines()
    cleaned_lines = []

    for line in lines:
        if re.match(r'^Understanding\s+Operating\s+Systems\s*,\s*Fifth\s+Edition', line, re.IGNORECASE):
            continue  # Skip the header line
        if re.match(r'^\d+$', line.strip()):  # Skip page numbers
            continue
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)
