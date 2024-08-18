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
