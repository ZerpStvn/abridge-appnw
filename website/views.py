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
from . import db
from .nlp import preprocess_text, clean_sentence, build_similarity_matrix, rank_sentences, summarize, extract_text_from_pdf_nlp, advanced_summarize_pdf, remove_book_details, extract_text_from_docs_nlp
from .quiz import generate_questions_from_summary, create_quiz
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

    return render_template('nav/dashboard.html', user=current_user, uploads=user_summaries, summaries=user_summaries, quizzes=user_quizzes)

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

    if not os.path.exists(file_path):
        flash('File not found', 'error')
        return redirect(url_for('views.import_materials'))

    existing_upload = Upload.query.filter_by(user_id=current_user.id, filename=filename).first()

    if not existing_upload:
        flash('No existing upload record found for this file', 'error')
        return redirect(url_for('views.import_materials'))

    try:
        if file_ext == '.pdf':
            text = extract_text_from_pdf_nlp(file_path)
        elif file_ext in ['.docx']:
            text = extract_text_from_docs_nlp(file_path)
        elif file_ext in ['.jpg', '.jpeg', '.png']:
            text = extract_text_from_image(file_path)
        else:
            flash('Unsupported file type for text extraction', 'error')
            return redirect(url_for('views.import_materials'))
        
        summary = summarize_text_with_openai(text)

        existing_upload.text = text
        existing_upload.summary = summary
        db.session.commit()

        return render_template('nlp-quiz/result.html', summary=summary, user=current_user, filename=filename, summary_id=existing_upload.id)

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Failed to process uploaded file: {str(e)}')
        flash(f'Failed to process uploaded file: {str(e)}', 'error')
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

@views.route('/delete_summary/<int:summary_id>', methods=['POST'])
@login_required
def delete_summary(summary_id):
    summary = Upload.query.get_or_404(summary_id)  # Will raise 404 if not found
    if summary.user_id != current_user.id:  # Check ownership
        flash('You do not have permission to delete this summary.', 'error')
        return redirect(url_for('views.dashboard'))

    try:
        db.session.delete(summary)
        db.session.commit()
        flash('Summary deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        flash(f'Error deleting summary: {str(e)}', 'error')

    return redirect(url_for('views.dashboard'))

@views.route('/generate_quiz/<int:summary_id>/<string:filename>', methods=['POST'])
@login_required
def generate_quiz(summary_id, filename):
    try:
        # Retrieve the summary from the database
        upload = Upload.query.get(summary_id)
        if not upload:
            flash("Summary not found!", "danger")
            return redirect(url_for('views.home'))
        
        # Get the summary text for quiz generation
        summary_text = upload.summary  # Assuming content is stored in the Upload model
        
        # Generate quiz using the summary
        quiz = create_quiz(summary_text, summary_id)
        
        if quiz:
            flash("Quiz successfully generated!", "success")
            return redirect(url_for('views.view_quiz', quiz_id=quiz.id))
        else:
            flash("Failed to generate quiz.", "danger")
            return redirect(url_for('views.dashboard'))
    
    except Exception as e:
        logging.error(f"Error generating quiz: {e}")
        flash("An error occurred while generating the quiz.", "danger")
        return redirect(url_for('views.dashboard'))

@views.route('/view_quiz/<int:quiz_id>')
@login_required
def view_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz or quiz.user_id != current_user.id:
        flash("Quiz not found or access denied.", "danger")
        return redirect(url_for('views.dashboard'))
    
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    # Split the choices back into a list
    for question in questions:
        question.choices = question.choices.split(",")  # Split choices into a list
    
    return render_template("nlp-quiz/view_quiz.html", quiz=quiz, questions=questions, user=current_user, enumerate=enumerate)

@views.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    try:
        quiz = Quiz.query.filter_by(id=quiz_id, user_id=current_user.id).first_or_404()
        user_answers = request.form.to_dict()
        total_questions = Question.query.filter_by(quiz_id=quiz_id).count()

        correct_answers = 0
        index_to_letter = ['A', 'B', 'C', 'D']

        for question in Question.query.filter_by(quiz_id=quiz_id).all():
            user_answer = user_answers.get(f'question_{question.id}')
            
            if user_answer is not None:
                user_answer_letter = index_to_letter[int(user_answer)]
                if user_answer_letter == question.correct_answer:
                    correct_answers += 1

        score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

        # Flash the score and redirect
        flash(f'Your score: {round(score, 2)}%', 'success')
        return redirect(url_for('views.dashboard'))

    except Exception as e:
        current_app.logger.error(f'Error submitting quiz: {str(e)}', exc_info=True)
        flash('An error occurred while submitting the quiz.', 'error')
        return redirect(url_for('views.dashboard'))

@views.route('/delete_quiz/<int:quiz_id>', methods=['POST'])
@login_required
def delete_quiz(quiz_id):
    try:
        quiz = Quiz.query.filter_by(id=quiz_id, user_id=current_user.id).one()  # Fetch only for current user
        
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
