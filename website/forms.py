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
    submit = SubmitField('Create Quiz')
    # Add more fields for additional questions as needed
    submit = SubmitField('Create Quiz')

