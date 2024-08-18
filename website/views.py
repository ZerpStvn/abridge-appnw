from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms.validators import InputRequired
from wtforms import FileField, SubmitField
from sqlalchemy.orm.exc import NoResultFound
from flask_wtf.file import FileAllowed
from werkzeug.utils import secure_filename
from .ocr import extract_text_from_image, preprocess_image_for_ocr, extract_text_from_file
import os
import spacy
from . import db
from .nlp import preprocess_text, clean_sentence, build_similarity_matrix, rank_sentences, summarize, extract_text_from_pdf_nlp, advanced_summarize_pdf, remove_book_details, extract_text_from_docs_nlp
from .quiz import extract_text_from_pdf, preprocess_text,generate_questions_from_summary, get_quiz_id, truncate_text, generate_dynamic_title, get_quiz_id
from .models import User, Quiz, Question, Upload
import logging
from .summarization import extract_text, clean_text, extract_definitions, format_output, summarize_text_with_openai

views = Blueprint('views', __name__)

ALLOWED_EXTENSIONS = {'docx', 'pdf', 'png', 'jpg', 'jpeg'}

class UploadForm(FlaskForm):
    file = FileField('File', validators=[InputRequired(), FileAllowed(ALLOWED_EXTENSIONS)])
    submit = SubmitField('Upload')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@views.route('/')
def home():
    return render_template('nav/home.html', user=current_user)

@views.route('/about')
def about():
    return render_template('nav/about.html', user=current_user)

@views.route('/contact')
def contact():
    return render_template('nav/contact.html', user=current_user)

@views.route('/dashboard')
@login_required
def dashboard():
    user_summaries = Upload.query.filter_by(user_id=current_user.id).all()
    user_quizzes = Quiz.query.filter_by(user_id=current_user.id).all()
    return render_template('nav/dashboard.html', user=current_user, uploads=user_summaries, quizzes=user_quizzes, summaries=user_summaries)

@views.route('/import', methods=['GET', 'POST'])
@login_required
def import_materials():
    form = UploadForm()
    if request.method == 'POST' and form.validate_on_submit():
        file = form.file.data
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            try:
                file.save(file_path)
                new_upload = Upload(user_id=current_user.id, filename=filename)
                db.session.add(new_upload)
                db.session.commit()
                flash('File uploaded successfully', 'success')
                return redirect(url_for('views.handle_upload', filename=filename))
            except Exception as e:
                db.session.rollback()
                flash(f'Failed to save upload to database: {str(e)}', 'error')
        else:
            flash('File type not allowed', 'error')
    return render_template('nlp-quiz/import_materials.html', form=form, user=current_user)

@views.route('/upload/<filename>', methods=['GET', 'POST'])
@login_required
def handle_upload(filename):
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(filename))
    file_ext = os.path.splitext(filename)[1].lower()

    existing_upload = Upload.query.filter_by(user_id=current_user.id, filename=filename).first()
    title = generate_dynamic_title(filename)
    quiz_id = get_quiz_id(title=title)

    if not existing_upload:
        flash('No existing upload record found for this file', 'error')
        return redirect(url_for('views.import_materials'))

    if file_ext in ['.pdf', '.docx', '.jpg', '.jpeg', '.png']:
        try:
            text = extract_text_from_pdf(file_path)
            summary = summarize_text_with_openai(text)

            existing_upload.text = text
            existing_upload.summary = summary
            db.session.commit()

            if request.method == 'POST' and request.form.get('create_quiz'):
                quiz_questions = generate_questions_from_summary(summary)
                logging.info(f"Generated quiz questions: {quiz_questions}")

                for question in quiz_questions:
                    new_question = Question(quiz_id=quiz_id, **question)
                    db.session.add(new_question)
                db.session.commit()

                return redirect(url_for('views.quiz', quiz_id=quiz_id))

            return render_template('nlp-quiz/result.html', summary=summary, user=current_user, filename=filename, quiz_id=quiz_id)

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Failed to process uploaded file: {str(e)}')
            flash(f'Failed to process uploaded file: {str(e)}', 'error')
            return redirect(url_for('views.import_materials'))
    else:
        flash('Unsupported file type for text extraction', 'error')
        return redirect(url_for('views.import_materials'))

@views.route('/view_summary/<int:summary_id>', methods=['GET'])
@login_required
def view_summary(summary_id):
    form = UploadForm()
    summary = Upload.query.get_or_404(summary_id)
    return render_template('nlp-quiz/view_summary.html', summary=summary, user=current_user, form=form)

@views.route('/edit_summary/<int:summary_id>', methods=['GET', 'POST'])
@login_required
def edit_summary(summary_id):
    summary = Upload.query.get_or_404(summary_id)
    form = UploadForm()

    if request.method == 'POST':
        # Extract edited text from form
        summary.text = request.form['text']
        summary.summary = request.form['summary']
        
        try:
            db.session.commit()
            flash('Summary updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating summary: {e}')
            flash('An error occurred. Please try again.', 'error')
            return render_template('nlp-quiz/edit_summary.html', form=form, user=current_user, summary=summary)
        
        return redirect(url_for('views.dashboard'))  # Adjust the redirect as needed
    
    return render_template('nlp-quiz/edit_summary.html', form=form, user=current_user, summary=summary)

@views.route('/delete-summary/<int:summary_id>', methods=['POST'])
@login_required
def delete_summary(summary_id):
    summary = Upload.query.get_or_404(summary_id)
    if summary.user_id != current_user.id:
        flash('You do not have permission to delete this summary.', 'error')
        return redirect(url_for('views.dashboard'))

    try:
        db.session.delete(summary)
        db.session.commit()
        flash('Summary deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting summary: {str(e)}', 'error')

    return redirect(url_for('views.dashboard'))

@views.route('/quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def quiz(quiz_id):
    # Fetch the quiz from the database
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()

    if not questions:
        flash('No questions found for this quiz.', 'error')
        return redirect(url_for('views.dashboard'))

    # If there are more than 10 questions, randomly select 10 questions
    if len(questions) > 10:
        questions = random.sample(questions, 10)

    # Handle the POST request to evaluate the quiz answers
    if request.method == 'POST':
        correct_answers = 0
        total_questions = len(questions)

        for idx, question in enumerate(questions):
            user_answer = request.form.get(f'question_{idx}')
            if user_answer == question.correct_answer:
                correct_answers += 1

        # Calculate the score percentage, handle division by zero
        if total_questions == 0:
            score_percent = 0
        else:
            score_percent = (correct_answers / total_questions) * 100

        flash(f'Quiz submitted! You scored {correct_answers}/{total_questions} correct ({score_percent:.2f}%).', 'info')
        return redirect(url_for('views.dashboard'))

    # Render the quiz template with the quiz and questions
    return render_template('nlp-quiz/quiz.html', quiz=quiz, questions=questions, user=current_user, enumerate=enumerate)

@views.route('/edit_quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    form = CreateQuizForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            quiz.title = form.title.data
            for i, question in enumerate(quiz.questions):
                question_data = getattr(form, f'question_{i+1}', None)
                if question_data:
                    question.question_text = question_data.data
                    question.option_a = getattr(form, f'option_{i+1}_1').data
                    question.option_b = getattr(form, f'option_{i+1}_2').data
                    question.option_c = getattr(form, f'option_{i+1}_3').data
                    question.option_d = getattr(form, f'option_{i+1}_4').data
                    question.correct_option = getattr(form, f'correct_{i+1}').data
            db.session.commit()
            flash('Quiz updated successfully!', 'success')
            return redirect(url_for('views.dashboard'))

    elif request.method == 'GET':
        form.title.data = quiz.title
        for i, question in enumerate(quiz.questions):
            # Corrected from 'questions_{i+1}' to 'question_{i+1}'
            getattr(form, f'question_{i+1}').data = question.question_text
            getattr(form, f'option_{i+1}_1').data = question.option_a
            getattr(form, f'option_{i+1}_2').data = question.option_b
            getattr(form, f'option_{i+1}_3').data = question.option_c
            getattr(form, f'option_{i+1}_4').data = question.option_d
            getattr(form, f'correct_{i+1}').data = question.correct_option

    total_questions = len(quiz.questions)
    return render_template('nlp-quiz/edit_quiz.html', user=current_user, form=form, quiz=quiz, total_questions=total_questions)

@views.route('/delete_quiz/<int:quiz_id>', methods=['POST'])
@login_required
def delete_quiz(quiz_id):
    try:
        quiz = Quiz.query.filter_by(id=quiz_id, user_id=current_user.id).one()
        
        # Delete associated questions
        questions = Question.query.filter_by(quiz_id=quiz_id).all()
        for question in questions:
            db.session.delete(question)

        db.session.delete(quiz)
        db.session.commit()
        flash('Quiz deleted successfully.', 'success')
    except NoResultFound:
        db.session.rollback()
        flash('Quiz not found.', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting quiz: {str(e)}', 'error')

    return redirect(url_for('views.dashboard'))