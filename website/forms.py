from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, InputRequired, ValidationError
from flask_wtf.file import FileField, FileAllowed

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=100)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class UploadForm(FlaskForm):
    file = FileField('File', validators=[InputRequired(), FileAllowed(ALLOWED_EXTENSIONS)])
    submit = SubmitField('Upload')

    def validate_file(self, field):
        if not '.' in field.data.filename or \
            field.data.filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
            raise ValidationError('File type not allowed')

class CreateQuizForm(FlaskForm):
    title = StringField('Quiz Title', validators=[DataRequired()])
    question_1 = StringField('Question 1', validators=[DataRequired()])
    option_1_1 = StringField('Option A', validators=[DataRequired()])
    option_1_2 = StringField('Option B', validators=[DataRequired()])
    option_1_3 = StringField('Option C', validators=[DataRequired()])
    option_1_4 = StringField('Option D', validators=[DataRequired()])
    correct_1 = SelectField('Correct Answer', choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], validators=[DataRequired()])
    question_2 = StringField('Question 2', validators=[DataRequired()])
    option_2_1 = StringField('Option A', validators=[DataRequired()])
    option_2_2 = StringField('Option B', validators=[DataRequired()])
    option_2_3 = StringField('Option C', validators=[DataRequired()])
    option_2_4 = StringField('Option D', validators=[DataRequired()])
    correct_2 = SelectField('Correct Answer', choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], validators=[DataRequired()])
    question_3 = StringField('Question 3', validators=[DataRequired()])
    option_3_1 = StringField('Option A', validators=[DataRequired()])
    option_3_2 = StringField('Option B', validators=[DataRequired()])
    option_3_3 = StringField('Option C', validators=[DataRequired()])
    option_3_4 = StringField('Option D', validators=[DataRequired()])
    correct_3 = SelectField('Correct Answer', choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], validators=[DataRequired()])
    question_4 = StringField('Question 4', validators=[DataRequired()])
    option_4_1 = StringField('Option A', validators=[DataRequired()])
    option_4_2 = StringField('Option B', validators=[DataRequired()])
    option_4_3 = StringField('Option C', validators=[DataRequired()])
    option_4_4 = StringField('Option D', validators=[DataRequired()])
    correct_4 = SelectField('Correct Answer', choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], validators=[DataRequired()])
    question_5 = StringField('Question 5', validators=[DataRequired()])
    option_5_1 = StringField('Option A', validators=[DataRequired()])
    option_5_2 = StringField('Option B', validators=[DataRequired()])
    option_5_3 = StringField('Option C', validators=[DataRequired()])
    option_5_4 = StringField('Option D', validators=[DataRequired()])
    correct_5 = SelectField('Correct Answer', choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], validators=[DataRequired()])
    question_6 = StringField('Question 6', validators=[DataRequired()])
    option_6_1 = StringField('Option A', validators=[DataRequired()])
    option_6_2 = StringField('Option B', validators=[DataRequired()])
    option_6_3 = StringField('Option C', validators=[DataRequired()])
    option_6_4 = StringField('Option D', validators=[DataRequired()])
    correct_6 = SelectField('Correct Answer', choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], validators=[DataRequired()])
    question_7 = StringField('Question 7', validators=[DataRequired()])
    option_7_1 = StringField('Option A', validators=[DataRequired()])
    option_7_2 = StringField('Option B', validators=[DataRequired()])
    option_7_3 = StringField('Option C', validators=[DataRequired()])
    option_7_4 = StringField('Option D', validators=[DataRequired()])
    correct_7 = SelectField('Correct Answer', choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], validators=[DataRequired()])
    question_8 = StringField('Question 8', validators=[DataRequired()])
    option_8_1 = StringField('Option A', validators=[DataRequired()])
    option_8_2 = StringField('Option B', validators=[DataRequired()])
    option_8_3 = StringField('Option C', validators=[DataRequired()])
    option_8_4 = StringField('Option D', validators=[DataRequired()])
    correct_8 = SelectField('Correct Answer', choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], validators=[DataRequired()])
    question_9 = StringField('Question 9', validators=[DataRequired()])
    option_9_1 = StringField('Option A', validators=[DataRequired()])
    option_9_2 = StringField('Option B', validators=[DataRequired()])
    option_9_3 = StringField('Option C', validators=[DataRequired()])
    option_9_4 = StringField('Option D', validators=[DataRequired()])
    correct_9 = SelectField('Correct Answer', choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], validators=[DataRequired()])
    question_10 = StringField('Question 10', validators=[DataRequired()])
    option_10_1 = StringField('Option A', validators=[DataRequired()])
    option_10_2 = StringField('Option B', validators=[DataRequired()])
    option_10_3 = StringField('Option C', validators=[DataRequired()])
    option_10_4 = StringField('Option D', validators=[DataRequired()])
    correct_10 = SelectField('Correct Answer', choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], validators=[DataRequired()])
    submit = SubmitField('Create Quiz')
