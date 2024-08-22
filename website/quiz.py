import random
import os
import fitz  # PyMuPDF
import spacy
from openai import OpenAI
from flask_login import current_user
from datetime import datetime
from .models import Quiz, Question  # Ensure Question model is included
from . import db
from flask import render_template, request, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename

# Load SpaCy model for sentence segmentation
nlp = spacy.load("en_core_web_sm")

# Set up OpenAI API key
client = OpenAI(api_key='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')

def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ''
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += page.get_text()
    return text

def preprocess_text(text):
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]
    return sentences

def generate_questions_from_summary(summary, num_questions=10, num_choices=4):
    sentences = preprocess_text(summary)
    questions = []
    for sentence in sentences:
        response = client.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Generate a question with {num_choices} choices and indicate which one is correct based on the following sentence: {sentence}"}
            ],
            max_tokens=300,
            temperature=0.5
        )
        generated_text = response.choices[0].message.content.strip()
        # Process response to extract question and choices
        lines = generated_text.split('\n')
        if len(lines) < num_choices + 1:
            continue

        question_text = lines[0].strip()
        choices = [line.strip() for line in lines[1:num_choices + 1]]
        correct_answer = lines[num_choices + 1].strip() if len(lines) > num_choices else None

        if not correct_answer or not question_text:
            continue

        # Ensure choices include the correct answer
        questions.append({
            'question': truncate_question(question_text, 10),
            'choices': choices,
            'correct_answer': correct_answer
        })

    random.shuffle(questions)
    return questions[:num_questions]

def truncate_question(question, word_limit=20):
    words = question.split()
    if len(words) > word_limit:
        return ' '.join(words[:word_limit]) + '...'
    return question

def truncate_choice(choice, word_limit=20):
    words = choice.split()
    if len(words) > word_limit:
        return ' '.join(words[:word_limit]) + '...'
    return choice

def truncate_text(text, word_limit):
    words = text.split()
    return ' '.join(words[:word_limit])

def generate_dynamic_title(filename):
    return f"Quiz for {filename} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

def get_quiz_id(title):
    new_quiz = Quiz(title=title, user_id=current_user.id)
    db.session.add(new_quiz)
    db.session.commit()
    return new_quiz.id