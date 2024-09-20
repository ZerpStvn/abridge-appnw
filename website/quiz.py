import random
import spacy
from openai import OpenAI
from flask_login import current_user
from datetime import datetime
from .models import Quiz, Question, Upload
from . import db
from flask import render_template, flash
import time
import re

# Set up OpenAI key
client = OpenAI(api_key='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')

def generate_questions_from_summary(summary, num_questions=10):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Generate a {num_questions}-question multiple-choice quiz from the following summary. Format the response as follows: \n1. Question: [Question Text]\n2. Choices:\n   A) [Choice 1]\n   B) [Choice 2]\n   C) [Choice 3]\n   D) [Choice 4]\n3. Answer: [Correct Answer]\n\nSummary: {summary}"}
        ]
    )

    generated_text = response.choices[0].message.content.strip()

    # Use regex to extract all questions, choices, and answers
    question_matches = re.findall(r"Question: (.+)", generated_text)
    choices_matches = re.findall(r"Choices:\s+A\) (.+)\s+B\) (.+)\s+C\) (.+)\s+D\) (.+)", generated_text)
    answer_matches = re.findall(r"Answer: ([A-D])", generated_text)
    
    # Ensure all components are extracted correctly
    if not question_matches or not choices_matches or not answer_matches:
        raise ValueError("Unable to extract questions, choices, or answers from the generated text.")
    
    questions_data = []
    for i in range(len(question_matches)):
        question_text = question_matches[i].strip()
        choices = list(choices_matches[i])  # Each match is a tuple, convert to list
        correct_answer = answer_matches[i].strip()
        questions_data.append((question_text, choices, correct_answer))
    
    return questions_data

def create_quiz(summary, summary_id, num_questions=10):
    # Retrieve the summary title from the Upload table
    upload = Upload.query.get(summary_id)
    if not upload:
        raise ValueError("Summary not found.")

    summary_title = upload.filename  # Assuming 'filename' is the title of the summary

    # Generate multiple questions
    questions_data = generate_questions_from_summary(summary, num_questions)

    # Create a new quiz with the summary title as the quiz title
    new_quiz = Quiz(
        title=summary_title,  # Set the quiz title to the summary title
        user_id=current_user.id  # Assuming user_id is required
    )
    db.session.add(new_quiz)
    db.session.commit()

    # Loop through the generated questions and save each to the database
    for question_text, choices, correct_answer in questions_data:
    # Convert list of choices to a single string (comma-separated values)
        choices_str = ",".join(choices)

        new_question = Question(
            question_text=question_text,
            quiz_id=new_quiz.id,
            correct_answer=correct_answer,  # Store the correct answer as "A", "B", "C", or "D"
            choices=choices_str
        )
        db.session.add(new_question)

    return new_quiz